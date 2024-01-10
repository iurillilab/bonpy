from abc import ABC, abstractmethod, abstractproperty
from functools import cached_property
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

import cv2
import numpy as np
from tqdm import tqdm

from bonpy.time_utils import inplace_time_cols_fix

@dataclass
class MovieMetadata:
    width: int
    height: int
    n_frames: int
    dtype: np.dtype
    bw: bool


class MovieData(ABC):
    """Interface for movie data. Subclasses can implement different readers backends,
    the class offer a numpy-like interface for accessing frames.

    Args:
        source_filename (str): Path to the movie file.

    Properties:
        metadata (MovieMetadata): Metadata of the movie.
        dtype (np.dtype): Data type of the movie.
        n_dims (int): Number of dimensions of the movie.
        is_bw (bool): Whether the movie is black and white.
        shape (tuple): Shape of the movie.

    Methods:
        __getitem__(idx): Returns a slice of the movie.

    """

    def __init__(self, source_filename, timestamp_begin=None) -> None:
        source_filename = Path(source_filename)
        
        assert source_filename.exists()

        # Check if a timestamp file is present.
        # The convention is that timestamp file is named the same as the movie file,
        # with timestamp instead of movie and .csv extension
        self.timestamp_filename = source_filename.parent / source_filename.name.replace("video", "timestamps")
        
        # Check if there is a DLC file available:
        # try:
        #     self.dlc_filename = next(source_filename.parent.glob(f"{source_filename.name}*DLC*.h5"))
        # except StopIteration:
        #     self.dlc_filename = None

        self.source_filename = source_filename
        self.timestamp_begin = timestamp_begin
        self.verbose = True

    # @abstractclassmethod
    # def load_indexed_frame(self):
    #    pass

    @abstractproperty
    def metadata(self) -> MovieMetadata:
        pass

    @property
    def has_timestamps(self) -> bool:
        return self.timestamp_filename.exists()
    
    @property
    def has_dlc(self) -> bool:
        return self.dlc_filename.exists()
    
    @cached_property
    def timestamps(self) -> np.ndarray:
        if self.has_timestamps:
            timestamps_df = pd.read_csv(self.timestamp_filename)
            inplace_time_cols_fix(timestamps_df, timestamp_begin=self.timestamp_begin)

            return timestamps_df
        else:
            return None

    @property
    def dtype(self) -> np.dtype:
        return self.metadata.dtype

    @property
    def n_dims(self) -> int:
        return len(self.shape)

    @property
    def is_bw(self) -> bool:
        return self.metadata.bw

    @property
    def shape(self) -> tuple:
        shape = (
            self.metadata.n_frames,
            self.metadata.height,
            self.metadata.width,
        )

        if not self.is_bw:
            shape += (3,)

        return shape

    def __getitem__(self, idx):
        if isinstance(idx, tuple):
            # Extract individual indexes for frames, rows, and columns
            channel_idx = slice(None)
            if self.is_bw:
                assert len(idx) == 3
                frame_idx, row_idx, col_idx = idx
            else:
                assert len(idx) in [3, 4]

                if len(idx) == 3:
                    frame_idx, row_idx, col_idx = idx
                else:
                    frame_idx, row_idx, col_idx, channel_idx = idx
        else:
            # If only one index is provided, it's for the frames
            frame_idx = idx
            row_idx = slice(None)  # All rows
            col_idx = slice(None)  # All columns
            channel_idx = slice(None)  # All channels

        # Retrieve and slice frames
        return self._retrieve_and_slice_frames(frame_idx, row_idx, col_idx, channel_idx)

    @abstractmethod
    def _retrieve_and_slice_frames(self, frame_idx, row_idx, col_idx, channel_idx):
        pass


