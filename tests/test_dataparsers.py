import numpy as np
from bonpy import data_dict
from bonpy.data_parsers import (
    _load_avi,
    _load_csv,
    _load_h5,
    _load_laser_log_csv,
    _load_ball_log_csv,
    _load_dlc_h5,
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