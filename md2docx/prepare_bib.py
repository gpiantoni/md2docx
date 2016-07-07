from re import split, findall, sub

FIELDS = {'address',
          'author',
          'booktitle',
          'chapter',
          'edition',
          'editor',
          'journal',
          'month',
          'number',
          'pages',
          'publisher',
          'series',
          'title',
          'volume',
          'year',
          'isbn',
          'issn',
          }


LATEX_SYMBOLS = {'$\\alpha$': 'α',
                 '$\\beta$': 'β',
                 '$\\gamma$': 'γ',
                 '$\\delta$': 'δ',
                 '$\\Sigma$': 'Σ',
                 '$\\epsilon$': 'ϵ',
                 '$\\eta$': 'η',
                 '$\\mu$': 'μ',
                 '$\\sim$': '~',
                 '$\\theta$': 'θ',
                 '$\\zeta$': 'ζ',
                 }


def fix_biblio(biblio_orig):
    """fix bibliography by keeping only useful fields.

    Parameters
    ----------
    orig_bib_file : path to .bib file
        directory with optional information

    Returns
    -------
    path to file
        bib file with a simpler structure.
    """
    biblio = biblio_orig.parent / (biblio_orig.stem + '_fixed.bib')

    if not biblio.exists() or biblio_orig.stat().st_mtime > biblio.stat().st_mtime:
        prepare_bib(biblio_orig, biblio)

    return biblio


def prepare_bib(old_bib, new_bib):
    with old_bib.open() as f:
        bib_orig = f.read()

    for latex_name, symbol in LATEX_SYMBOLS.items():
        bib_orig = bib_orig.replace(latex_name, symbol)

    keys = findall('@[a-z]+{[\w]*,', bib_orig)
    entries = split('@[a-z]+{[\w]*,', bib_orig)[1:]  # the first one is the autogenerated script by Mendeley

    assert len(keys) == len(entries)

    bib_fixed = []
    for key, entry in zip(keys, entries):
        bib_fixed.append(key + '\n' + fix_entry(entry))
    bib_fixed.append('')

    with new_bib.open('w') as f:
        f.write('\n}\n\n'.join(bib_fixed))


def fix_entry(entry):
    """ add fix_biblio from predocx.py"""
    s = []
    for field, value in findall('\n([a-z]*) = {(.*)}', entry):
        if field in FIELDS:
            value = value.replace('{\ldots}', '...')
            if field == 'author':
                value = sub(' and ([\w ]+) ([\w]+),', ' and {\g<1> \g<2>},', value)
                value = sub('{([\w ]+) ([\w]+),', '{{\g<1> \g<2>},', value)

            if field == 'booktitle':
                value = sub('(booktitle = {)(.*)(},)', '\g<1>{\g<2>}\g<3>', value)

            if field == 'pages':
                value = value.split(';')[0]  # '402--5;discussion422--7'
                value = value.split(',')[0]  # '1061-75, 1075A-1075B'
                value = value.split('author')[0]  # 17560147: '405--9 author reply 411--7'
            s.append(field + ' = {' + value + '},')

    return '\n'.join(s)


def return_csl(var_dir, journal):
    """Return the default citation style language depending on journal type.

    Parameters
    ----------
    var_dir : path to dir
        directory with optional information
    journal : str
        str with journal name

    Returns
    -------
    path to file
        path to csl file
    """
    csl_dir = var_dir / 'csl'

    if journal == 'CerebCortex':
        CSL = csl_dir / 'cerebral-cortex.csl'
    elif journal == 'eLife':
        CSL = csl_dir / 'the-journal-of-neuroscience.csl'
    elif journal == 'HumBrainMapp':
        CSL = csl_dir / 'human-brain-mapping.csl'
    elif journal == 'JNeurosci':
        CSL = csl_dir / 'the-journal-of-neuroscience.csl'
    elif journal == 'NatCommun':
        CSL = csl_dir / 'nature.csl'
    elif journal == 'NeuralPlast':
        CSL = csl_dir / 'elsevier-vancouver.csl'  # I removed access field
    elif journal == 'Neuroimage':
        CSL = csl_dir / 'elsevier-harvard.csl'
    elif journal == 'Neuron':
        CSL = csl_dir / 'cell.csl'
    elif journal == 'PLoSBiol':
        CSL = csl_dir / 'plos.csl'  # I removed access field
    elif journal == 'PNAS':
        CSL = csl_dir / 'pnas.csl'  # I removed access field
    elif journal == 'Sleep':
        CSL = csl_dir / 'sleep.csl'
    else:
        raise ValueError('The format of ' + journal + ' is not implemented')

    return CSL
