import numpy as np
import pandas as pd

from bonpy.data_parsers import (
    _load_avi,
    _load_ball_log_csv,
    _load_csv,
    _load_cube_log_csv,
    _load_dlc_h5,
    _load_h5,
    _load_laser_log_csv,
    _load_pupil_dlc_h5,
)


def test_csv_loading(asset_moviedata_folder):
    simple_csv_with_timestamp = _load_csv(
        asset_moviedata_folder / "eye-cam_timestamps_2023-12-14T16_27_20.csv"
    )

    assert simple_csv_with_timestamp.shape == (500, 2)
    assert simple_csv_with_timestamp.columns.tolist() == ["timedelta", "time"]
    assert np.allclose(
        simple_csv_with_timestamp["time"].values[-5:],
        [15.6973952, 15.725568, 15.754176, 15.7832448, 15.8210688],
    )


def test_h5_loading(asset_moviedata_folder):
    simple_h5 = _load_h5(asset_moviedata_folder / "random_file.h5")
    assert list(simple_h5.keys())


def test_dlc_loading(asset_moviedata_folder):
    dlc_h5 = _load_dlc_h5(
        asset_moviedata_folder
        / "eye-cam_video_2023-12-14T16_27_20DLC_resnet50_eye-pupilDec16shuffle1_15000.h5"
    )

    assert dlc_h5.shape == (500, 37)
    assert dlc_h5.columns.tolist()[:2] == [("top-eyelid_1", "x"), ("top-eyelid_1", "y")]


def test_video_loading(asset_moviedata_folder):
    moviedata = _load_avi(
        asset_moviedata_folder / "eye-cam_video_2023-12-14T16_27_20.avi"
    )
    assert moviedata.shape == (500, 240, 320)
    assert moviedata.metadata.n_frames == 500
    assert moviedata.metadata.width == 320


def test_ball_log_loading(asset_moviedata_folder):
    ball_log = _load_ball_log_csv(
        asset_moviedata_folder / "ball-log_2023-12-14T16_27_20.csv"
    )
    assert ball_log.shape == (1000, 6)
    assert ball_log.columns.tolist() == ["x0", "x1", "y0", "y1", "timedelta", "time"]


def test_cube_log_loading(asset_moviedata_folder):
    cube_log = _load_cube_log_csv(
        asset_moviedata_folder / "cube-positions_2023-12-14T16_27_20.csv"
    )
    assert cube_log.shape == (144, 5)
    assert cube_log.columns.tolist() == [
        "radius",
        "theta",
        "direction",
        "timedelta",
        "time",
    ]


def test_laser_log_loading(asset_moviedata_folder):
    laser_log = _load_laser_log_csv(
        asset_moviedata_folder / "laser-log_2023-12-14T16_27_20.csv"
    )
    assert laser_log.shape == (144, 6)
    assert laser_log.columns.tolist() == [
        "LaserSerialMex",
        "timedelta",
        "time",
        "frequency",
        "pulse_width",
        "stim_duration",
    ]


def test_pupil_dlc_loading(asset_moviedata_folder):
    pupil_dlc = _load_pupil_dlc_h5(
        asset_moviedata_folder
        / "eye-cam_video_2023-12-14T16_27_20DLC_resnet50_eye-pupilDec16shuffle1_15000.h5"
    )
    assert pupil_dlc.shape == (500, 42)
    cols = pd.MultiIndex.from_tuples(
        [
            ("top-eyelid_1", "x"),
            ("top-eyelid_1", "y"),
            ("top-eyelid_1", "likelihood"),
            ("top-eyelid_2", "x"),
            ("top-eyelid_2", "y"),
            ("top-eyelid_2", "likelihood"),
            ("top-eyelid_3", "x"),
            ("top-eyelid_3", "y"),
            ("top-eyelid_3", "likelihood"),
            ("top-eyelid_4", "x"),
            ("top-eyelid_4", "y"),
            ("top-eyelid_4", "likelihood"),
            ("bottom-eyelid_2", "x"),
            ("bottom-eyelid_2", "y"),
            ("bottom-eyelid_2", "likelihood"),
            ("bottom-eyelid_1", "x"),
            ("bottom-eyelid_1", "y"),
            ("bottom-eyelid_1", "likelihood"),
            ("pupil_1", "x"),
            ("pupil_1", "y"),
            ("pupil_1", "likelihood"),
            ("pupil_2", "x"),
            ("pupil_2", "y"),
            ("pupil_2", "likelihood"),
            ("pupil_3", "x"),
            ("pupil_3", "y"),
            ("pupil_3", "likelihood"),
            ("pupil_4", "x"),
            ("pupil_4", "y"),
            ("pupil_4", "likelihood"),
            ("pupil_5", "x"),
            ("pupil_5", "y"),
            ("pupil_5", "likelihood"),
            ("pupil_6", "x"),
            ("pupil_6", "y"),
            ("pupil_6", "likelihood"),
            ("time", ""),
            ("avg_pupil_diameter", ""),
            ("avg_pupil_x", ""),
            ("avg_pupil_y", ""),
            ("main_ax_proj", ""),
            ("sec_ax_proj", ""),
        ],
        names=["bodyparts", "coords"],
    )
    assert all(pupil_dlc.columns == cols)
