from pathlib import Path

import pytest


# fixture for the asset folder
@pytest.fixture
def asset_moviedata_folder():
    return (
        Path(__file__).parent / "assets" / "test_dataset" / "M13" / "20231214" / "162720"
    )


# fixture for the movie file
@pytest.fixture
def asset_moviedata_file(asset_moviedata_folder):
    filename = asset_moviedata_folder / "eye-cam_video_2023-12-14T16_27_20.avi"
    return filename
    # if return_string:
    #     return str(filename)
    # else:
    #     return filename