class OpenCVMovieData(MovieData):
    """Movie data class using OpenCV as backend."""

    VERBOSE_DEFAULT_NFRAMES = 400  # Number of frames above which to show progress bar
    BW_DEFAULT_ATOL = (
        10  # Absolute tolerance of similarity across channels for BW detection
    )

    def __init__(self, source_filename, verbose=True) -> None:
        super().__init__(source_filename)

        self.verbose = verbose

    @cached_property
    def metadata(self):
        # We need to read frames independently from _retrieve_and_slice_frames to
        # avoid circularity and read the metadata:
        cap = cv2.VideoCapture(str(self.source_filename))
        ret, frame = cap.read()

        # bw if all frames very similar across channels:
        bw = np.allclose(
            frame[:, :, 0], frame[:, :, 1], atol=self.BW_DEFAULT_ATOL
        ) and np.allclose(frame[:, :, 0], frame[:, :, 2], atol=self.BW_DEFAULT_ATOL)

        metadata = MovieMetadata(
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            dtype=frame.dtype,
            bw=bw,
            n_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        )

        cap.release()

        return metadata

    def _retrieve_and_slice_frames(self, frame_idx, row_idx, col_idx, channel_idx=None):
        # On my machine, a single frame of size (634, 548) takes approx. 0.015 seconds to retrieve;
        # 100 frames take approx. 0.25 seconds to retrieve (2.3 ms/frame + 15 ms overhead).

        # Open the video file
        cap = cv2.VideoCapture(str(self.source_filename))
        squeeze_n_frames = False
        # Test if frame index is iterable:
        try:
            iter(frame_idx)
            is_iterable = True
        except TypeError:
            is_iterable = False

        if is_iterable:
            frame_idx = np.array(frame_idx)
            # If so, check if boolean or integer values, If boolean, test if length matches number of frames,
            # and generate array with integer valid values:
            # print(frame_idx, frame_idx.dtype)
            assert frame_idx.dtype in [bool, int, np.int32, np.int64]

            if frame_idx.dtype == bool:
                if len(frame_idx) != self.length:
                    raise ValueError(
                        "Boolean frame index must have same length as number of frames."
                    )
                frame_indices = np.where(frame_idx)[0]

            elif frame_idx.dtype == int:
                # check if values are valid
                if np.any(np.array(frame_idx) >= self.metadata.n_frames):
                    raise ValueError(
                        "Integer frame indices must be between 0 and number of frames."
                    )
                # Convert negative indices to positive, conting from the end:
                frame_idx[frame_idx < 0] += self.metadata.n_frames

            frame_indices = frame_idx

        else:
            # Determine frame indices
            if (
                isinstance(frame_idx, int)
                or isinstance(frame_idx, np.int32)
                or isinstance(frame_idx, np.int64)
            ):
                frame_indices = [frame_idx]
                squeeze_n_frames = True
            elif isinstance(frame_idx, slice):
                frame_indices = range(*frame_idx.indices(self.metadata.n_frames))

            else:
                raise TypeError(
                    "Frame index must be an interable, an integer or a slice."
                )

        # Compute the size of the retrieved frames:
        new_frames = len(frame_indices)
        new_height = len(range(*row_idx.indices(self.metadata.height)))
        new_width = len(range(*col_idx.indices(self.metadata.width)))
        new_channels = (
            len(range(*channel_idx.indices(3))) if channel_idx is not None else None
        )

        output_data_shape = (new_frames, new_height, new_width)
        if not self.is_bw:
            output_data_shape += (new_channels,)

        frames_data = np.zeros(output_data_shape, dtype=self.dtype)

        # Show bar only if verbose and more than VERBOSE_DEFAULT_NFRAMES frames:
        wrapper = (
            tqdm
            if self.verbose and new_frames > self.VERBOSE_DEFAULT_NFRAMES
            else lambda x: x
        )

        for n_idx, idx in enumerate(wrapper(frame_indices)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Slice the frame immediately:
                if channel_idx is not None:
                    sliced_frame = frame[row_idx, col_idx, channel_idx]
                else:
                    sliced_frame = frame[row_idx, col_idx]
                if sliced_frame.ndim == 3 and self.is_bw:
                    sliced_frame = sliced_frame[:, :, 0]
                frames_data[n_idx, ...] = sliced_frame
            else:
                break

        cap.release()

        if squeeze_n_frames:
            frames_data = np.squeeze(frames_data, axis=0)

        return frames_data


class DLCTrackedMovieData:
    pass


if __name__ == "__main__":
    path = "/Users/vigji/Desktop/headfixed/M13/20231110/135615/top-cam_video_2023-11-10T13_56_15.avi"

    m = OpenCVMovieData(path)
    print("getting meta")
    print(m.metadata)
    print("getting 2")
    print(m.metadata)
    print("done")

    print(m[[1, 2, 3]].shape)

    print(m[:10, 10:-20, 30:-30].shape)

    # time single frame retrieval on 100 test frames:
    # import napari

    # v = napari.Viewer()
    # v.add_image(m, name="test", contrast_limits=(0, 255), multiscale=False)
    # napari.run()
