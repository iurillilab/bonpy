import numpy as np
import pandas as pd


def crop_around_idxs(trace, idxs, window, out_of_range_fill=np.nan):
    window_idxs = np.arange(window[0], window[1], dtype=int)
    idxs_mat = idxs + window_idxs[:, np.newaxis]
    idxs_mat[idxs_mat >= len(trace)] = -1  # set to negative for filling in next step

    cropped = trace[idxs_mat]

    # if filling with eg nan, first convert to float:
    if cropped.dtype is not type(out_of_range_fill):
        cropped = cropped.astype(type(out_of_range_fill))

    cropped[idxs_mat < 0] = out_of_range_fill

    return cropped


def crop_around_times(trace, times, window, fs):
    idxs = (times * fs).astype(int)
    window = (np.array(window) * fs).astype(int)

    return crop_around_idxs(trace, idxs, window)


def smart_crop(
    data,
    crop_events,
    window,
    dt=None,
    time_arr=None,
    out_of_range_fill=np.nan,
    out_of_range_drop=False,
    max_jitter_fraction=0.1,
):
    """Crop data around times, using a window.

    Parameters
    ----------
    data : np.ndarray or pd.Series or pd.DataFrame
        Data to crop, can be 1D or 2D. If 2D, the first dimension is assumed to be time.
    window : tuple
        Window to crop around, in seconds
    out_of_range_fill : bool or int or float, optional
        Value filling parts of the matrix that are out of range, by default np.nan.
    out_of_range_drop : bool, optional
        Whether to drop events that are too close to the edges, by default False.
    max_jitter_fraction : float, optional
        Maximum temporal jitter fraction allowed, by default 0.1

    Returns
    -------
    timebase : np.ndarray
        Timebase of the cropped data
    cropped_data : np.ndarray
        Cropped data
    """
    assert not (
        dt is not None and time_arr is not None
    ), "Only one of dt and time_arr can be provided"

    columns = None
    if type(data) in [pd.Series, pd.DataFrame]:
        # Use index of the dataframe if no time info is provided:
        if time_arr is None and dt is None:
            time_arr = data.index.values

        if type(data) == pd.DataFrame:
            columns = data.columns
    else:
        assert (
            dt is not None or time_arr is not None
        ), "Either dt or time_arr must be provided if data is numpy array"

    data = np.array(data)

    # If we just provided dt and there is no index to be used:
    if time_arr is None and dt is not None:
        time_arr = np.arange(data.shape[0]) * dt

    crop_events = np.array(crop_events)
    assert crop_events.ndim == 1, "crop_events must be 1D"
    searchsorted = np.searchsorted(time_arr, crop_events)
    # for each searchsorted idx, the closest time could be either the one before or after.
    # Figure out which one is closer:
    # TODO: this might be configurable
    before = np.abs(time_arr[searchsorted - 1] - crop_events)
    after = np.abs(time_arr[searchsorted] - crop_events)
    closest_idxs = np.where(before < after, searchsorted - 1, searchsorted)

    if dt is None:
        timedelta = np.diff(time_arr)
        dt = np.mean(timedelta)

    # Convert window to points:
    window_pts = np.round(np.array(window) / dt).astype(int)

    # Find all time intervals and estimate jitter between trials:
    start_idxs = closest_idxs + window_pts[0]
    end_idxs = closest_idxs + window_pts[1]

    inrange_selection = (start_idxs >= 0) & (end_idxs < len(time_arr))
    all_durations = (
        time_arr[end_idxs[inrange_selection]] - time_arr[start_idxs[inrange_selection]]
    )
    variation_coef = np.std(all_durations) / np.mean(all_durations)

    if variation_coef > max_jitter_fraction:
        raise ValueError(
            f"Warning: jitter of {variation_coef} > 0.1, you should resample the raw data"
        )

    # If we want to ignore events too close to the edges:
    if out_of_range_drop:
        closest_idxs = closest_idxs[inrange_selection]

    timebase = np.arange(window_pts[0], window_pts[1]) * dt
    cropped_data = crop_around_idxs(
        data, closest_idxs, window_pts, out_of_range_fill=out_of_range_fill
    )

    if columns is not None:
        cropped_data = {key: cropped_data[..., i] for i, key in enumerate(columns)}

    return timebase, cropped_data
