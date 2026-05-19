import time
from DIPPID import SensorUDP
import os
import joblib
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import pandas as pd
import numpy as np

from collections import deque

PORT = 5700
sensor = SensorUDP(PORT)

models = {}
for key in ['20Hz_hand', '20Hz_pocket', '100Hz_hand', '100Hz_pocket']:
    model_filename = f'models/{key}_svm_model.joblib'
    models[key] = joblib.load(model_filename)

freqs = [20, 100]
placements = ['hand', 'pocket']
freq = None
placement = None

now = None
next_window_start = None
last_time = 0

working_out = False


window_size_seconds = 2

WINDOW_SIZE_20HZ = window_size_seconds * 20
WINDOW_SIZE_100HZ = window_size_seconds * 100
OVERLAP = 0.5


current_acc_data = None
current_gyro_data = None

dict_tmp = {"id": [], "timestamp": [], "gyro": [], "acc": []}
current_features = None
features_list = []
MAX_LEN_FEATURES_LIST = 5

scaler = StandardScaler()

prediction_history = []
MAX_HISTORY_LENGTH = 5


# mapping of model output to activity name
workouts = {
    0: "running",
    1: "rowing",
    2: "jumpingjacks",
    3: "lifting",
    None: "unknown"
}


def extract_features():
    global dict_tmp

    cols_to_evaluate = ['acc_x', 'acc_y', 'acc_z', 'gyro_x',
                        'gyro_y', 'gyro_z', 'acc_magnitude', 'gyro_magnitude']

    acc_x = [d["x"] for d in dict_tmp["acc"]]
    acc_y = [d["y"] for d in dict_tmp["acc"]]
    acc_z = [d["z"] for d in dict_tmp["acc"]]
    gyro_x = [d["x"] for d in dict_tmp["gyro"]]
    gyro_y = [d["y"] for d in dict_tmp["gyro"]]
    gyro_z = [d["z"] for d in dict_tmp["gyro"]]

    df_tmp = pd.DataFrame({
        "acc_x": acc_x,
        "acc_y": acc_y,
        "acc_z": acc_z,
        "gyro_x": gyro_x,
        "gyro_y": gyro_y,
        "gyro_z": gyro_z
    })

    window_features = df_tmp.copy()

    window_features['acc_magnitude'] = np.sqrt(
        window_features['acc_x']**2 +
        window_features['acc_y']**2 + window_features['acc_z']**2
    )
    window_features['gyro_magnitude'] = np.sqrt(
        window_features['gyro_x']**2 +
        window_features['gyro_y']**2 + window_features['gyro_z']**2
    )

    feature_list = {}
    for col in cols_to_evaluate:
        feature_list[f'{col}_max'] = window_features[col].max()
        feature_list[f'{col}_median'] = window_features[col].median()
        feature_list[f'{col}_std'] = window_features[col].std()
        feature_list[f'{col}_dominant_freq'] = get_dominant_frequency(
            window_features[col], freq)

    feature_list['acc_x_y_corr'] = get_correlation(
        window_features, 'acc_x', 'acc_y')
    feature_list['acc_x_z_corr'] = get_correlation(
        window_features, 'acc_x', 'acc_z')
    feature_list['acc_y_z_corr'] = get_correlation(
        window_features, 'acc_y', 'acc_z')
    feature_list['gyro_x_y_corr'] = get_correlation(
        window_features, 'gyro_x', 'gyro_y')
    feature_list['gyro_x_z_corr'] = get_correlation(
        window_features, 'gyro_x', 'gyro_z')
    feature_list['gyro_y_z_corr'] = get_correlation(
        window_features, 'gyro_y', 'gyro_z')

    feature_list_df = pd.DataFrame([feature_list])
    return feature_list_df


def classify_activity(features_df_line):
    global models, placement, freq

    model_key = f"{freq}Hz_{placement}"
    model = models.get(model_key)
    if model is not None:

        prediction = model.predict(features_df_line)
        predictions = model.predict_proba(features_df_line)
        # print rounded prediction probabilities for each class
        print(np.round(predictions, 2))

        # print the predicted activity
        prediction_history.append(prediction[0])
        if len(prediction_history) > MAX_HISTORY_LENGTH:
            prediction_history.pop(0)


