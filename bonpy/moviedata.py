from abc import ABC, abstractmethod, abstractproperty
from functools import cached_property
import cv2
import numpy as np
from tqdm import tqdm


class MovieData(ABC):
    def __init__(self, source_filename) -> None:
        self.source_filename = str(source_filename)
        self.verbose = True

    #@abstractclassmethod
    #def load_indexed_frame(self):
    #    pass

    @abstractproperty
    def metadata(self):
        pass

    
class OpenCVMovieData(MovieData):
    def __init__(self, source_filename, verbose=True) -> None:
        super().__init__(source_filename)

        self.verbose = verbose

    @cached_property
    def metadata(self):
        cap = cv2.VideoCapture(self.source_filename)

        ret, frame = cap.read()

        metadata = dict(width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                        dtype=frame.dtype,
                        bw=np.allclose(frame[:, :, 0], frame[:, :, 1]) and np.allclose(frame[:, :, 0], frame[:, :, 2]),
                        n_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    
        cap.release()

        return metadata

    def __getitem__(self, idx):
        if isinstance(idx, tuple):
            # Extract individual indexes for frames, rows, and columns
            channel_idx = slice(None)
            if self.metadata["bw"]:
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

    def _retrieve_and_slice_frames(self, frame_idx, row_idx, col_idx, channel_idx=None):

        # Open the video file
        cap = cv2.VideoCapture(self.source_filename)

        # Test if frame index is iterable:
        try:
            iter(frame_idx)
            frame_idx = np.array(frame_idx)
            # If so, check if boolean or integer values, If boolean, test if length matches number of frames,
            # and generate array with integer valid values:
            assert frame_idx.dtype in [bool, int]

            if frame_idx.dtype == bool:
                if len(frame_idx) != self.length:
                    raise ValueError("Boolean frame index must have same length as number of frames.")
                frame_indices = np.where(frame_idx)[0]
            
            elif frame_idx.dtype == int:
                # check if values are valid
                if np.any(np.array(frame_idx) >= self.metadata["n_frames"]):
                    raise ValueError("Integer frame indices must be between 0 and number of frames.")
                # Convert negative indices to positive, conting from the end:
                frame_idx[frame_idx < 0] += self.metadata["n_frames"]
            
            frame_indices = frame_idx
        
        except TypeError:
            # Determine frame indices
            if isinstance(frame_idx, int):
                frame_indices = [frame_idx]
            elif isinstance(frame_idx, slice):
                frame_indices = range(*frame_idx.indices(self.metadata["n_frames"]))
            else:
                raise TypeError("Frame index must be an interable, an integer or a slice.")

        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Slice the frame immediately:
                if channel_idx is not None:
                    sliced_frame = frame[row_idx, col_idx, channel_idx]
                else:
                    sliced_frame = frame[row_idx, col_idx]
                if sliced_frame.ndim == 3 and self.metadata["bw"]:
                    sliced_frame = sliced_frame[:, :, 0]
                frames.append(sliced_frame)
            else:
                break

        cap.release()

        return np.array(frames)


    

if __name__ == "__main__":
    path = "/Users/vigji/Desktop/headfixed/M13/20231110/135615/eye-cam_video_2023-11-10T13_56_15.avi"

    m = OpenCVMovieData(path)
    print("getting meta")
    print(m.metadata)
    print("getting 2")
    print(m.metadata)
    print("done")

    print(m[[1,2,3]].shape)

    print(m[:10, 10:-20, 30:-30].shape)
