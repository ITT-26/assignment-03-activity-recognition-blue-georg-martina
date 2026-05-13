# %%
import pandas as pd
import numpy as np
import os

# %%
# get all csv files in the data folder
data_folder = 'data'
csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]

# %%

def make_df_list(csv_files, keyword):
    dfs = []
    for csv_file in csv_files:
        if keyword in csv_file:
            df = pd.read_csv(os.path.join(data_folder, csv_file))
            dfs.append(df)
    return dfs

dfs_20Hz_hand = make_df_list(csv_files, '20Hz-hand')
dfs_20Hz_pocket = make_df_list(csv_files, '20Hz-pocket')
dfs_100Hz_hand = make_df_list(csv_files, '100Hz-hand')
dfs_100Hz_pocket = make_df_list(csv_files, '100Hz-pocket')

# %%

# ((DONE)) change file names 

# go through all the csv files in the data folder
# convert into dataframes. maybe add columns for frequency, placement and activity label (int)

# pre-processing: standard and minmax normalization, [low-pass filter (maybe it would make sense only for 100 Hz)], NaN handling (for each axis in accel and gyro)

# treat different sampling frequencies separately, and also placement separately
#       - frequency: we can then choose only one for the final model
#       - placement: maybe have two models in the end, and ask user to choose placement before starting the activity recognition to use the correct model

# feature extraction - for each axis in accel an gyro, extract:
#       - max amplitude
#       - mean amplitude
#       - standard deviation or variance
#       - dominant frequency (using FFT)
# in total: 6 axes (accel x,y,z and gyro x,y,z) * 4 features = 24 features per sample
# create new data frames with the extracted features and the activity labels / different frequency and placement groups
# columns: ['freq', 'placement', 'activity_label', 'max_accel_x', 'mean_accel_x', 'std_accel_x', 'dom_freq_accel_x', 'max_accel_y', 'mean_accel_y', 'std_accel_y', 'dom_freq_accel_y', 'max_accel_z', 'mean_accel_z', 'std_accel_z', 'dom_freq_accel_z', 'max_gyro_x', 'mean_gyro_x', 'std_gyro_x', 'dom_freq_gyro_x', 'max_gyro_y', 'mean_gyro_y', 'std_gyro_y', 'dom_freq_gyro_y', 'max_gyro_z', 'mean_gyro_z', 'std_gyro_z', 'dom_freq_gyro_z']

# plot the features for each activity label to see if there are any patterns or differences between the activities
# choose the most relevant features
#       - we could run the models with different combinations of n features and see which ones give the best results
#       - PCA?

# split the data into training and testing sets
# try different split ratios, kernels, etc.

# evaluate the models using appropriate metrics (accuracy, precision, recall, F1-score)
# choose best model

# create application for real-time activity recognition using the best model using pyglet

# DOCUMENT EVERYTHING !!!


