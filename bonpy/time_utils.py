import re

import pandas as pd
import pytz

TIMEZONE = "Europe/Rome"


# Heuristic to identify the timestamp column
def _is_timestamp_column(values):
    """Identify the timestamp column in a dataframe."""
    timestamp_regex = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[\+\-]\d{2}:\d{2}"
    return all(re.match(timestamp_regex, str(x)) for x in values)


def inplace_time_cols_fix_and_resample(df, timestamp_begin=None):
    timestamp_col = df.head().apply(_is_timestamp_column)
    timestamp_cols = timestamp_col[timestamp_col].index

    # Check that only one timestamp column is found, in which case is a legitimate
    # timestamped dataframe;
    assert len(timestamp_cols) <= 1, "More than one timestamp column found!"

    if len(timestamp_cols) > 0:
        # In which case:
        # Parse timestamp column:
        timestamp_col = timestamp_cols[0]
        print(f"Found timestamp column: {timestamp_col}")
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])

        # Compute time offset:
        if timestamp_begin is None:
            time_offset = df[timestamp_col][0]
        else:
            time_offset = pd.to_datetime(timestamp_begin).tz_localize(
                pytz.timezone(TIMEZONE)
            )

        df["timedelta"] = df[timestamp_col] - time_offset
        df["time"] = df["timedelta"].dt.total_seconds()

        df.drop([timestamp_col], axis=1, inplace=True)


def interpolate_df(input_df, new_timebin="10ms", from_zero=True):
    """Interpolate dataframe to new timebin, assuming there is a time column as
    per standard bonpy loading function.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to interpolate, must have a time column
    new_timebin : str, optional
        New time, by default "10ms"
    from_zero : bool, optional
        Whether to start from zero the interpolated array, by default True

    Returns
    -------
    pd.DataFrame
        Interpolated dataframe
    """
    if from_zero:
        # Add a first row with time 0 and all other columns np.nan
        # Initialize empty dataframe with same columns as eye_df and fill with nans
        pad_df = pd.DataFrame(
            np.full((1, input_df.shape[1]), np.nan), columns=input_df.columns
        )
        pad_df["time"] = 0

        input_df = pd.concat([pad_df, input_df], ignore_index=True)

    time_col = pd.to_datetime(input_df["time"], unit="s")
    resampled_df = (
        input_df.set_index(time_col).resample(new_timebin).mean().interpolate()
    )
    resampled_df.reset_index(inplace=True, drop=True)

    return resampled_df
