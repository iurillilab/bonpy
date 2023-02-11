from datetime import datetime
from bonpy.df_parsers import parse_ball_log, parse_stim_log
from bonpy.custom_dc import ExperimentMetadata
import pytz

FILETSTAMP_LENGTH = 19  # length of the file timestamp
FILETSTAMP_PARSER = "%Y-%m-%dT%H_%M_%S"  # pattern of the file timestamp
KEY_PATTERN = "log"  # pattern in the file that identify the key string
TIMEZONE = "Europe/Rome"

PARSERS_DICT = dict(ball_log=parse_ball_log, stim_log=parse_stim_log)


class Experiment:
    def __init__(self, root_path, time_id=None, mouse_id=None, exp_id=None):

        self.root_path = Path(root_path)
        self.time_id = time_id

        self.timestamp = None  # this will be set reading the files
        self.mouse_id = mouse_id if mouse_id is not None else self.root_path.name
        self.exp_id = exp_id if exp_id is not None else self.root_path.parent.name

        self.files_dict = dict()

        self._discover_files()
        self._set_all_attrs()

        self.metadata = ExperimentMetadata(timestamp=self.timestamp,
                                           mouse_id=self.mouse_id,
                                           exp_id=self.exp_id)

    def _discover_files(self):
        """Find all files belonging to the Experiment.
        """
        # Find all matching files including or not the timeid:
        file_pattern = f"*{self.time_id}.csv" if self.time_id is not None else "*.csv"

        unique_times = []

        for file in self.root_path.glob(file_pattern):
            try:  #
                tstamp = datetime.strptime(file.stem[-FILETSTAMP_LENGTH:], FILETSTAMP_PARSER)
                unique_times.append(tstamp)
            except ValueError:
                pass

            file_key = file.stem.split(KEY_PATTERN)[0] + KEY_PATTERN

            self.files_dict[file_key] = file

        self.timestamp = tstamp
        tz = pytz.timezone(TIMEZONE)
        self.timestamp = tz.localize(self.timestamp)

        # self.metadata
        if len(set(unique_times)) > 1:
            raise ValueError("The folder contains multiple experiments! You have to specify a timeid")

    def _set_all_attrs(self):
        # TODO implement caching for this part!!

        for key, val in self.files_dict.items():
            load_func = PARSERS_DICT[key]
            setattr(self, key, load_func)

    @staticmethod
    def _


exp = Experiment("/Users/vigji/Desktop/HF_MPA/testmouse")
file = exp.files_dict["ball_log"]