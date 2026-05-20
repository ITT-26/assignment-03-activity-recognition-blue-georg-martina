# this program recognizes activities
import numpy as np
from constants import *
from collections import deque
import pandas as pd
import joblib
from model_trainer import ModelTrainer


class ActivityRecognizer:

    # initialization
    def __init__(self, frequency, placement):
        # frequency and placement for model selection and thresholds
        self.frequency = frequency
        self.placement = placement

        # classifier threshold for the selected frequency and placement
        self.classifier_threshold = CLASSIFIER_THRESHOLDS[f"{frequency}Hz_{placement}"]

        # buffer for current window data and prediction history for majority voting
        buffer_len = WINDOW_SIZE_100HZ if frequency == 100 else WINDOW_SIZE_20HZ

        # dictionary of raw data with max length
        self.dict_tmp = {
            "acc": deque(maxlen=buffer_len),
            "gyro": deque(maxlen=buffer_len),
        }

        # prediction history for majority voting
        self.prediction_history = []

        # better Version: loads models from notebook
        # # loads the models for all combinations
        # self.models = {}
        # for key in ['20Hz_hand', '20Hz_pocket', '100Hz_hand', '100Hz_pocket']:
        #     model_filename = f'models/{key}_svm_model.joblib'
        #     self.models[key] = joblib.load(model_filename)

        # slower version but wanted in the assignment -> train model before application starts
        self.model_trainer = ModelTrainer()
        self.models = self.model_trainer.train_models()

    # change configuration -> update frequency, placement, thresholds and reset buffers and history
    def change_configuration(self, frequency, placement):
        self.frequency = frequency
        self.placement = placement
        self.classifier_threshold = CLASSIFIER_THRESHOLDS[f"{frequency}Hz_{placement}"]

        buffer_len = WINDOW_SIZE_100HZ if frequency == 100 else WINDOW_SIZE_20HZ
        self.dict_tmp = {
            "acc": deque(maxlen=buffer_len),
            "gyro": deque(maxlen=buffer_len),
        }
        self.prediction_history.clear()

    # the function thats called from the outside -> returns the classified activity
    def return_classification(self):
        features = self.extract_features()
        self.classify_activity(features)
        majority = self.get_majority_prediction()
        return WORKOUTS[majority]

    # classify activity based on a single data point
    def classify_activity(self, features_line):
        # select model based on frequency and placement
        model_key = f"{self.frequency}Hz_{self.placement}"
        model = self.models.get(model_key)
        if model is not None:
            # get probabilities and prediction from model
            proba = model.predict_proba(features_line)[0]
            p_max = float(proba.max())
            prediction = model.predict(features_line)[0]

            # if the max probability is above the threshold -> add to prediction history
            if p_max >= self.classifier_threshold:
                self.prediction_history.append(prediction)
                if len(self.prediction_history) > MAX_HISTORY_LENGTH:
                    self.prediction_history.pop(0)

            else:
                self.prediction_history.append(None)
                if len(self.prediction_history) > MAX_HISTORY_LENGTH:
                    self.prediction_history.pop(0)

    # get the majority prediction from the history
    def get_majority_prediction(self):
        if len(self.prediction_history) < MAX_HISTORY_LENGTH:
            return None

        # get the most common prediction in the history and return it if it appears over 50% of the time
        majority_prediction = max(set(self.prediction_history),
                                  key=self.prediction_history.count)
        if self.prediction_history.count(majority_prediction) > MAX_HISTORY_LENGTH * MAJORITY_THRESHOLD:
            return majority_prediction

        return None

    # extract features from the current window data (similar to notebook)
    def extract_features(self):

        cols_to_evaluate = [
            "acc_x", "acc_y", "acc_z",
            "gyro_x", "gyro_y", "gyro_z",
            "acc_magnitude", "gyro_magnitude"
        ]

        acc_x = np.array([d["x"] for d in self.dict_tmp["acc"]], dtype=float)
        acc_y = np.array([d["y"] for d in self.dict_tmp["acc"]], dtype=float)
        acc_z = np.array([d["z"] for d in self.dict_tmp["acc"]], dtype=float)
        gyro_x = np.array([d["x"] for d in self.dict_tmp["gyro"]], dtype=float)
        gyro_y = np.array([d["y"] for d in self.dict_tmp["gyro"]], dtype=float)
        gyro_z = np.array([d["z"] for d in self.dict_tmp["gyro"]], dtype=float)

        acc_magnitude = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        gyro_magnitude = np.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)

        feature_arrays = {
            "acc_x": acc_x,
            "acc_y": acc_y,
            "acc_z": acc_z,
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z,
            "acc_magnitude": acc_magnitude,
            "gyro_magnitude": gyro_magnitude,
        }

        feature_list = {}
        for col in cols_to_evaluate:
            values = feature_arrays[col]
            feature_list[f"{col}_max"] = float(np.max(values))
            feature_list[f"{col}_median"] = float(np.median(values))
            feature_list[f"{col}_std"] = float(np.std(values, ddof=1))
            feature_list[f"{col}_dominant_freq"] = self.get_dominant_frequency(
                values, self.frequency)

        feature_list["acc_x_y_corr"] = self.get_correlation_array(acc_x, acc_y)
        feature_list["acc_x_z_corr"] = self.get_correlation_array(acc_x, acc_z)
        feature_list["acc_y_z_corr"] = self.get_correlation_array(acc_y, acc_z)
        feature_list["gyro_x_y_corr"] = self.get_correlation_array(
            gyro_x, gyro_y)
        feature_list["gyro_x_z_corr"] = self.get_correlation_array(
            gyro_x, gyro_z)
        feature_list["gyro_y_z_corr"] = self.get_correlation_array(
            gyro_y, gyro_z)

        return pd.DataFrame([feature_list])

    # helper function similar to notebook
    def get_correlation_array(self, a, b):
        if np.std(a) == 0 or np.std(b) == 0:
            return 0.0
        corr = np.corrcoef(a, b)[0, 1]
        return float(corr) if not np.isnan(corr) else 0.0

    # helper function similar to notebook
    def get_dominant_frequency(self, series, sampling_rate):
        series = np.asarray(series)
        n = len(series)
        if n < 2:
            return 0.0

        freqs = np.fft.rfftfreq(n, d=1 / sampling_rate)
        fft_magnitude = np.abs(np.fft.rfft(series))

        if len(fft_magnitude) <= 1:
            return 0.0

        return float(freqs[1:][np.argmax(fft_magnitude[1:])])
