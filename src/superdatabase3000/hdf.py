"""TODO"""

import os
import pandas as pd

DEFAULT_HDF_FILENAME = f"{os.environ['HOME']}/.superdatabase3000.hdf"


class HdfStoreManager():
    """
    TODO

    Not thread-safe. Not even a little. Don't try. Ok? No. Don't.
    """

    def __init__(self, hdf_filename=None):
        """TODO"""
        # TODO: flock filename
        if hdf_filename is None:
            hdf_filename = DEFAULT_HDF_FILENAME
        self.store = pd.HDFStore(hdf_filename)

    def __del__(self):
        """Close the hdf store."""
        self.store.close()

    def maintain(self):
        """TODO"""
        for table in self.store.keys():
            self.store.create_table_index(table, optlevel=9, kind='full')

    def flush(self):
        """TODO"""
        self.store.flush(True)

    def select(self, table, where=None, columns=None, start=None, stop=None):
        """TODO"""
        if table not in self.store.keys():
            print(f"Hdf: select: can't find table {table}")
            return None
        if where is None and columns is None and start is None and stop is None:
            return self.store.get(table)
        if start is not None or stop is not None:
            nrows = self.store.get_storer(table).nrows
            if start is not None and start < 0:
                start = nrows + start
            if stop is not None and stop < 0:
                stop = nrows + stop
        return self.store.select(
            table, where=where, columns=columns, start=start, stop=stop
        )

    def insert(self, table, df):
        """TODO"""
        # update/'insert in the middle' are not currently supported,
        # so here's the deal:
        after_df = self.select(
            table,
            where=f"index >= {df.index[0]}"
        )  # this might use a shitload of ram
        if after_df is not None:
            self.delete(
                table,
                where=f"index >= {df.index[0]}"
            )
            df = df.append(after_df)
            df = df.loc[~df.index.duplicated(keep='last')]

        if not df.index.is_monotonic_increasing:
            print(
                "Hdf: insert: warning, tried to add a DataFrame with "
                f"unsorted indexes to {table}; I'll sort it for you..."
            )
            df.sort_index(inplace=True)

        try:
            self.store.append(table, df)  # , data_columns=True)
        except (RuntimeError, ValueError):  # HDF5ExtError
            print(f"Hdf: insert: something went wrong with {table}")
            return False
        return True

    def delete(self, table, where):
        """TODO"""
        try:
            self.store.remove(table, where)
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
