from dateutil.parser import parse
import re
import pandas as pd
import pytz

TIMEZONE = "Europe/Rome"


# Heuristic to identify the timestamp column
def _is_timestamp_column(values):
    """Identify the timestamp column in a dataframe."""
    timestamp_regex = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[\+\-]\d{2}:\d{2}"
    return all(re.match(timestamp_regex, str(x)) for x in values)


def inplace_time_cols_fix(df, timestamp_begin=None):

    timestamp_col = df.head().apply(
        _is_timestamp_column
    )
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
        df["time"] = df["timedelta"] .dt.total_seconds()

        df.drop([timestamp_col], axis=1, inplace=True)

