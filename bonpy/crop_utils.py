import numpy as np


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