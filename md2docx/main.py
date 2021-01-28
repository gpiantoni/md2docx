#!/usr/bin/env python3

from argparse import ArgumentParser
from os import getcwd
from pathlib import Path
from shutil import rmtree
from subprocess import run
try:
    from PIL import Image
except ImportError:
    Image = None

from .prepare_md import preproc_md
from .prepare_docx import convert_to_docx
from .prepare_bib import fix_biblio
from .prepare_pdf import convert_to_pdf
from .journal import Journal
from .utils import (bib_dir,
                    journals_dir,
                    ref_dir,
                    var_dir,
                    csl_dir
                    )


orig_bib_file = bib_dir / 'library.bib'
REF_DOCX = ref_dir / 'reference.docx'
JOURNALS = [x.stem for x in journals_dir.glob('*.json')]


def main():
    """

    TODO
    ----
    make journal_json mutually exclusive with journal in arguments
    """
    parser = ArgumentParser(prog='md2docx',
                            description='Convert Markdown to Office DOCX')
    parser.add_argument('-j', '--journal', required=True,
                        help='journal name (' + ', '.join(JOURNALS) + ')')
    parser.add_argument('--journal_json',
                        help='specify full path to custom journal .json file')
    parser.add_argument('--library', default=str(orig_bib_file),
                        help='bib library to use (default: %(default)s)')
    parser.add_argument('--csl',
                        help='path to csl file (default depends on journal)')
    parser.add_argument('--ref_docx', default=REF_DOCX,
                        help='path to docx used as reference (default: %(default)s)')
    parser.add_argument('--node_path',
                        help='path to directory containing node (if not on PATH already)')
    parser.add_argument('--inkscape_path',
                        help='path to directory containing inkscape (if not on PATH already)')
    parser.add_argument('--acronyms', default=str(var_dir / 'acronyms.txt'),
                        help='acronyms to use (default: %(default)s)')
    parser.add_argument('--embed', action='store_true',
                        help='will embed png in the docx')
    parser.add_argument('--keep_png', action='store_true',
                        help='do not convert png to tiff, even if it is required by the journal')
    parser.add_argument('--pdf', action='store_true',
                        help='convert to PDF as well (you need libreoffice installed)')
    parser.add_argument('--skip_inkscape', action='store_true',
                        help='do not convert svg with inkscape')
    parser.add_argument('--only_md', action='store_true',
                        help='prepare only the intermediate md (for debugging)')
    parser.add_argument('--only_docx', action='store_true',
                        help='prepare only the docx from the already existing intermediate md (for debugging)')

    args = parser.parse_args()

    MD_FILES = ('main.md', 'review.md', 'editor.md')

    if not args.journal_json:
        args.journal_json = journals_dir / (args.journal + '.json')
    j = Journal(args.journal_json)

    if not args.csl:
        args.csl = csl_dir / j.csl

    article_dir = Path(getcwd())
    out_dir = article_dir / 'output'
    out_dir.mkdir(exist_ok=True)

    args.library = fix_biblio(Path(args.library).resolve())

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
            if args.pdf:
                convert_to_pdf(out_dir, md_file)

    # convert to tiff if necessary
    if j.figure_format() == 'tiff' and not args.keep_png:
        if Image is None:
            raise ImportError('cannot convert png to tiff, install Pillow')

        for one_png in out_dir.glob('*.png'):
            one_tiff = one_png.with_suffix('.tiff')
            img = Image.open(str(one_png))
            img.save(str(one_tiff))  # uncompressed TIFF
            one_png.unlink()


def prepare_bib():
    parser = ArgumentParser(prog='prepare_bib',
                            description='Convert bibtex/mendeley to json library for citeproc.js')
    parser.add_argument('--library', default=str(orig_bib_file),
                        help='bib library to use (default: %(default)s)')
    args = parser.parse_args()

    fix_biblio(Path(args.library))
