import pytest
from bonpy.crop_utils import crop_around_idxs, crop_around_times
import numpy as np

@pytest.mark.parametrize("filling", [np.nan, -1])
def test_1d_crop_around_idxs(filling):
    crop = crop_around_idxs(np.arange(100), np.array([1, 20, 99]), [-2, 2], out_of_range_fill=filling)
    assert np.allclose(crop, np.array([[filling, 18., 97.],
       [ 0., 19., 98.],
       [ 1., 20., 99.],
       [ 2., 21., filling]]), equal_nan=True)
    assert crop.dtype == type(filling)
    assert np.allclose(crop[0, 0], filling, equal_nan=True)

@pytest.mark.parametrize("filling", [np.nan, -1])
def test_2d_crop_around_idxs(filling):
    tocrop_mat = np.arange(100).reshape((4, 25)).T

    cropped = crop_around_idxs(tocrop_mat, np.array([1, 25]), [-2, 1], out_of_range_fill=filling)
    assert cropped.shape == (3, 2, 4)
    assert np.allclose(cropped, np.array([[[filling, filling, filling, filling],
            [23, 48, 73, 98]],

        [[ 0, 25, 50, 75],
            [24, 49, 74, 99]],

        [[ 1, 26, 51, 76],
            [filling, filling, filling, filling]]]), equal_nan=True)