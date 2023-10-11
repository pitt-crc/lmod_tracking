"""Utilities for generating and interacting with mock log data."""

from pathlib import Path

import pandas as pd

TEST_PATH = Path(__file__).resolve().parent / 'mock_data.log'


def get_mock_data() -> pd.DataFrame:
    """Return a pandas DataFrame containing mock log data

    Returns:
        A pandas DataFrame
    """

    return pd.DataFrame(dict(
        date=['Apr 1 03:20:34', 'May 12 03:20:34'],
        jobid=[1, None],
        node=['gpu-n53', 'smp-n10'],
        user=['user1', 'user2'],
        module=['gcc/8.2.0', 'openmpi'],
        path=['/software/gcc/8.2.0.lua', '/software/gcc/openmpi/4.0.3.lua'],
        host=['gpu-n53.crc.pitt.edu', 'smp-n10.crc.pitt.edu'],
        time=[1682407234.086799, 1682407234.103664],
    ))
