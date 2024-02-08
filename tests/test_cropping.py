import numpy as np
import pandas as pd
import pytest

from bonpy.crop_utils import crop_around_idxs, smart_crop


@pytest.mark.parametrize("filling", [np.nan, -1])
def test_1d_crop_around_idxs(filling):
    crop = crop_around_idxs(
        np.arange(100), np.array([1, 20, 99]), [-2, 2], out_of_range_fill=filling
    )
    assert np.allclose(
        crop,
        np.array(
            [
                [filling, 18.0, 97.0],
                [0.0, 19.0, 98.0],
                [1.0, 20.0, 99.0],
                [2.0, 21.0, filling],
            ]
        ),
        equal_nan=True,
    )
    assert crop.dtype == type(filling)
    assert np.allclose(crop[0, 0], filling, equal_nan=True)


@pytest.mark.parametrize("filling", [np.nan, -1])
def test_2d_crop_around_idxs(filling):
    tocrop_mat = np.arange(100).reshape((4, 25)).T

    cropped = crop_around_idxs(
        tocrop_mat, np.array([1, 25]), [-2, 1], out_of_range_fill=filling
    )
    assert cropped.shape == (3, 2, 4)
    assert np.allclose(
        cropped,
        np.array(
            [
                [[filling, filling, filling, filling], [23, 48, 73, 98]],
                [[0, 25, 50, 75], [24, 49, 74, 99]],
                [[1, 26, 51, 76], [filling, filling, filling, filling]],
            ]
        ),
        equal_nan=True,
    )


dt = 0.01
x_arr = np.arange(0, 10, dt)
window = [-0.1, 0.1]
crop_events = np.array([0.05, 2, 5])
fill_value = np.nan
columns = ["test1", "test2"]
len_2nd_dim = len(columns)


def test_time_crop_df():
    test_df = pd.DataFrame(data=np.arange(len(x_arr)), columns=columns[:1], index=x_arr)
    timebase, crop_data = smart_crop(
        test_df, crop_events=crop_events, window=window, out_of_range_fill=fill_value
    )
    assert np.allclose(timebase, np.arange(*window, dt))
    assert crop_data[columns[0]].shape == (len(timebase), len(crop_events))

    result_idxs = (crop_events + window[0]) / dt
    result_idxs[result_idxs < 0] = fill_value
    assert np.allclose(crop_data[columns[0]][0, :], result_idxs, equal_nan=True)
    assert np.allclose(crop_data[columns[0]][-1, :], (crop_events + window[1]) / dt - 1)


@pytest.mark.parametrize(
    "out_of_range_drop, res_shape",
    [(True, len(crop_events) - 1), (False, len(crop_events))],
)
def test_time_crop_df_drop(out_of_range_drop, res_shape):
    test_df = pd.DataFrame(data=np.arange(len(x_arr)), columns=columns[:1], index=x_arr)
    timebase, crop_data = smart_crop(
        test_df,
        crop_events=crop_events,
        window=window,
        out_of_range_fill=fill_value,
        out_of_range_drop=out_of_range_drop,
    )
    assert np.allclose(timebase, np.arange(*window, dt))

    assert crop_data[columns[0]].shape == (len(timebase), res_shape)


def test_pandas_2d_data():
    test_2d_df = pd.DataFrame(
        data=np.arange(len(x_arr) * 2).reshape(-1, len_2nd_dim),
        columns=columns,
        index=x_arr,
    )

    timebase, cropped_data = smart_crop(
        test_2d_df, crop_events=crop_events, window=window
    )
    assert set(cropped_data.keys()) == set(columns)
    assert cropped_data[columns[0]].shape == (len(timebase), len(crop_events))


def test_numpy_2d_data():
    test_2d_arr = np.arange(len(x_arr) * 2).reshape(-1, len_2nd_dim)

    timebase, cropped_data = smart_crop(
        test_2d_arr, crop_events=crop_events, window=window, dt=dt
    )
    assert cropped_data.shape == (len(timebase), len(crop_events), len_2nd_dim)


def test_assertion_errors():
    test_df = pd.DataFrame(data=np.arange(len(x_arr)), columns=columns[:1], index=x_arr)

    with pytest.raises(AssertionError) as e:
        smart_crop(
            test_df.values,
            crop_events=crop_events,
            window=window,
        )
    assert "Either" in str(e.value)

    with pytest.raises(AssertionError) as e:
        smart_crop(
            test_df,
            crop_events=crop_events,
            window=window,
            dt=dt,
            time_arr=x_arr,
        )
    assert "Only one" in str(e.value)


@pytest.mark.parametrize("timeargs", (dict(dt=dt), dict(time_arr=x_arr)))
def test_time_arr_options(timeargs):
    test_2d_arr = np.arange(len(x_arr) * 2).reshape(-1, len_2nd_dim)

    timebase, _ = smart_crop(
        test_2d_arr, crop_events=crop_events, window=window, **timeargs
    )
    assert np.allclose(timebase, np.arange(*window, dt))


def test_jitter_issues():
    np.random.seed(42)
    test_df = pd.DataFrame(
        data=np.arange(len(x_arr)),
        columns=columns[:1],
        index=x_arr + np.random.rand(len(x_arr)) * dt / 2,
    )

    # Passing with very high jitter threshold:
    smart_crop(
        test_df,
        crop_events=crop_events,
        window=window,
        max_jitter_fraction=0.5,
    )

    # Failing with low jitter threshold:
    with pytest.raises(ValueError) as e:
        smart_crop(
            test_df,
            crop_events=crop_events,
            window=window,
            max_jitter_fraction=0.001,
        )

    assert "jitter" in str(e.value)
