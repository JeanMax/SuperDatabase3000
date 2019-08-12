"""TODO"""

import pandas as pd


class HdfStoreManager():
    """
    TODO

    Not thread-safe. Not even a little. Don't try. Ok? No. Don't.
    """

    def __init__(self, filename):
        """TODO"""
        self.store = pd.HDFStore(filename)  # , complevel=9, complib='blosc')

    def __del__(self):
        """Close the hdf store."""
        self.store.close()

    def maintain(self):
        """TODO"""
        for k in self.store.keys():
            df = self.store.get(k)
            if not df.index.is_monotonic_increasing:
                print(k, "is NOT sorted!!!! Hdf store fucked up :/")
                df.sort_index(inplace=True)
                self.store.append(k, df, append=False)  # I *love* this arg
            self.store.create_table_index(k, optlevel=9, kind='full')

    def save(self, key, df):
        """TODO"""
        return self.store.append(key, df)

    def load(self, key, where=None):
        """TODO"""
        if where is not None:
            return self.store.select(key, where)
        return self.store.get(key)

    def remove(self, key):
        """TODO"""
        del self.store[key]
