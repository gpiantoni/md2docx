"""Work on markdown file and rearrange it if necessary
"""
from copy import deepcopy
from json import load, dump
from os import devnull
from re import sub, search, findall, finditer, split
from subprocess import call

from citeproc.source.bibtex import BibTeX
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation, CitationItem

from .journal import Journal

SRC_DIR = 'src'
IMG_DIR = 'img'
OUT_DIR = 'output'
CROSSREF_JSON = 'crossref.json'


def warn(citation_item):
    print("WARNING: Reference '{}' not found in the bibliography."
          .format(citation_item.key))

BIBLIO_TITLE = '## References'
DPI = 300


def preproc_md(article_dir, tmp_dir, md_file, args):
    """Fix

        - references (OK)
        - acronyms (OK)
        - authors

    TODO
    ----
    figures should follow order of text

    TODO
    ----
    tables should follow order of text
    """
    md_path = article_dir / SRC_DIR / md_file
    if not md_path.exists():
        return
    out_path = tmp_dir / md_file

    is_main = md_file == 'main.md'
    is_review = md_file == 'review.md'

    with md_path.open() as f:
        md = f.read()

    j = Journal(args.journal)

    # reorder, because this affects references, acronyms and figure/table order
    md = organize_md(md, j, is_main)

    md = _make_acronyms(md, args.acronyms)

    print('')
    md = include_figures(article_dir, md, is_main)

    md = add_references(md, args)

    if is_main:
        print('')
        count_text(md, j)

    with out_path.open('w') as f:
        f.write(md)

    if is_main:
        _get_main_ref(tmp_dir)

    if is_review:
        _set_review_ref(tmp_dir)


def count_text(md, j):

    md_title, md_sections = _read_section_by_section(md)

    for limit in j.json['wordcount']:
        count = 0
        section_names = []
        for section in limit['sections']:
            section_names.append(section)

            try:
                section_text = md_sections[section]
            except KeyError:
                print(section + ' is missing')
                break

            if limit['limit']['type']:
                count += len(findall('\s', section_text))
            else:
                raise NotImplementedError

        if count == 0:
            continue
        if count > limit['limit']['number']:
            print('{0} has {1} words (max: {2}) -> WARNING'
                  ''.format('+'.join(section_names), count, limit['limit']['number']))
        else:
            print('{0} has {1} words (max: {2})'
                  ''.format('+'.join(section_names), count, limit['limit']['number']))


def _read_section_by_section(md):
    """we need to do it twice, 1) when we reorder the text and 2) when we count
    the words"""
    md_section_names = findall('\n## ([\w ]+)\n', md)

    md_parts = split('\n## [\w ]+\n', md)
    md_title = md_parts[0]
    md_sections = dict(zip(md_section_names, md_parts[1:]))
    return md_title, md_sections


def organize_md(md, j, is_main):
    md_title, md_sections = _read_section_by_section(md)

    md = [md_title, ]
    for sect in j.sections:
        try:
            md.append('\n## ' + sect + '\n' + md_sections.pop(sect))
        except KeyError:
            if j.is_necessary(sect) and is_main:
                print('missing section ' + sect)

    if md_sections and is_main:
        print('unused sections: ' + ', '.join(list(md_sections)))

    return ''.join(md)


def include_figures(article_dir, s, is_main):
    """
    TODO
    ----
    this should depend on order in text, but then rearrange them at the end.

        if args.journal == 'PNAS':
            s = sub('### (?!Figure \[\+)(.*)', '**\g<1>**', s)

    """
    img_dir = article_dir / IMG_DIR
    out_dir = article_dir / OUT_DIR

    # if args.embed or not is_main:  # TODO
    s = sub('### Figure (\[\+[\w]*\])',
            '\g<0>\n![](' + str(out_dir / 'figure_\g<1>.png') + ')\n',
            s)

    # ADD INDICES FOR FIGURES AND TABLES
    s, figure_name = _make_index(s, is_main)
    _svg2png(figure_name, img_dir, out_dir)
    return s


