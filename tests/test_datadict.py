import numpy as np

from bonpy.data_dict import LazyDataDict


def test_lazy_data_dict(asset_moviedata_folder):
    data_dict = LazyDataDict(asset_moviedata_folder)

    assert tuple(data_dict.keys()) == (
        "eye-cam_video",
        "eye-cam_video_DLC",
        "eye-cam_timestamps",
        "random_file",
        "simple_tstamp_csv",
        "random_format",
        "simple_h5",
    )


def test_csv_loading(asset_moviedata_folder):
    data_dict = LazyDataDict(asset_moviedata_folder)

    simple_csv_with_timestamp = data_dict["simple_tstamp_csv"]

    assert simple_csv_with_timestamp.shape == (500, 2)
    assert simple_csv_with_timestamp.columns.tolist() == ["timedelta", "time"]
    assert np.allclose(
        simple_csv_with_timestamp["time"].values[-5:],
        [15.6973952, 15.725568, 15.754176, 15.7832448, 15.8210688],
    )


def test_h5_loading(asset_moviedata_folder):
    data_dict = LazyDataDict(asset_moviedata_folder)
    simple_h5 = data_dict["simple_h5"]
    assert list(simple_h5.keys())


def test_dlc_loading(asset_moviedata_folder):
    data_dict = LazyDataDict(asset_moviedata_folder)
    dlc_h5 = data_dict["eye-cam_video_DLC"]

    assert dlc_h5.shape == (500, 37)
    assert dlc_h5.columns.tolist()[:2] == [("top-eyelid_1", "x"), ("top-eyelid_1", "y")]


def test_video_loading(asset_moviedata_folder):
    data_dict = LazyDataDict(asset_moviedata_folder)

    moviedata = data_dict["eye-cam_video"]
    assert moviedata.shape == (500, 240, 320)
    assert moviedata.metadata.n_frames == 500
    assert moviedata.metadata.width == 320
