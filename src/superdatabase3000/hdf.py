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
        for table in self.store.keys():
            self.store.create_table_index(table, optlevel=9, kind='full')

    def flush(self):
        self.store.flush(True)

    def select(self, table, where=None, columns=None, start=None, stop=None):
        """TODO"""
        if where is None and columns is None and start is None and stop is None:
            return self.store.get(table)
        if start is not None or stop is not None:
            nrows = self.store.get_storer(table).nrows
            if start is not None and start < 0:
                start = nrows - start
            if stop is not None and stop < 0:
                stop = nrows - stop
        return self.store.select(
            table, where=where, columns=columns, start=start, stop=stop
        )
        # TODO:
        # except KeyError:
        #     print(f"Hdf: select: can't find table {table}")
        #     return False

    def insert(self, table, df):
        """TODO"""
        if not df.index.is_monotonic_increasing:
            print(
                "Hdf: insert: warning, tried to add a DataFrame with "
                f"unsorted indexes to {table}; I'll sort it for you..."
            )
            df.sort_index(inplace=True)
        # TODO: add update=False
        # if update:  # or 'insert in the middle'
        #     # this is not currently supported, so here's the deal:
        #     after_df = self.select(
        #         table,
        #         where="index >= df.index[0]"
        #     )  # this might use a shitload of ram
        #     if not after_df.empty:
        #         self.delete(
        #             table,
        #             where="index >= df.index[0]"
        #         )
        #         df = df.merge(after_df)  # ???
        try:
            self.store.append(table, df, data_columns=True)
        except RuntimeError:  # HDF5ExtError
            print(f"Hdf: insert: something went wrong with {table}")
            return False
        return True

    def delete(self, table, where):
        """TODO"""
        try:
            self.store.delete(table, where)
        except KeyError:
            print(f"Hdf: delete: can't find table {table}")
            return False
        return True

    def drop(self, table):
        """TODO"""
        try:
            del self.store[table]
        except KeyError:
            print(f"Hdf: drop: can't find table {table}")
            return False
        return True
