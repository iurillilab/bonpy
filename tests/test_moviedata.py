# Test classes in bonpy/moviedata.py using the asset folder as fixture:
from numpy import dtype
import pytest
from pathlib import Path
from bonpy.moviedata import OpenCVMovieData

# from tests.conftest import asset_moviedata_file


# test over multiple arguments
@pytest.mark.parametrize("string_arg", [True, False])
def test_opencvmoviedata_open(asset_moviedata_file, string_arg):
    """Test if OpenCVMovieData opens a file."""
    input_file = asset_moviedata_file
    if string_arg:
        input_file = str(input_file)

    mdata = OpenCVMovieData(asset_moviedata_file)
    assert mdata is not None


def test_opencvmoviedata_metadata(asset_moviedata_file):
    """Test if OpenCVMovieData opens a file."""
    mdata = OpenCVMovieData(asset_moviedata_file)

    # Test content of the metadata dict:
    assert mdata.metadata.n_frames == 500
    assert mdata.metadata.width == 320
    assert mdata.metadata.height == 240
    assert mdata.metadata.dtype == dtype("uint8")
    assert mdata.metadata.bw == True


@pytest.mark.parametrize(
    "slicer, expected_shape",
    [
        (1, (240, 320)),
        ([1], (1, 240, 320)),
        ([1, 2, 3], (3, 240, 320)),
        # (([1,2,3], 0, slice(0, 10)), (3, 1, 10)),
        (([1, 2, 3], slice(0, 10), slice(5, 10)), (3, 10, 5)),
        (([1, 2, 3], slice(0, -10), slice(5, 10)), (3, 230, 5)),
    ],
)
def test_opencvmoviedata_data(asset_moviedata_file, slicer, expected_shape):
    mdata = OpenCVMovieData(asset_moviedata_file)

    assert mdata[slicer].shape == expected_shape


if __name__ == "__main__":
    asset_moviedata_file = (
        Path(__file__).parent
        / "assets"
        / "dataset"
        / "M1"
        / "20231201"
        / "095001"
        / "eye-cam_video_2023-12-14T16_27_20.avi"
    )

    test_opencvmoviedata_open(asset_moviedata_file)
