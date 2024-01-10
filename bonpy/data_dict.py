from collections import UserDict
from pathlib import Path
import pandas as pd
import flammkuchen as fl

from bonpy.time_utils import inplace_time_cols_fix

# from bonpy.df_parsers import parse_ball_log, parse_stim_log
from bonpy.moviedata import OpenCVMovieData

# FILETSTAMP_LENGTH = 19  # length of the file timestamp
# FILETSTAMP_PARSER = "%Y-%m-%dT%H_%M_%S"  # pattern of the file timestamp
# KEY_PATTERN = "log"  # pattern in the file that identify the key string

# PARSERS_DICT = dict(
#     ball_log=parse_ball_log,
#     stim_log=parse_stim_log,
#     laser_log=parse_stim_log,
# )


def _load_csv(filename, timestamp_begin=None):
    """Load a csv file and parse the timestamp column."""
    df = pd.read_csv(filename)
    inplace_time_cols_fix(df, timestamp_begin=timestamp_begin)
    return df


def _load_avi(filename, timestamp_begin=None):
    return OpenCVMovieData(filename)


def _load_h5(filename, _):
    return fl.load(filename)


def _load_dlc_h5(file, timestamp_begin=None):
    df = pd.read_hdf(file)
    # remove first level of columns multiindex:
    df.columns = df.columns.droplevel(0)

    # Check if there are timestamps for the video:
    candidate_timestamps_name = file.parent / (file.name.split("DLC")[0].replace("video", "timestamps") + ".csv")
    print(candidate_timestamps_name)
    if candidate_timestamps_name.exists():
        print("here")
        timestamps_df = pd.read_csv(candidate_timestamps_name)
        inplace_time_cols_fix(timestamps_df, timestamp_begin=timestamp_begin)
        assert timestamps_df.shape[0] == df.shape[0], "Timestamps and DLC dataframes have different lengths!"
        
        df["time"] = timestamps_df["time"]

    return df


class LazyDataDict(UserDict):
    """Dictionary that loads data on demand using a dictionary of loaders."""

    # Dictionary defining loading functions for different file types.
    # By default only extention is used to identify the loader, but
    # this can be changed by prepending name patterns to match with _ 
    # (e.g. DLC_h5 matches all h5 files containing DLC in the name)
    # The order of this dictionary matter! Loaders will be tried in order top to bottom,
    # so if a file matches multiple loaders, the last one will be used.
    LOADERS_DICT = dict(
        csv=_load_csv,
        avi=_load_avi,
        h5=_load_h5,
        DLC_h5=_load_dlc_h5,
    )

    def __init__(self, path, timestamp_begin=None):
        self.root_path = Path(path)
        self.files_dict = self._discover_files(self.root_path)

        self.timestamp_begin = timestamp_begin

        super().__init__()

    def keys(self):
        return self.files_dict.keys()

    @staticmethod
    def _discover_files(path):
        categories_to_discover = LazyDataDict.LOADERS_DICT.keys()

        # Loop over all categories that have a parser defined.
        # For each, make a dictionary of dictionaries
        files_dict = dict()
        for file in path.glob("*"):
            name = file.stem
            file_dict = dict(file=file, category="-")
            for category in categories_to_discover:
                extension = category.split("_")[-1]
                pattern = category.split('_')[0] if "_" in category else ""

                if file.suffix[1:] == extension and pattern in file.stem:

                    # split over beginning of timestamp, assuming convention _YYYY...
                    name = file.stem
                    if "_202" in file.stem:
                        name = name.split("_202")[0]

                    if "_" in category:
                        name = name + "_" + category.split("_")[0]

                    file_dict = dict(file=file, category=category)

            files_dict[name] = file_dict

        return files_dict

    def __repr__(self) -> str:
        output = ""
        line_template = "{:<25} {:<13} {:<13} {:<13} {:<13}\n"
        output += line_template.format("Filename", "Extension", "Category", "Has reader", "Loaded")
        for filename, file_info in self.files_dict.items():
            path = file_info["file"]
            print(path)
            category = file_info["category"]
            output += line_template.format(
                filename,
                path.suffix,
                category,
                ["No", "Yes"][int(category in self.LOADERS_DICT)],
                ["No", "Yes"][int(filename in self.data)],
            )

        return output
        # return f"Lazy data dict with keys: {list(self.files_dict.keys())}"

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, key):
        file = self.files_dict[key]["file"]
        category = self.files_dict[key]["category"]
        if key not in self.data:
            self.data[key] = self.LOADERS_DICT[category](file, self.timestamp_begin)

        return self.data[key]
