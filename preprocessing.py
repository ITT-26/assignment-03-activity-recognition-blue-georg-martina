# %%
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import seaborn as sns
import matplotlib.pyplot as plt
import random
import copy

# %%
# get all csv files in the data folder
data_folder = 'data'

all_csv_paths = []
for dirpath, dirnames, filenames in os.walk(data_folder):
    for filename in filenames:
        if filename.endswith('.csv'):
            all_csv_paths.append((os.path.join(dirpath, filename), filename))

# %%


def make_df_list(csv_paths, keyword):
    dfs = []
    for full_path, filename in csv_paths:
        if keyword in filename:
            df = pd.read_csv(full_path)

            if 'running' in filename:
                df['activity_label'] = 0

            elif 'rowing' in filename:
                df['activity_label'] = 1

            elif 'jumpingjacks' in filename:
                df['activity_label'] = 2

            elif 'lifting' in filename:
                df['activity_label'] = 3

            dfs.append(df)
    return dfs


dfs_20Hz_hand = make_df_list(all_csv_paths, '20Hz-hand')
dfs_20Hz_pocket = make_df_list(all_csv_paths, '20Hz-pocket')
dfs_100Hz_hand = make_df_list(all_csv_paths, '100Hz-hand')
dfs_100Hz_pocket = make_df_list(all_csv_paths, '100Hz-pocket')

all_df_lists = {
    '20Hz_hand': dfs_20Hz_hand,
    '20Hz_pocket': dfs_20Hz_pocket,
    '100Hz_hand': dfs_100Hz_hand,
    '100Hz_pocket': dfs_100Hz_pocket
}

# %%

print(len(dfs_20Hz_hand))
print(len(dfs_20Hz_pocket))
print(len(dfs_100Hz_hand))
print(len(dfs_100Hz_pocket))


# %%

# degree change / second -> radian change / second


def radian_or_degree(df):
    for col in df.columns:
        if 'gyro' in col:
            if df[col].abs().max() > 100:
                return 'degree'
    return 'radian'


def degree_to_radian(df):
    for col in df.columns:
        if 'gyro' in col:
            df[col] = np.deg2rad(df[col])
    return df


for dfs in all_df_lists.values():
    for df in dfs:
        if radian_or_degree(df) == 'degree':
            df = degree_to_radian(df)


# %%

for df in dfs_20Hz_hand:
    if radian_or_degree(df) == 'degree':
        print('still degree')

print('everything checked')

# %%

for key, dfs in all_df_lists.items():
    for i, df in enumerate(dfs):
        dfs[i] = df.dropna().reset_index(drop=True)

# %%

scaler = StandardScaler()

scaled_dfs_20Hz_hand = []
scaled_dfs_20Hz_pocket = []
scaled_dfs_100Hz_hand = []
scaled_dfs_100Hz_pocket = []

all_scaled_df_lists = {
    '20Hz_hand': scaled_dfs_20Hz_hand,
    '20Hz_pocket': scaled_dfs_20Hz_pocket,
    '100Hz_hand': scaled_dfs_100Hz_hand,
    '100Hz_pocket': scaled_dfs_100Hz_pocket
}

cols_to_scale = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']

for key, dfs in all_df_lists.items():
    for df in dfs:
        scaler.fit(df[cols_to_scale])
        scaled_tmp = scaler.transform(df[cols_to_scale])
        scaled_df = df.copy()
        scaled_df[cols_to_scale] = scaled_tmp
        all_scaled_df_lists[key].append(scaled_df)


# %%
random_key = random.choice(list(all_df_lists.keys()))
random_idx = random.randrange(len(all_df_lists[random_key]))

df_original = all_df_lists[random_key][random_idx]
df_scaled = all_scaled_df_lists[random_key][random_idx]

sns.set_style("whitegrid")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Plot Original Data
ax1.plot(df_original['timestamp'], df_original['acc_x'],
         color='#1f77b4', linewidth=1)
ax1.set_title(
    f'Original acc_x | Category: {random_key} | Index: {random_idx}', fontsize=14)
ax1.set_ylabel('Raw Acceleration')

# Plot Scaled Data
ax2.plot(df_scaled['timestamp'], df_scaled['acc_x'],
         color='#ff7f0e', linewidth=1)
ax2.set_title(f'Scaled acc_x (StandardScaler)', fontsize=14)
ax2.set_ylabel('Z-Score (Standardized)')
ax2.set_xlabel('Timestamp')

plt.tight_layout()
plt.show()

# %%

ts_normalized_20Hz_hand = []
ts_normalized_20Hz_pocket = []
ts_normalized_100Hz_hand = []
ts_normalized_100Hz_pocket = []

all_timestamp_normaized_dfs = {
    '20Hz_hand': ts_normalized_20Hz_hand,
    '20Hz_pocket': ts_normalized_20Hz_pocket,
    '100Hz_hand': ts_normalized_100Hz_hand,
    '100Hz_pocket': ts_normalized_100Hz_pocket
}

for key, dfs in all_df_lists.items():
    for df in dfs:
        min_timestamp = df['timestamp'].min()
        df_tmp = df.copy()
        df_tmp['timestamp'] = (df_tmp['timestamp'] - min_timestamp)
        all_timestamp_normaized_dfs[key].append(df_tmp)

# %%

scaler = MinMaxScaler()

