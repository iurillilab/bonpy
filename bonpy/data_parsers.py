from pathlib import Path
from re import M

import flammkuchen as fl
import numpy as np
import pandas as pd

# from bonpy.df_parsers import parse_ball_log, parse_stim_log
from bonpy.moviedata import OpenCVMovieData
from bonpy.time_utils import inplace_time_cols_fix_and_resample

BALL_SMOOOTH_WND = 200


def _load_csv(filename, timestamp_begin=None):
    """Load a csv file and parse the timestamp column."""
    df = pd.read_csv(filename)
    inplace_time_cols_fix_and_resample(df, timestamp_begin=timestamp_begin)
    return df


def _load_laser_log_csv(file, timestamp_begin=None):
    df = _load_csv(file, timestamp_begin=timestamp_begin)

    # df.reset_index(drop=True, inplace=True)
    for i, content in enumerate(["frequency", "pulse_width", "stim_duration"]):
        df[content] = df["LaserSerialMex"].apply(lambda x: x.split(";")[i])

    return df

def _load_laser_log_v01_csv(file, timestamp_begin=None):
    df = _load_csv(file, timestamp_begin=timestamp_begin)

    # df.reset_index(drop=True, inplace=True)
    for i, content in enumerate(["frequency", "pulse_width", "stim_duration"]):
        df[content] = df["Value"].apply(lambda x: x.split(";")[i])

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


def _load_cube_log_csv(file, timestamp_begin=None):
    MIN_DURATION = 1

    df = _load_csv(file, timestamp_begin=timestamp_begin)
    # Exclude initial centering of position:
    df = df.iloc[1:]
    COLUMN_OPTIONS_DICT = {
        "Value.Theta": "theta",
        "Value.Radius": "radius",
        "Value.Direction": "direction",
        "Value.CircleRadius": "radius",
    }
    columns_renaming_dict = {
        k: val for k, val in COLUMN_OPTIONS_DICT.items() if k in df.columns
    }
    df.rename(
        columns=columns_renaming_dict,
        inplace=True,
    )
    # Assumes one every two movements is a reset movement:
    actual_movements_df = df.iloc[::2].copy()
    hold_times = df.iloc[1::2].index - df.iloc[::2].index
    actual_movements_df["hold_time"] = hold_times
    actual_movements_df = actual_movements_df[
        actual_movements_df["hold_time"] > MIN_DURATION
    ]
    # df.reset_index(drop=True, inplace=True)
    return actual_movements_df


def _load_avi(filename, timestamp_begin=None):
    return OpenCVMovieData(filename, timestamp_begin=timestamp_begin)


def _load_h5(filename, _=None):
    return fl.load(filename)


def load_dlc_h5(file, timestamp_begin=None):
    file = Path(file)

    df = pd.read_hdf(file)
    # remove first level of columns multiindex:
    df.columns = df.columns.droplevel(0)

    # Check if there are timestamps for the video:
    candidate_timestamps_name = file.parent / (
        file.name.split("DLC")[0].replace("video", "timestamps") + ".csv"
    )

    if candidate_timestamps_name.exists():
        timestamps_df = pd.read_csv(candidate_timestamps_name)
        inplace_time_cols_fix_and_resample(
            timestamps_df, timestamp_begin=timestamp_begin
        )
        assert (
            timestamps_df.shape[0] == df.shape[0]
        ), "Timestamps and DLC dataframes have different lengths!"

        df.index = timestamps_df.index

    return df


def load_dlc_csv(file, timestamp_begin=None):
    file = Path(file)

    df = pd.read_csv(file)
    # remove first level of columns multiindex:
    df.columns = df.columns.droplevel(0)

    # Check if there are timestamps for the video:
    candidate_timestamps_name = file.parent / (
        file.name.split("DLC")[0].replace("video", "timestamps") + ".csv"
    )

    if candidate_timestamps_name.exists():
        timestamps_df = pd.read_csv(candidate_timestamps_name)
        inplace_time_cols_fix_and_resample(
            timestamps_df, timestamp_begin=timestamp_begin
        )
        assert (
            timestamps_df.shape[0] == df.shape[0]
        ), "Timestamps and DLC dataframes have different lengths!"

        df.index = timestamps_df.index

    return df


def _project_points_onto_line(points):
    # Calculate the mean of x and y
    mean_x = np.nanmean(points[:, 0])
    mean_y = np.nanmean(points[:, 1])

    # Calculate the slope of the line (principal component)
    m = np.nansum((points[:, 0] - mean_x) * (points[:, 1] - mean_y)) / np.nansum(
        (points[:, 0] - mean_x) ** 2
    )

    # Calculate the intercept of the line
    b = mean_y - m * mean_x
    # print(b, m)

    # Project each point onto the line
    projected_points = np.zeros_like(points)
    for i, (x, y) in enumerate(points):
        x_proj = (x + m * y - m * b) / (1 + m**2)
        y_proj = (m * x + (m**2) * y - (m**2) * b) / (1 + m**2) + b
        projected_points[i] = [x_proj, y_proj]
    # print(np.nansum(np.isnan(projected_points)))

    return projected_points