def get_majority_prediction():
    global prediction_history
    if len(prediction_history) < MAX_HISTORY_LENGTH:
        return None

    # get the most common prediction in the history and return it if it appears over 50% of the time
    majority_prediction = max(set(prediction_history),
                              key=prediction_history.count)
    if prediction_history.count(majority_prediction) > MAX_HISTORY_LENGTH / 2:
        return majority_prediction

    return None


# function to calculate the dominant frequency of a series using FFT
def get_dominant_frequency(series, sampling_rate):
    n = len(series)
    freqs = np.fft.rfftfreq(n, d=1/sampling_rate)
    fft_magnitude = np.abs(np.fft.rfft(series))
    return freqs[1:][np.argmax(fft_magnitude[1:])]


# function to calculate the correlation between two columns in a window, returning 0 if the correlation is NaN
def get_correlation(window, col1, col2):
    corr = window[col1].corr(window[col2])
    return corr if not np.isnan(corr) else 0.0


def handle_button_1(data):
    global now, next_window_start, freq, working_out

    if data == 0 or working_out:
        return

    now = time.time()
    next_window_start = now + window_size_seconds
    working_out = True


def handle_button_2(data):

    # resets data
    global dict_tmp, current_features, features_list, working_out, last_time, next_window_start, prediction_history

    if data == 0 or not working_out:
        return
    

    working_out = False
    dict_tmp = {"id": [], "timestamp": [], "gyro": [], "acc": []}
    current_features = None
    features_list = []
    last_time = 0
    next_window_start = 0
    prediction_history.clear()


def acc_callback(data):
    global current_acc_data
    current_acc_data = data


def gyro_callback(data):
    global current_gyro_data
    current_gyro_data = data


sensor.register_callback("button_1", handle_button_1)
sensor.register_callback("button_2", handle_button_2)
sensor.register_callback('accelerometer', acc_callback)
sensor.register_callback('gyroscope', gyro_callback)

# select frequency
while freq not in freqs:
    chosen_freq = input("Press 1 for 20Hz, 2 for 100Hz: ")
    if chosen_freq == "1":
        freq = 20
    elif chosen_freq == "2":
        freq = 100
    else:
        print("Invalid input, please try again")

# select placement
while placement not in placements:
    chosen_placement = input("Press 1 for hand, 2 for pocket: ")
    if chosen_placement == "1":
        placement = "hand"
    elif chosen_placement == "2":
        placement = "pocket"
    else:
        print("Invalid input, please try again")


# workout loop
while True:

    # there is no workout in progress
    if not working_out:
        time.sleep(0.001)
        continue

    # workout in progress
    else:

        # time for measurement
        if time.time() - last_time >= 1/freq or last_time == 0:
            dict_tmp["id"].append(0)
            dict_tmp["timestamp"].append(time.time())
            dict_tmp["acc"].append(current_acc_data)
            dict_tmp["gyro"].append(current_gyro_data)

            if len(dict_tmp["id"]) > (WINDOW_SIZE_100HZ if freq == 100 else WINDOW_SIZE_20HZ):
                dict_tmp["id"].pop(0)
                dict_tmp["timestamp"].pop(0)
                dict_tmp["acc"].pop(0)
                dict_tmp["gyro"].pop(0)

            last_time = time.time()

        # window complete
        if time.time() >= next_window_start:
            if not working_out:
                continue
            features_line = extract_features()
            # print("Feature columns:", features_line.columns.tolist())
            # print("Feature shape:", features_line.shape)
            # print("Sample values:", features_line.values)
            features_list.append(features_line)
            classify_activity(features_line)
            majority_prediction = get_majority_prediction()
            next_window_start = time.time() + window_size_seconds * (1 - OVERLAP)
            # print the majority prediction
            print(f"Predicted activity: {workouts[majority_prediction]}")
