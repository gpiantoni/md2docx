#!/usr/bin/env python3

from argparse import ArgumentParser
from os import getcwd
from pathlib import Path
from shutil import rmtree
from subprocess import run

from .prepare_md import preproc_md
from .prepare_docx import convert_to_docx
from .prepare_bib import fix_biblio, return_csl
from .journal import Journal


cwd = Path(getcwd())

pkg_dir = Path(__file__).resolve().parent
var_dir = pkg_dir / 'var'
orig_bib_file = var_dir / 'bib' / 'library.bib'
ref_dir = var_dir / 'docx'
REF_DOCX = ref_dir / 'reference.docx'
journals_dir = var_dir / 'journals'
JOURNALS = [x.stem for x in journals_dir.glob('*.json')]


def main():
    """

    TODO
    ----
    make journal_json mutually exclusive with journal in arguments
    """
    parser = ArgumentParser(prog='md2docx',
                            description='Convert Markdown to Office DOCX')
    parser.add_argument('-p', '--proj', required=True,
                        help='project code')
    parser.add_argument('-j', '--journal',
                        help='journal name (' + ', '.join(JOURNALS) + ')')
    parser.add_argument('--journal_json',
                        help='specify full path to custom journal .json file')
    parser.add_argument('--library', default=str(orig_bib_file),
                        help='bib library to use (default: %(default)s)')
    parser.add_argument('--csl',
                        help='path to csl file (default depends on journal)')
    parser.add_argument('--ref_docx', default=REF_DOCX,
                        help='path to docx used as reference (default: %(default)s)')
    parser.add_argument('--acronyms', default=str(var_dir / 'acronyms.txt'),
                        help='acronyms to use (default: %(default)s)')
    parser.add_argument('--embed', action='store_true',
                        help='will embed png in the docx')
    parser.add_argument('--only_md', action='store_true',
                        help='prepare only the intermediate md (for debugging)')
    parser.add_argument('--only_docx', action='store_true',
                        help='prepare only the docx from the already existing intermediate md (for debugging)')

    args = parser.parse_args()

    if not args.csl:
        args.csl = return_csl(var_dir, args.journal)

    MD_FILES = ('main.md', 'review.md', 'editor.md')

    if args.journal:
        FOLDER_PREFIX = 'article'
        if not args.journal_json:
            args.journal_json = journals_dir / (args.journal + '.json')
    else:
        FOLDER_PREFIX = 'grant'

    args.article = FOLDER_PREFIX + '_' + args.proj
    article_dir = cwd / args.article
    out_dir = article_dir / 'output'
    out_dir.mkdir(exist_ok=True)

    args.library = fix_biblio(Path(args.library))
    # copy files

    tmp_dir = article_dir / 'tmp'

    if not args.only_docx:
        # remove tmp directory if we run prepare_md again
        try:
            rmtree(str(tmp_dir))
        except OSError:
            pass
        tmp_dir.mkdir()

        for md_file in MD_FILES:
            preproc_md(article_dir, tmp_dir, md_file, args)

    if not args.only_md:
        for md_file in MD_FILES:
            convert_to_docx(out_dir, tmp_dir, md_file, args)

    # convert to tiff if necessary
    j = Journal(args.journal_json)
    if j.figure_format() == 'tiff':
        for one_png in out_dir.glob('*.png'):
            one_tiff = one_png.with_suffix('.tiff')
            run(['convert', str(one_png), str(one_tiff)])
            one_png.unlink()