# The second level of the column multiindex contains x, y and likelyhood.
# For each label (first level of the column multiindex), set x and y to np.nan if the likelyhood is below a threshold:
def _remove_low_likelyhood(df, likelihood_threshold=0.95):
    df_interp = df.copy()
    # Get unique labels from the first level of the multiindex
    labels = df.columns.get_level_values(0).unique()
    for label in labels:
        # if label == "time":
        #     continue
        # Select columns for current label
        # label_data = df_interp.loc[:, label]
        # Check if the likelihood is below the threshold
        low_likelihood = df_interp[(label, "likelihood")] < likelihood_threshold

        # Set 'x' and 'y' to np.nan where likelihood is low
        for coord in ["x", "y"]:
            df_interp.loc[low_likelihood, (label, coord)] = np.nan
        # label_data.loc[low_likelihood, 'x'] = np.nan
        # label_data.loc[low_likelihood, 'y'] = np.nan

    return df_interp.interpolate(method="linear", axis=0)


def _compute_avg_bodypart_position(df, bodypart_name):
    # In the dataframe there's a multilevel column index, with the first level being the body part name.
    # Take all that have the first level of the column index being "eyelid":
    all_bodypart_cols = df.columns[
        [bodypart_name in col for col in df.columns.get_level_values(0)]
    ]

    # Compute the average eyelid position by averaging over x and y coordinates, indicated in the second level of the column index:
    bodypart_data = df[all_bodypart_cols]

    # Compute the mean for each coordinate
    # Assuming the second level of the column index has 'x' and 'y'
    mean_df = dict()
    for coord in ["x", "y"]:
        mean_df[coord] = bodypart_data.xs(coord, level=1, axis=1).mean(axis=1)

    return pd.DataFrame(mean_df)


def _compute_mean_pupil_diameter(df):
    all_pupil_diameters = []

    for i in range(3):
        diff = df[f"pupil_{i+1}"] - df[f"pupil_{i+2}"]
        all_pupil_diameters.append(np.sqrt(diff.x**2 + diff.y**2))

    return pd.concat(all_pupil_diameters, axis=1).mean(axis=1)


def _load_pupil_dlc_h5(file, timestamp_begin=None):
    df = load_dlc_h5(file, timestamp_begin=timestamp_begin)

    df = _remove_low_likelyhood(df)
    avg_eyelid_abs = _compute_avg_bodypart_position(df, "eyelid")
    avg_pupil_abs = _compute_avg_bodypart_position(df, "pupil")
    avg_pupil_pos = avg_pupil_abs - avg_eyelid_abs
    avg_pupil_diameter = _compute_mean_pupil_diameter(df)

    eye_df = df  # exp.data_dict["eye-cam_timestamps"]
    eye_df["pupil_likelihood"] = (
        sum([eye_df[(f"pupil_{i+1}", "likelihood")] for i in range(6)]) / 6
    )
    eye_df["avg_pupil_diameter"] = avg_pupil_diameter
    eye_df["avg_pupil_x"] = avg_pupil_pos.x
    eye_df["avg_pupil_y"] = avg_pupil_pos.y
    projections = _project_points_onto_line(
        eye_df[["avg_pupil_x", "avg_pupil_y"]].values
    )
    eye_df["main_ax_proj"] = projections[:, 0]
    eye_df["sec_ax_proj"] = projections[:, 1]

    return eye_df


def _load_top_dlc_h5(file, timestamp_begin=None):
    df = load_dlc_h5(file, timestamp_begin=timestamp_begin)
    df["centered_nose"] = (
        df[("nose", "x")] - (df[("nose-l", "x")] + df[("nose-r", "x")]) / 2
    )

    return df


# TODO: just changing this dictionary and the functions it implements could be a reasonable
# way to versioning the data loading process; in the future new dictionaries could be defined
# for new data compositions.
LOADER_DICT = dict(
    v00=dict(
        csv=_load_csv,
        laser_csv=_load_laser_log_csv,
        ball_csv=_load_ball_log_csv,
        cube_csv=_load_cube_log_csv,
        avi=_load_avi,
        h5=_load_h5,
        DLC_h5=load_dlc_h5,
        eye_DLC_h5=_load_pupil_dlc_h5,
        top_DLC_h5=_load_top_dlc_h5,
    ),
    v01=dict(
        csv=_load_csv,
        laser_csv=_load_laser_log_v01_csv,
        ball_csv=_load_ball_log_csv,
        motor_csv=_load_cube_log_csv,
        avi=_load_avi,
        h5=_load_h5,
        DLC_h5=load_dlc_h5,
        eye_DLC_h5=_load_pupil_dlc_h5,
        top_DLC_h5=_load_top_dlc_h5,
    ))

MOUSE_LOADER_DICT = dict(M13=LOADER_DICT["v00"], 
                         M14=LOADER_DICT["v00"],
                         M15=LOADER_DICT["v00"], 
                         M16=LOADER_DICT["v00"],
                         M17=LOADER_DICT["v00"], 
                         M18=LOADER_DICT["v00"],
                         M19=LOADER_DICT["v00"], 
                         M20=LOADER_DICT["v00"],
                         M21=LOADER_DICT["v01"], 
                         M22=LOADER_DICT["v01"],
                         M23=LOADER_DICT["v01"], 
                         M24=LOADER_DICT["v01"])

if __name__ == "__main__":
    df = _load_laser_log_csv(
        "/Users/vigji/Desktop/test_mpa_dir/M21/20240421/165242"
    )
