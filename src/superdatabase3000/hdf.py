"""This module is an interface to the pandas hdf store."""

import os
import pandas as pd

DEFAULT_HDF_FILENAME = f"{os.environ['HOME']}/.superdatabase3000.hdf"


class HdfStoreManager():
    """
    This class allows to manage an hdf store (no shit).
    It gives convenient sql like methods (select/insert/delete/drop).

    Not thread-safe. Not even a little. Don't try. Ok? No. Don't.
    """

    def __init__(self, hdf_filename=None):
        """Open the hdf store from the given 'hdf_filename'."""
        # TODO: flock filename
        if hdf_filename is None:
            hdf_filename = DEFAULT_HDF_FILENAME
        self.store = pd.HDFStore(hdf_filename)

    def __del__(self):
        """Close the hdf store."""
        self.store.close()

    def maintain(self):
        """Create table index for each table in the store."""
        for table in self.store.keys():
            self.store.create_table_index(table, optlevel=9, kind='full')

    def flush(self):
        """Flush the store to disk (calls fsync)."""
        self.store.flush(True)

    def select(self, table, where=None, columns=None, start=None, stop=None):
        """
        Select rows (as a DataFrame) from the given 'table'.

        start (int): row number to start selection (negative index allowed)
        stop  (int): row number to stop selection (negative index allowed)
        columns : a list of columns that will limit the return columns

        Return None if something funky happens.
        For the 'where' syntax, see:
        https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#querying-a-table
        """
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
            if start >= nrows or stop >= nrows:
                print(f"Hdf: select: out of bound start/stop argument")
                return None
        return self.store.select(
            table, where=where, columns=columns, start=start, stop=stop
        )

    def insert(self, table, df):
        """
        Insert the DataFrame 'df' to the given 'table'. Might update values.

        The table must always be sorted, so you should prefer inserting
        to the end (with growing indexes) if you need better performances.

        Return False if the table doesn't exist or something funky happens.
        """
        # update/'insert in the middle' are not currently supported,
        # so here's the deal:
        after_df = self.select(
            table,
            where=f"index >= {df.index[0]}"
        )  # this might use a shitload of ram
        if after_df is not None:
            if list(df.columns) != list(after_df.columns):
                print(
                    "Hdf: insert: tried to insert a DataFrame "
                    f"with differents columns than the DataFrame in {table}"
                )
                return False
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
            # this should happend only if the given 'df' is unsorted
            df.sort_index(inplace=True)

        try:
            self.store.append(table, df)  # , data_columns=True)
        except (RuntimeError, ValueError):  # HDF5ExtError
            print(f"Hdf: insert: something went wrong with {table}")
            return False
        return True

    def delete(self, table, where):
        """
        Drop the rows matching the 'where' close on the given 'table'.

        Return False if the table doesn't exist.
        For the 'where' syntax, see:
        https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#querying-a-table
        """
        try:
            self.store.remove(table, where)
        except KeyError:
            print(f"Hdf: delete: can't find table {table}")
            return False
        return True

    def drop(self, table):
        """
        Drop the given 'table'.

        Return False if the table doesn't exist.
        """
        try:
            del self.store[table]
        except KeyError:
            print(f"Hdf: drop: can't find table {table}")
            return False
        return True

    # TODO: add count / columns / keys
