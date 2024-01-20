import pandas as pd
import numpy as np
from bonpy.time_utils import interpolate_df
import pytest


@pytest.mark.parametrize(
    "from_zero, expected_shape", [(True, (901, 1)), (False, (801, 1))]
)
def test_interpolate_df(from_zero, expected_shape):
    # Test case 1: Interpolate with default parameters
    input_df = pd.DataFrame(
        data=np.arange(1, 10, 1), columns=["time"], index=np.arange(1, 10, 1)
    )

    output_df = interpolate_df(input_df, new_timebin="10ms", from_zero=from_zero)
    print(output_df.shape)
    assert output_df.shape == expected_shape