def _make_index(s, is_main):
    """Make indices for figures.

    Parameters
    ----------
    s : str
        the whole article
    is_main : bool
        if it's false, i.e. a review, add "R" before table and figure names

    Returns
    -------
    str
        the whole article, with the correct indeces for figures, tables
    figure_name : tuple of list
        2 lists with the names of the svg files and the png files

    Notes
    -----
    Format is rather rigid: each figure should be named
    ### Figure [+figure_name]
    and every time you refer to it, you should use [+figure_name]

    It uses roman numerals for tables
    """
    all_fig = finditer('### Fig(ure|\.) (\[\+(\w+)\])', s)
    figure_svg = []
    figure_png = []
    for i, fig in enumerate(all_fig):

        fig_ref = fig.group(2)
        fig_code = fig.group(3)

        if is_main:
            fig_idx = str(i + 1)
        else:
            fig_idx = 'R' + str(i + 1)

        s = s.replace(fig_ref, fig_idx)
        figure_svg.append(fig_code + '.svg')
        figure_png.append('figure_' + fig_idx + '.png')

    figure_name = (figure_svg, figure_png)

    all_table = finditer('### Table (\[\+\w+\])', s)
    for i, table in enumerate(all_table):
        table_ref = table.group(1)

        if is_main:
            table_idx = _int_to_roman(i + 1)
        else:
            table_idx = 'R' + _int_to_roman(i + 1)

        s = s.replace(table_ref, table_idx)

    return s, figure_name


def _svg2png(figure_name, img_dir, out_dir):
    """Convert svg to png if necessary.

    Parameters
    ----------
    figure_name : tuple of list
        2 lists with the names of the svg files and the png files
    img_dir : path to dir
        directory with the svg images
    out_dir : path to dir
        directory that contains the output

    Raises
    ------
    FileNotFoundError
        when the svg cannot be found

    Notes
    -----
    CerebCortex: max with = 86mm, 180mm
    JNeurosci: max width = 85mm, 116mm, 176mm
    """
    inkscape_cmd = '('

    for i_svg, i_png in zip(*figure_name):
        svg_file = img_dir / i_svg
        if not svg_file.exists():
            raise FileNotFoundError(str(svg_file))

        png_file = out_dir / i_png

        print('Converting ' + i_svg)
        inkscape_cmd += 'echo ' + str(svg_file)
        inkscape_cmd += ' --export-dpi=' + str(DPI)
        inkscape_cmd += ' --export-background=#ffffff'  # use white background
        inkscape_cmd += ' --export-png=' + str(png_file) + '\n'

    inkscape_cmd += ') |  inkscape --shell'
    if len(inkscape_cmd) > 22:  # if it has anything to do at all
        call(inkscape_cmd, stdout=open(devnull, "w"),
             stderr=open(devnull, "w"), shell=True)


def _int_to_roman(i):
    """From http://code.activestate.com/recipes/81611-roman-numerals/
    """
    numeral_map = tuple(zip((1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4,
                             1), ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL',
                                  'X', 'IX', 'V', 'IV', 'I')))

    result = []
    for integer, numeral in numeral_map:
        count = i // integer
        result.append(numeral * count)
        i -= integer * count
    return ''.join(result)


def add_references(md, args):
    bib_source = BibTeX(str(args.library), 'utf-8')
    bib_style = CitationStylesStyle(str(args.csl), validate=False)
    bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.plain)

    md_citations = findall('\[([\w \.]*)(@[@\w+0-9; ]+)\]', md)  # linked to to_replace

    citations = []

    for full_citation in md_citations:
        prefix, md_citation = full_citation
        md_citationitems = findall('@(\w+[0-9]+\w+)', md_citation)

        citation_items = []
        for md_citationitem in md_citationitems:
            citation_items.append(CitationItem(md_citationitem))
        citation = Citation(citation_items)
        citations.append(citation)
        bibliography.register(citation)

    for full_citation, citation in zip(md_citations, citations):
        prefix, md_citation = full_citation

        to_replace = '[' + prefix + md_citation + ']'
        formatted_citation = str(bibliography.cite(citation, warn))
        formatted_citation = formatted_citation[0] + prefix + formatted_citation[1:]

        md = md.replace(to_replace, formatted_citation, 1)

    references = [BIBLIO_TITLE, ]
    bibliography.sort()
    for item in bibliography.bibliography():
        references.append(str(item))

    md_biblio = '\n\n'.join(references)

    return md.replace(BIBLIO_TITLE, md_biblio)


