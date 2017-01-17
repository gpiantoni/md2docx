from subprocess import run, DEVNULL


def convert_to_pdf(out_dir, md_file):
    docx_path = (out_dir / md_file).with_suffix('.docx')
    if docx_path.exists():
        run(['libreoffice', '--headless', '--convert-to', 'pdf',
             docx_path.name], cwd=out_dir, stdout=DEVNULL)
