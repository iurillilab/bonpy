import pandas as pd

from bonpy.time_utils import inplace_time_cols_fix

BALL_SMOOOTH_WND = 200


def parse_ball_log(file, t0=None, smooth_wnd=None):
    df = pd.read_csv(file, header=None)
    columns = []
    print(df.shape)
    if df.shape[1] == 3:
        columns = ["pitch", "yaw", "timestamp"]
    elif df.shape[1] == 4:
        columns = ["pitch", "yaw", "roll", "timestamp"]
    elif df.shape[1] == 5:
        columns = ["pitch", "yaw", "roll", "servo_pos", "timestamp"]
    df.columns = columns
    df = df[1:].reset_index()

    inplace_time_cols_fix(df)
    data_cols = [c for c in df.columns if "time" not in c and "servo_pos" not in c]

    for c in data_cols:
        df[c] = df[c].apply(lambda x: int(x))
    df[data_cols] -= 127  # set actual origin (original number is uint8)

    if smooth_wnd is not None:
        df.loc[:, data_cols] = (
            df.loc[:, data_cols].rolling(smooth_wnd, center=True).median()
        )

    return df


def parse_stim_log(file, t0=None):
    df = pd.read_csv(file)
    df.columns = ["laser", "timestamp"]
    df.reset_index(drop=True, inplace=True)
    inplace_time_cols_fix(df, t0=t0)
    return df


def parse_dlc_tracking(file, t0=None):
    df = pd.read_hdf(file)
    # remove first level of columns multiindex:
    df.columns = df.columns.droplevel(0)

    # Check if there are timestamps for the video:
    candidate_timestamps_name = file.parent / file.name.split("DLC")[0].replace("video", "timestamps")

    if candidate_timestamps_name.exists():
        timestamps_df = pd.read_csv(candidate_timestamps_name)
        inplace_time_cols_fix(timestamps_df)
        assert timestamps_df.shape[0] == df.shape[0], "Timestamps and DLC dataframes have different lengths!"
        
        df["time"] = timestamps_df["time"]

    return df
