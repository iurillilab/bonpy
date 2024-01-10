import time
import pandas as pd
from pathlib import Path

# Path to your DeepLabCut H5 file
input_path = Path("/Users/vigji/Desktop/grid/M14/20231214/162720/")
input_file = input_path / "eye-cam_video_2023-12-14T16_27_20DLC_resnet50_eye-pupilDec16shuffle1_15000.h5"

output_path = Path("/Users/vigji/code/bonpy/tests/assets/dataset/M1/20231201/095001")
output_file = output_path / input_file.name

import flammkuchen as fl

data = fl.load(input_file)
print(data.keys())
# Load the DataFrame from the H5 file
df = pd.read_hdf(input_file)
# print(df.keys())
# Extract the first 500 lines
df_subset = df.iloc[:500]

print(df_subset.shape)
# Save the subset DataFrame back to an H5 file
df_subset.to_hdf(output_file, key="df_with_missing", mode="w")


timestamp_input_file = input_path / "eye-cam_timestamps_2023-12-14T16_27_20.csv"
timestamp_df = pd.read_csv(timestamp_input_file)
print(timestamp_df.tail())

# save first 500 to new file:
output_file = output_path / timestamp_input_file.name
timestamp_df.iloc[:500].to_csv(output_file, index=False)

# print header of new file:
print(pd.read_csv(output_file).tail())