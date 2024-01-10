import re
from collections import UserDict
from datetime import datetime
from pathlib import Path
from functools import cached_property
import pandas as pd
import pytz

# from bonpy.df_parsers import parse_ball_log, parse_stim_log
from bonpy.moviedata import OpenCVMovieData

FILETSTAMP_LENGTH = 19  # length of the file timestamp
FILETSTAMP_PARSER = "%Y-%m-%dT%H_%M_%S"  # pattern of the file timestamp
KEY_PATTERN = "log"  # pattern in the file that identify the key string
TIMEZONE = "Europe/Rome"

# PARSERS_DICT = dict(
#     ball_log=parse_ball_log, 
#     stim_log=parse_stim_log, 
#     laser_log=parse_stim_log,
# )


# Heuristic to identify the timestamp column
def _is_timestamp_column(values):
    """Identify the timestamp column in a dataframe."""
    timestamp_regex = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[\+\-]\d{2}:\d{2}"
    return all(re.match(timestamp_regex, str(x)) for x in values)


def _load_csv(filename, timestamp_begin=None):
    """Load a csv file and parse the timestamp column."""
    df = pd.read_csv(filename)
    timestamp_col = df.head().apply(
        _is_timestamp_column
    )  # [_is_timestamp_column(df.columns)]
    timestamp_cols = timestamp_col[timestamp_col].index

    # Check that only one timestamp column is found, in which case is a legitimate 
    # timestamped dataframe;
    if len(timestamp_cols) == 1:
        # In which case:
        # Parse timestamp column:
        df[timestamp_cols[0]] = pd.to_datetime(df[timestamp_cols[0]])

        # Compute time offset:
        if timestamp_begin is None:
            time_offset = df[timestamp_cols[0]][0]
        else:
            time_offset = pd.to_datetime(timestamp_begin).tz_localize(
                pytz.timezone(TIMEZONE)
            )

        df["time"] = (df[timestamp_cols[0]] - time_offset).dt.total_seconds()

    return df


def _load_avi(filename):
    return OpenCVMovieData(filename)


def _load_dlc_h5(file, t0=None):
    df = pd.read_hdf(file)
    # remove first level of columns multiindex:
    df.columns = df.columns.droplevel(0)  

    return df  


class LazyDataDict(UserDict):
    """Dictionary that loads data on demand using a dictionary of loaders."""

    # Dictionary defining loading functions for different file types:
    # TODO specify better eg h5 files
    LOADERS_DICT = dict(csv=_load_csv, 
                        # avi=_load_avi, 
                        h5=_load_dlc_h5)

    def __init__(self, path, timestamp_begin=None):
        self.root_path = Path(path)
        self.files_dict = self._discover_files(path)
        # self.loaders_dict = LOADERS_DICT
        self.timestamp_begin = timestamp_begin

        super().__init__()

    def keys(self):
        return self.files_dict.keys()

    @staticmethod
    def _discover_files(path):
        categories_to_discover = LazyDataDict.LOADERS_DICT.keys()

        files_dict = dict()
        for extension in categories_to_discover:
            for file in path.glob(f"*.{extension}"):
                # split over beginning of timestamp, assuming convention _YYYY...
                name = file.stem
                if "_202" in file.stem:
                    name = name.split("_202")[0]

                files_dict[name] = file

        return files_dict
    
    def __repr__(self) -> str:
        output = ""
        line_template = "{:<25} {:<13} {:<13} {:<13}\n"
        output += line_template.format("Filename", "Extension", "Has reader", "Loaded")
        for filename, path in self.files_dict.items():
            output += line_template.format(filename, 
                                           path.suffix, 
                                           ["No", "Yes"][int(path.suffix[1:] in self.LOADERS_DICT)],
                                           ["No", "Yes"][int(filename in self.data)])

        return output
        # return f"Lazy data dict with keys: {list(self.files_dict.keys())}"
    
    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, key):
        file = self.files_dict[key]
        extension = file.suffix[1:]
        if key not in self.data:
            self.data[key] = self.LOADERS_DICT[extension](file, self.timestamp_begin)

        return self.data[key]
