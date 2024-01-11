import os
from datetime import datetime
from functools import cached_property
from pathlib import Path

import pandas as pd

from bonpy.custom_dc import ExperimentMetadata
from bonpy.data_dict import LazyDataDict


class Experiment:
    def __init__(self, root_path, session_id, timestamp, animal_id, paradigm_id):
        self.root_path = root_path
        # self.session_id = session_id

        self.files_dict = dict()
        # self._discover_files()

        self.data_dict = LazyDataDict(self.root_path, timestamp_begin=timestamp)

        self.metadata = ExperimentMetadata(
            timestamp=timestamp,
            session_id=session_id,
            animal_id=animal_id,
            paradigm_id=paradigm_id,
        )

    @cached_property
    def size_gb(self):
        total_size = 0
        for file in self.root_path.rglob("*"):
            if file.is_file():
                total_size += os.path.getsize(file)
        return total_size / 1e9

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

    def __repr__(self) -> str:
        return f"Experiment {self.metadata.paradigm_id} on animal: {self.metadata.animal_id} ({self.metadata.timestamp})"

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

    main_path = Path("/Users/vigji/Desktop/eye-response")

    all_tracked = list(main_path.glob("M*/*/*/tracked*eye*.csv"))

    filtered = [f.parent for f in all_tracked if len(pd.read_csv(f)) > 50000]

    exp = Experiment.load_112023(filtered[0])
    exp.data_dict["tracked_eye-cam_video"]
