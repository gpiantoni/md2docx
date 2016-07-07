from json import load


class Journal:
    """Class containing the information regarding one journal, based on json
    file.

    Parameters
    ----------
    journal_json : instance of Path
        path to journal .json file

    TODO
    -----
    use csl from json file
    """
    def __init__(self, journal_json):
        self.journal_json = journal_json

        with journal_json.open() as f:
            self.json = load(f)

    @property
    def sections(self):
        return [x['name'] for x in self.json['sections']]

    def is_necessary(self, section_name):
        """check if session is necessary

        Parameters
        ----------
        section_name : str
            name of the section
        """
        for x in self.json['sections']:
            if x['name'] == section_name:
                return x['mandatory']

        raise KeyError('Could not find ' + section_name)

    def has_newpage(self, section_name):
        """check if session needs a new page

        Parameters
        ----------
        section_name : str
            name of the section
        """
        for x in self.json['sections']:
            if x['name'] == section_name:
                return x['newpage']

        raise KeyError('Could not find ' + section_name)