def _make_acronyms(l, acronym_file):
    """change all the acronyms.

    Parameters
    ----------
    l : str
        string to change
    acronym_file : path to file
        json file with acronyms

    Returns
    -------
    str
        string with acronyms
    """
    with open(acronym_file, 'r') as r:
        acronym = load(r)

    full_acronym = deepcopy(acronym)

    while True:
        m = search('\[\$[a-zA-Z]+\]', l)
        if m is None:
            break
        key = m.group()[2:-1]
        l0 = l[:m.start()]
        l1 = l[m.end():]
        if acronym[key] is not None:  # first time
            l = l0 + acronym[key] + ' (' + key + ')' + l1
            acronym[key] = None
        else:
            l = l0 + key + l1

    # ADD ACRONYMS at the end
    s = []
    for key in sorted(acronym, key=lambda x: x.lower()):
        if acronym[key] is None:
            s.append(key + ': ' + full_acronym[key])
    l = l.replace('[ACRONYMS]', '; '.join(s))

    return l


def _get_main_ref(tmp_dir):
    """Get references from the main text

    Parameters
    ----------
    tmp_dir : path to dir
        directory with temporary files

    Notes
    -----
    It seems complicated but the code is pretty straightforward. It finds
    which keys should be looked up in reply-to-reviewers, then it reads the
    text from the main manuscript.

    The only tricky part is join(main_s.splot(key)[1::2]). It splits the
    main text based on the key and it takes every other string (those
    between keys). Then it joins them using [...] if necessary.
    """
    md_path = tmp_dir / 'main.md'
    crossref_json = tmp_dir / CROSSREF_JSON

    with md_path.open('r') as r:
        main_s = r.read()  # read the whole file

    # we create a dict of the key and complete values.
    review_sub = {}
    for key in set(findall('@\[[0-9a-z.]+\]', main_s)):
        l = ' [...]\n'.join(main_s.split(key)[1::2])
        # remove italics already in the string (but not boldface)
        l = sub('\*(.+?)\*', '\g<1>', l.replace('**', 'XX')).replace('XX',
                                                                     '**')
        # corner case, when one key is in the text of another key
        review_sub[key] = sub('@\[[0-9a-z.]+\]', '', l)

    # use italics for cross-references (review.md should use *@[X]* then)
    for key, value in review_sub.items():
        review_sub[key] = value.replace('\n', '*\n*')

    with crossref_json.open('w') as f:
        dump(review_sub, f)

    # remove markers used for review (and bold which is used only to highlight)
    main_s = sub('@\[[0-9a-z.]+\]', '', main_s)
    main_s = main_s.replace('**', '')

    with md_path.open('w') as w:
        w.write(main_s)  # write the whole file


def _set_review_ref(tmp_dir):
    """Set references to the review text

    Parameters
    ----------
    tmp_dir : path to dir
        directory with temporary files
    """
    review_path = tmp_dir / 'review.md'
    crossref_json = tmp_dir / CROSSREF_JSON

    with review_path.open('r') as r:
        review_s = r.read()  # read the whole file

    with crossref_json.open('r') as f:
        review_sub = load(f)

    # we create a dict of the key and complete values.
    for key, value in review_sub.items():
        review_s = review_s.replace(key, value)

    with review_path.open('w') as w:
        w.write(review_s)  # write the whole file
