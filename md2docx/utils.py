from os import getcwd
from pathlib import Path

cur_dir = Path(getcwd())

pkg_dir = Path(__file__).resolve().parent
var_dir = pkg_dir / 'var'
bib_dir = var_dir / 'bib'
csl_dir = var_dir / 'csl'
ref_dir = var_dir / 'docx'
loc_dir = var_dir / 'locale'
node_dir = var_dir / 'nodejs'
journals_dir = var_dir / 'journals'
