import sys
import time
import os
import numpy as np
import pandas as pd
import pytest
from tables.exceptions import HDF5ExtError

import superdatabase3000.hdf as hdf


@pytest.mark.filterwarnings("ignore:numpy.ufunc size changed")
def test_hdf():

    test_hdf_file = "/tmp/db.h5"
    test_table = "/toto"
    if os.path.exists(test_hdf_file):
        os.unlink(test_hdf_file)
    hsm = None
    for _ in range(32):
        try:
            hsm = hdf.HdfStoreManager(test_hdf_file)
            break
        except HDF5ExtError:
            time.sleep(0.1)
    if hsm is None:
        assert hsm
        sys.exit(42)

    df1 = pd.DataFrame(np.random.random((10000, 12)))
    hsm.insert(test_table, df1)
    hsm.flush()
    df2 = hsm.select(test_table)

    assert not len((df1 == df2).replace(True, np.nan).dropna())
    assert len(hsm.select(test_table, start=-1)) == 1
    assert len(hsm.select(test_table, stop=-1)) == 10000 - 1
    hsm.delete(test_table, where="index >= 3")
    assert len(hsm.select(test_table)) == 3

    df3 = pd.DataFrame(
        np.random.random((10000, 12)),
        index=np.random.shuffle(list(df2.index))
    )
    hsm.insert(test_table, df3)

    hsm.maintain()
    hsm.drop(test_table)
    del hsm

    # yay = False
    # for _ in range(32):
    #     try:
    #         os.unlink(test_hdf_file)
    #         yay = True
    #         break
    #     except FileNotFoundError:
    #         time.sleep(0.1)
    # if not yay:
    #     assert yay
    #     sys.exit(42)
