from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# make sure that VERSION can be converted to float
with open(path.join(here, 'md2docx', 'VERSION')) as f:
    VERSION = f.read().strip('\n')  # editors love to add newline

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='md2docx',
    version=VERSION,
    description='Use MarkDown to write articles and grants',
    long_description=long_description,
    url='http://www.gpiantoni.com/md2docx',
    author='Gio Piantoni',
    author_email='md2docx@gpiantoni.com',
    license='GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='neuroscience analysis sleep EEG ECoG',
    packages=find_packages(),
    install_requires=['citeproc-py'],
    package_data={
        'md2docx': ['VERSION',
                    'var/docx',
                    'var/docx/docProps/*',
                    'var/docx/_rels/*',
                    'var/docx/word/*',
                    'var/docx/word/_rels/*',
                    'var/docx/word/theme/*',
                    ],
    },
    entry_points={
        'console_scripts': [
            'md2docx=md2docx.main:main',
        ],
    },
)
