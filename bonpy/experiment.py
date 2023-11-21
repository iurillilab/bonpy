import re
from collections import UserDict
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytz

from bonpy.custom_dc import ExperimentMetadata
from bonpy.df_parsers import parse_ball_log, parse_stim_log
from bonpy.moviedata import OpenCVMovieData

FILETSTAMP_LENGTH = 19  # length of the file timestamp
FILETSTAMP_PARSER = "%Y-%m-%dT%H_%M_%S"  # pattern of the file timestamp
KEY_PATTERN = "log"  # pattern in the file that identify the key string
TIMEZONE = "Europe/Rome"

PARSERS_DICT = dict(
    ball_log=parse_ball_log, stim_log=parse_stim_log, laser_log=parse_stim_log
)


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


# Dictionary defining loading functions for different file types:
LOADERS_DICT = dict(csv=_load_csv, avi=_load_avi)


class LazyDict(UserDict):
    """Dictionary that loads data on demand using a dictionary of loaders."""

    def __init__(self, files_dict, loaders_dict=LOADERS_DICT, timestamp_begin=None):
        self.files_dict = files_dict
        self.loaders_dict = LOADERS_DICT
        self.timestamp_begin = timestamp_begin

        super().__init__()

    def keys(self):
        return self.files_dict.keys()
    
    def __repr__(self) -> str:
        output = ""
        line_template = "{:<25} {:<13} {:<13} {:<13}\n"
        output += line_template.format("Filename", "Extension", "Has reader", "Loaded")
        for filename, path in self.files_dict.items():
            output += line_template.format(filename, 
                                           path.suffix, 
                                           ["No", "Yes"][int(path.suffix[1:] in LOADERS_DICT)],
                                           ["No", "Yes"][int(filename in self.data)],
            )

        return output
        # return f"Lazy data dict with keys: {list(self.files_dict.keys())}"
    
    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, key):
        file = self.files_dict[key]
        extension = file.suffix[1:]
        if key not in self.data:
            self.data[key] = self.loaders_dict[extension](file, self.timestamp_begin)

        return self.data[key]


class Experiment:
    def __init__(self, root_path, session_id, timestamp, animal_id, paradigm_id):
        self.root_path = root_path
        # self.session_id = session_id

        self.files_dict = dict()
        self._discover_files()

        self.data_dict = LazyDict(self.files_dict, timestamp_begin=timestamp)

        self.metadata = ExperimentMetadata(
            timestamp=timestamp,
            session_id=session_id,
            animal_id=animal_id,
            paradigm_id=paradigm_id,
        )

    def _discover_files(self):
        categories_to_discover = LOADERS_DICT.keys()

        for extension in categories_to_discover:
            for file in self.root_path.glob(f"*.{extension}"):
                # split over beginning of timestamp:
                name = file.stem
                if "20" in file.stem:
                    name = name.split("_20")[0]

                self.files_dict[name] = file

    @classmethod
    def load_112023(cls, folder_path, exp_id=None):
        folder_path = Path(folder_path)
        time = folder_path.name
        date = folder_path.parent.name

        animal_id = folder_path.parent.parent.name
        exp_id = exp_id if exp_id is not None else folder_path.parent.parent.parent.name

        return cls(
            root_path=folder_path,
            animal_id=animal_id,
            paradigm_id=exp_id,
            session_id=date + "/" + time,
            timestamp=datetime.strptime(date + time, "%Y%m%d%H%M%S"),
        )

    ### Code for experiments before 11/2023
    # def _discover_files(self):
    #     """Find all files belonging to the Experiment.
    #     """
    #     # Find all matching files including or not the timeid:
    #     file_pattern = f"*{self.time_id}.csv" if self.time_id is not None else "*.csv"

    #     unique_times = []

    #     for file in self.root_path.glob(file_pattern):
    #         try:  #
    #             tstamp = datetime.strptime(file.stem[-FILETSTAMP_LENGTH:], FILETSTAMP_PARSER)
    #             unique_times.append(tstamp)
    #         except ValueError:
    #             pass

    #         file_key = file.stem.split(KEY_PATTERN)[0] + KEY_PATTERN

    #         self.files_dict[file_key] = file

    #     self.timestamp = tstamp
    #     tz = pytz.timezone(TIMEZONE)
    #     self.timestamp = tz.localize(self.timestamp)

    #     # self.metadata
    #     if len(set(unique_times)) > 1:
    #         raise ValueError("The folder contains multiple experiments! You have to specify a timeid")

    # def _set_all_attrs(self):
    #     # TODO implement caching for this part!!

    #     for key, filename in self.files_dict.items():
    #         load_func = PARSERS_DICT[key]
    #         print(filename)
    #         setattr(self, key, load_func(filename))


if __name__ == "__main__":
    path = "/Users/vigji/Desktop/eye-response/M13/20231115/145913"

    import numpy as np
    import pandas as pd
    from pathlib import Path
    from bonpy.experiment import Experiment

    main_path = Path("/Users/vigji/Desktop/eye-response")

    all_tracked = list(main_path.glob("M*/*/*/tracked*eye*.csv"))

    filtered = [f.parent for f in all_tracked if len(pd.read_csv(f)) > 50000]

    exp = Experiment.load_112023(filtered[0])
    exp.data_dict["tracked_eye-cam_video"]
