"""TODO"""


class SuperDatabase3000():
    """
blabla
    """

    def __init__(self):
        """
blabla

Parameters
----------
arg : type
    blabla
arg : type
    blabla

Examples
--------
blabla
        """
        self.items = {}

    def __getitem__(self, key):
        """TODO"""
        return self.items[key]

    def __setitem__(self, key, value):
        """TODO"""
        self.items[key] = value

    def __delitem__(self, key):
        """TODO"""
        del self.items[key]

    def __iter__(self):
        """TODO"""
        return iter(self.items)

    def __len__(self):
        """TODO"""
        return len(self.items)

    def __repr__(self):
        """TODO"""
        return f"<SuperDatabase3000: {self.keys()}>"

    def keys(self):
        """TODO"""
        return self.items.keys()

    def values(self):
        """TODO"""
        return self.items.values()

    def get(self, key, default=None):
        """TODO"""
        try:
            return self.__getitem__(key)
        except ValueError:
            return default

    def append(self, key, item):
        """TODO"""
        self.items[key] += item
