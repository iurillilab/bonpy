from datetime import datetime
from bonpy.df_parsers import parse_ball_log, parse_stim_log
from bonpy.custom_dc import ExperimentMetadata
import pytz
from pathlib import Path

FILETSTAMP_LENGTH = 19  # length of the file timestamp
FILETSTAMP_PARSER = "%Y-%m-%dT%H_%M_%S"  # pattern of the file timestamp
KEY_PATTERN = "log"  # pattern in the file that identify the key string
TIMEZONE = "Europe/Rome"

PARSERS_DICT = dict(ball_log=parse_ball_log, stim_log=parse_stim_log, laser_log=parse_stim_log)




class Experiment:
    def __init__(self, root_path, session_id, 
                 timestamp, animal_id, exp_id):

        self.root_path = root_path
        # self.session_id = session_id

        self.files_dict = dict()

        self._discover_files()
        self._set_all_attrs()

        self.metadata = ExperimentMetadata(timestamp=self.timestamp,
                                           session_id=session_id,
                                           animal_id=mouse_id,
                                           exp_id=exp_id)
        
    def _discover_files(self):
        file_pattern = 

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

    @classmethod
    def load_112023(cls, folder_path, exp_id=None):
        folder_path = Path(folder_path)
        time = folder_path.name
        date = folder_path.parent.name

        animal_id = folder_path.parent.parent.name
        exp_id = exp_id if exp_id is not None else folder_path.parent.parent.parent.name

        return cls(root_path=folder_path,
                   animal_id=animal_id, 
                   exp_id=exp_id, 
                   session_id=date + "/" + time, 
                   timestamp=datetime.strptime(date + time, '%Y%m%d%H%M%S')
                   )

    #@staticmethod
    #def _


if __name__ == "__main__":
    path = "/Users/vigji/Desktop/headfixed/M13/20231110/135615"

    exp = Experiment.load_112023(path)