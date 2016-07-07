#!/usr/bin/env python3

from argparse import ArgumentParser
from os import getcwd
from pathlib import Path
from shutil import rmtree

from .prepare_md import preproc_md
from .prepare_docx import convert_to_docx, zip_reference_docx
from .prepare_bib import fix_biblio, return_csl


cwd = Path(getcwd())

pkg_dir = Path(__file__).resolve().parent
var_dir = pkg_dir / 'var'
orig_bib_file = var_dir / 'bib' / 'library.bib'
ref_dir = var_dir / 'docx'
journals_dir = var_dir / 'journals'
JOURNALS = [x.stem for x in journals_dir.glob('*.json')]
grants_dir = var_dir / 'grants'
GRANTS = [x.stem for x in grants_dir.glob('*.json')]


def main():
    """

    TODO
    ----
    prepare_bib
    """
    parser = ArgumentParser(prog='md2docx',
                            description='Convert Markdown to Office DOCX')
    parser.add_argument('-p', '--proj', required=True,
                        help='project code')
    parser.add_argument('-j', '--journal',
                        help='journal name (' + ', '.join(JOURNALS) + ')')
    parser.add_argument('-g', '--grant',
                        help='grant type (' + ', '.join(GRANTS) + ')')
    parser.add_argument('--library', default=str(orig_bib_file),
                        help='bib library to use (default: %(default)s)')
    parser.add_argument('--csl',
                        help='path to csl file (default depends on journal)')
    parser.add_argument('--ref_docx', default=zip_reference_docx(ref_dir),
                        help='path to docx used as reference (default: %(default)s)')
    parser.add_argument('--acronyms', default=str(var_dir / 'acronyms.txt'),
                        help='acronyms to use (default: %(default)s)')
    parser.add_argument('--only_md', action='store_true',
                        help='prepare only the intermediate md (for debugging)')
    parser.add_argument('--only_docx', action='store_true',
                        help='prepare only the docx from the already existing intermediate md (for debugging)')

    args = parser.parse_args()

    if not args.csl:
        args.csl = return_csl(var_dir, args.journal)

    MD_FILES = ('main.md', 'review.md', 'editor.md')

    if args.journal:
        print('journal')
        FOLDER_PREFIX = 'article'
    else:
        print('grant')
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

    """

    parser.add_argument('--embed', action='store_true',
                        help='will embed png in the docx')

    # copy docx to output dir
    for md_file in MD_FILES:
        filetype = splitext(md_file)[0]
        tmp_docx = join(tmp_dir, filetype + '.docx')
        if exists(tmp_docx):
            final_docx = join(out_dir, args.proj + '_' + filetype + '.docx')
            copyfile(tmp_docx, final_docx)

    # convert to tiff if necessary
    if args.journal in ('CerebCortex', 'HumBrainMapp', 'JNeurosci', 'PNAS'):
        for one_png in glob(join(out_dir, '*.png')):
            one_tiff = splitext(one_png)[0] + '.tiff'
            call('convert ' + one_png + ' ' + one_tiff, shell=True)
            remove(one_png)



    """
