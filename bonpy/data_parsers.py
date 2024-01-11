import pandas as pd

from bonpy.time_utils import inplace_time_cols_fix

import flammkuchen as fl
import pandas as pd

# from bonpy.df_parsers import parse_ball_log, parse_stim_log
from bonpy.moviedata import OpenCVMovieData
from bonpy.time_utils import inplace_time_cols_fix


BALL_SMOOOTH_WND = 200


def _load_csv(filename, timestamp_begin=None):
    """Load a csv file and parse the timestamp column."""
    df = pd.read_csv(filename)
    inplace_time_cols_fix(df, timestamp_begin=timestamp_begin)
    return df


def _load_laser_log_csv(file, timestamp_begin=None):
    df = _load_csv(file, timestamp_begin=timestamp_begin)

    df.reset_index(drop=True, inplace=True)
    for i, content in enumerate(["frequency", "pulse_width", "stim_duraiton"]):
        df[content] = df["LaserSerialMex"].apply(lambda x: x.split(";")[i])

    return df


def _load_ball_log_csv(file, timestamp_begin=None, smooth_wnd=None):
    df = _load_csv(file, timestamp_begin=timestamp_begin)

    # if n_log_cols== 3:
    #     columns = ["pitch", "yaw", "timestamp"]
    # elif n_log_cols == 4:
    #     columns = ["pitch", "yaw", "roll", "timestamp"]
    # elif n_log_cols == 5:
    #     columns = ["pitch", "yaw", "roll", "servo_pos", "timestamp"]
    # df.columns = columns
    # df = df[1:].reset_index()
    # inplace_time_cols_fix(df)
    data_cols = [c for c in df.columns if c not in ["time", "timedelta"]]

    for c in data_cols:
        df[c] = df[c].apply(lambda x: int(x))
    df[data_cols] -= 127  # set actual origin (original number is uint8)

    if smooth_wnd is not None:
        df.loc[:, data_cols] = (
            df.loc[:, data_cols].rolling(smooth_wnd, center=True).median()
        )

    return df


def _load_avi(filename, timestamp_begin=None):
    return OpenCVMovieData(filename, timestamp_begin=timestamp_begin)


def _load_h5(filename, _=None):
    return fl.load(filename)


def _load_dlc_h5(file, timestamp_begin=None):
    df = pd.read_hdf(file)
    # remove first level of columns multiindex:
    df.columns = df.columns.droplevel(0)

    # Check if there are timestamps for the video:
    candidate_timestamps_name = file.parent / (
        file.name.split("DLC")[0].replace("video", "timestamps") + ".csv"
    )
    print(candidate_timestamps_name)
    if candidate_timestamps_name.exists():
        print("here")
        timestamps_df = pd.read_csv(candidate_timestamps_name)
        inplace_time_cols_fix(timestamps_df, timestamp_begin=timestamp_begin)
        assert (
            timestamps_df.shape[0] == df.shape[0]
        ), "Timestamps and DLC dataframes have different lengths!"

        df["time"] = timestamps_df["time"]

    return df


# TODO: just changing this dictionary and the functions it implements could be a reasonable
# way to versioning the data loading process; in the future new dictionaries could be defined
# for new data compositions.
LOADERS_DICT = dict(
    csv=_load_csv,
    laser_csv=_load_laser_log_csv,
    ball_csv=_load_ball_log_csv,
    avi=_load_avi,
    h5=_load_h5,
    DLC_h5=_load_dlc_h5,
)

if __name__ == "__main__":
    pass
    # df = _load_ball_log_csv(
    #    "/Users/vigji/code/bonpy/tests/assets/test_dataset/M1/20231214/162720/ball-log_2023-12-14T16_27_20.csv"
    # )
    # print(df.head())