normalized_dfs_20Hz_hand = []
normalized_dfs_20Hz_pocket = []
normalized_dfs_100Hz_hand = []
normalized_dfs_100Hz_pocket = []

all_normalized_df_lists = {
    '20Hz_hand': normalized_dfs_20Hz_hand,
    '20Hz_pocket': normalized_dfs_20Hz_pocket,
    '100Hz_hand': normalized_dfs_100Hz_hand,
    '100Hz_pocket': normalized_dfs_100Hz_pocket
}

cols_to_scale = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']

for key, dfs in all_timestamp_normaized_dfs.items():
    for df in dfs:
        scaler.fit(df[cols_to_scale])
        normalized_tmp = scaler.transform(df[cols_to_scale])
        normalized_df = df.copy()
        normalized_df[cols_to_scale] = normalized_tmp
        all_normalized_df_lists[key].append(normalized_df)


# %%

def get_median_amplitude(df, col):
    return df[col].median()


def get_std(df, col):
    return df[col].std()


def get_dominant_frequency(df, col, sampling_rate):
    n = len(df)
    freqs = np.fft.rfftfreq(n, d=1/sampling_rate)
    fft_magnitude = np.abs(np.fft.rfft(df[col]))

    dominant_freq = freqs[1:][np.argmax(fft_magnitude[1:])]
    return dominant_freq

# %%


def append_values_to_dict(dict, activity_label, col_features):
    dict['activity_label'].append(activity_label)
    for feature_name, feature_value in col_features.items():
        dict[feature_name].append(feature_value)


dict_template = {'activity_label': [],
                 'acc_x_median': [], 'acc_x_std': [], 'acc_x_dominant_freq': [],
                 'acc_y_median': [], 'acc_y_std': [], 'acc_y_dominant_freq': [],
                 'acc_z_median': [], 'acc_z_std': [], 'acc_z_dominant_freq': [],
                 'gyro_x_median': [], 'gyro_x_std': [], 'gyro_x_dominant_freq': [],
                 'gyro_y_median': [], 'gyro_y_std': [], 'gyro_y_dominant_freq': [],
                 'gyro_z_median': [], 'gyro_z_std': [], 'gyro_z_dominant_freq': []}

features_20Hz_hand_dict = copy.deepcopy(dict_template)
features_20Hz_pocket_dict = copy.deepcopy(dict_template)
features_100Hz_hand_dict = copy.deepcopy(dict_template)
features_100Hz_pocket_dict = copy.deepcopy(dict_template)

cols_to_evaluate = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']

for key, dfs in all_normalized_df_lists.items():

    for df in dfs:

        activity = df['activity_label'].iloc[0]

        sampling_rate = None
        if '20Hz' in key:
            sampling_rate = 20
        elif '100Hz' in key:
            sampling_rate = 100

        col_features = {}

        for col in cols_to_evaluate:
            median_amplitude = get_median_amplitude(df, col)
            std = get_std(df, col)
            dominant_freq = get_dominant_frequency(df, col, sampling_rate)

            col_features[f'{col}_median'] = median_amplitude
            col_features[f'{col}_std'] = std
            col_features[f'{col}_dominant_freq'] = dominant_freq

        match key:
            case '20Hz_hand':
                append_values_to_dict(
                    features_20Hz_hand_dict, activity, col_features)

            case '20Hz_pocket':
                append_values_to_dict(
                    features_20Hz_pocket_dict, activity, col_features)

            case '100Hz_hand':
                append_values_to_dict(
                    features_100Hz_hand_dict, activity, col_features)

            case '100Hz_pocket':
                append_values_to_dict(
                    features_100Hz_pocket_dict, activity, col_features)



    # %%

    # change file names (jumping_jacks -> jumpingjacks, name problems)

    # go through all the csv files in the data folder
    # convert into dataframes. maybe add columns for frequency, placement and activity label (int)

    # outlier detection and handling? <<===

    # pre-processing: standard and minmax normalization, [low-pass filter (maybe it would make sense only for 100 Hz)], NaN handling (for each axis in accel and gyro)

    # treat different sampling frequencies separately, and also placement separately
    #       - frequency: we can then choose only one for the final model
    #       - placement: maybe have two models in the end, and ask user to choose placement before starting the activity recognition to use the correct model

    # X

    # feature extraction - for each axis in accel an gyro, extract:
    #       - max amplitude -> doesn't make much sense since it's normalized -> but normalization makes sense because of height differences between users
    #       - mean amplitude -> without outliers
    #       - median amplitude -> with outliers
    #       - standard deviation or variance
    #       - dominant frequency (using FFT)
    #       - if we need more features, we can try: spectral energy
    # in total: 6 axes (accel x,y,z and gyro x,y,z) * 3 features = 18 features per sample
    # create new data frames with the extracted features and the activity labels / different frequency and placement groups
    # columns: ['activity_label', 'acc_x_median', 'acc_x_std', 'acc_x_dominant_freq', 'acc_y_median', 'acc_y_std', ...]

    # plot the features for each activity label to see if there are any patterns or differences between the activities

    # choose the most relevant features
    #       - we could run the models with different combinations of n features and see which ones give the best results
    #       - PCA?

    # split the data into training and testing sets
    # try different split ratios, kernels, etc.

    # evaluate the models using appropriate metrics (accuracy, precision, recall, F1-score)
    # choose best model

    # create application for real-time activity recognition using the best model & using pyglet

    # DOCUMENT EVERYTHING !!!
