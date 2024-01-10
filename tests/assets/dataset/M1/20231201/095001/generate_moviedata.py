import pandas as pd
from pathlib import Path

# Path to your DeepLabCut H5 file
input_file = Path('/Users/vigji/Desktop/grid/M14/20231214/162720/eye-cam_video_2023-12-14T16_27_20DLC_resnet50_eye-pupilDec16shuffle1_15000.h5')
output_file = Path("/Users/vigji/code/bonpy/tests/assets/dataset/M1/20231201/095001") / input_file.name

import flammkuchen  as fl
data = fl.load(input_file)
print(data.keys())
# Load the DataFrame from the H5 file
df = pd.read_hdf(input_file)
#print(df.keys())
# Extract the first 500 lines
df_subset = df.iloc[:500]

print(df_subset.shape)
# Save the subset DataFrame back to an H5 file
df_subset.to_hdf(output_file, key='df_with_missing', mode='w')