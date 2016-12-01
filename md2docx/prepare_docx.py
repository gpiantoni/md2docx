from docx import Document
from re import split, findall, sub

from .journal import Journal



def convert_to_docx(output_dir, tmp_dir, md_file, args):

    md_path = tmp_dir / md_file
    if not md_path.exists():
        return

    j = Journal(args.journal_json)

    document = Document(str(args.ref_docx))

    docx_path = output_dir / md_path.with_suffix('.docx').name

    with md_path.open() as f:

        p = None

        for md in f.read().split('\n'):

            if md.startswith('# '):
                document.add_heading(md[2:], 0)

            elif md.startswith('## '):
                section_name = md[3:]
                if j.has_newpage(section_name):
                    document.add_page_break()
                document.add_heading(md[3:], 1)

            elif md.startswith('### '):
                cond0 = j.embed_figures() or args.embed
                cond1 = md.startswith('### Figure ') and not md == '### Figure 1'
                if cond0 and cond1:
                    document.add_page_break()
                document.add_heading(md[4:], 2)

            elif md.startswith('![]('):
                path_to_img = md[4:-1]  # TODO: cleaner way to select path
                document.add_picture(path_to_img)

            elif len(md) > 0 and md[0] == '^' and md[-1] == '^':  # table header (TODO: how to modify format)
                n_col = md.count('^') - 1
                table = document.add_table(rows=1, cols=n_col)
                row_cells = table.rows[0].cells
                for one_cell, txt in zip(row_cells, md.split('^')[1:-1]):
                    one_cell.text = txt.strip()

            elif len(md) > 0 and md[0] == '|' and md[-1] == '|':
                row_cells = table.add_row().cells

                for one_cell, txt in zip(row_cells, md.split('|')[1:-1]):
                    one_cell.text = txt.strip()

            elif md.strip() == '':  # empty line, i.e. end of the paragraph
                p = None

            else:
                if p is None:
                    if md.startswith('>'):
                        style = 'Reviewer'
                        md = md[2:]  # remove "> " at the beginning
                    else:
                        style = None
                    p = document.add_paragraph(style=style)
                else:
                    p.add_run(' ')

                _add_run(p, md)

    document.save(str(docx_path))


def _add_run(p, md):

    runs = split('(?<!\\\)[%|\*|_|\^|~]', md)
    values = findall('(?<!\\\)[%|\*|_|\^|~]', md)
    values.append('')

    italics = False
    bold = False
    underline = False
    superscript = False
    subscript = False

    for one_run, one_value in zip(runs, values):

        # remove slash for \*, \~, \^
        one_run = sub('\\\([%~\*\^])', '\g<1>', one_run)

        r = p.add_run(one_run)

        if italics:
            r.italic = True
        if bold:
            r.bold = True
        if underline:
            r.underline = True
        if superscript:
            r.font.superscript = True
        if subscript:
            r.font.subscript = True

        if one_value == '%':
            bold = ~bold
        if one_value == '*':
            italics = ~italics
        if one_value == '^':
            superscript = ~superscript
        if one_value == '~':
            subscript = ~subscript
