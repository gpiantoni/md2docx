from pathlib import Path
from json import load


JOURNALS_PATH = Path('/home/gio/Documents/articles/var/journals')


class Journal:
    #TODO: use csl from json file
    def __init__(self, journal):
        json_file = JOURNALS_PATH / (journal + '.json')
        self.json_file = json_file

        with json_file.open() as f:
            self.json = load(f)

    @property
    def sections(self):
        return [x['name'] for x in self.json['sections']]

    def is_necessary(self, section_name):
        """check if session is necessary
        """
        for x in self.json['sections']:
            if x['name'] == section_name:
                return x['mandatory']

        raise KeyError('Could not find ' + section_name)

    def has_newpage(self, section_name):
        """check if session needs a new page
        """
        for x in self.json['sections']:
            if x['name'] == section_name:
                return x['newpage']

        raise KeyError('Could not find ' + section_name)
