import pandas as pd
from dateutil.parser import parse

BALL_SMOOOTH_WND = 200

def time_cols_fix(df, t0=None):
    # TODO to substitute with some form of datetime.strptime(df["timestamp"][0], "%Y-%m-%dT%H:%M:%S")
    df["timestamp"] = df["timestamp"].apply(parse)

    if t0 is None:
        t0 = df["timestamp"][0]
    df["timedelta"] = df["timestamp"] - t0  # .dt.total_seconds()
    df["time"] = df["timedelta"].dt.total_seconds()
    df.drop(["timestamp"], axis=1, inplace=True)


def parse_ball_log(file, t0=None, smooth_wnd=None):
    df = pd.read_csv(file, header=None)

    df.columns = ["pitch", "yaw", "roll", "timestamp"] if df.shape[1] > 3 else ["pitch", "yaw", "timestamp"]

    time_cols_fix(df)

    data_cols = [c for c in df.columns if "time" not in c]
    df[data_cols] -= 127  # set actual origin (original number is uint8)

    if smooth_wnd is not None:
        df.loc[:, data_cols] = df.loc[:, data_cols].rolling(smooth_wnd, center=True).median()

    return df


def parse_stim_log(file, t0=None)
    df = pd.read_csv(file)  # .loc[1:, ["Timestamp"]]
    df.columns = ["laser", "timestamp"]
    df.reset_index(drop=True, inplace=True)
    time_cols_fix(df, t0=t0)
    # stim_df["timestamp"] = stim_df["timestamp"].apply(parse)
    # stim_df["timestamp"] = (stim_df["timestamp"] - t0).dt.total_seconds()
    return df


