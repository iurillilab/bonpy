from bonpy.data_dict import LazyDataDict


def test_lazy_data_dict(asset_moviedata_folder):
    data_dict = LazyDataDict(asset_moviedata_folder)

    assert tuple(data_dict.keys()) == (
        "eye-cam_video",
        "eye-cam_video_eye",
        "ball-log_ball",
        "laser-log_laser",
        "cube-positions_cube",
        "eye-cam_timestamps",
        "random_file",
        "simple_tstamp_csv",
        "random_format",
        "simple_h5",
    )


# test lazy loading behavior:
def test_lazy_loading(asset_moviedata_folder):
    data_dict = LazyDataDict(asset_moviedata_folder)

    for key in data_dict.keys():
        assert key not in data_dict.data

    for key in data_dict.keys():
        data_dict[key]

    for key in data_dict.keys():
        assert key in data_dict.data
