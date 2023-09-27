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
        node=['gpu-n53', 'smp-n10'],
        user=['user1', 'user2'],
        module=['gcc/8.2.0', 'openmpi'],
        path=['/software/gcc/8.2.0.lua', '/software/gcc/openmpi/4.0.3.lua'],
        host=['gpu-n53.crc.pitt.edu', 'smp-n10.crc.pitt.edu'],
        time=[1682407234.086799, 1682407234.103664],
    ))


def write_mock_data(data: pd.DataFrame, path: Path) -> None:
    """Write mock data to disk using the expected log format

    Args:
        data: The data to write to disk
        path: The path to write data to
    """

    log_format = "{date} {node} ModuleUsageTracking: user={user} module={module} path={path} host={host} time={time}\n"
    with path.open('w') as file:
        for _, row in data.iterrows():
            file.write(log_format.format(**row))
