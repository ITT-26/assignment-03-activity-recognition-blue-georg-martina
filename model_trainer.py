# copied from notebook (slight adjustments) -> not commented that thoroughly
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from constants import *


class ModelTrainer:

    def __init__(self):
        self.data_folder = 'data'
        self.models = {}
        self.best_params = {
            '20Hz_hand':    {'C': 10, 'gamma': 'scale', 'kernel': 'rbf'},
            '20Hz_pocket':  {'C': 10, 'gamma': 0.01,   'kernel': 'rbf'},
            '100Hz_hand':   {'C': 10, 'gamma': 'scale', 'kernel': 'rbf'},
            '100Hz_pocket': {'C': 10, 'gamma': 'scale', 'kernel': 'rbf'},
        }
        self.groups = {
            '20Hz_hand':    ('20Hz-hand',   WINDOW_SIZE_20HZ,  20),
            '20Hz_pocket':  ('20Hz-pocket', WINDOW_SIZE_20HZ,  20),
            '100Hz_hand':   ('100Hz-hand',  WINDOW_SIZE_100HZ, 100),
            '100Hz_pocket': ('100Hz-pocket', WINDOW_SIZE_100HZ, 100),
        }

    def get_files(self):
        all_csv_paths = []
        for dirpath, _, filenames in os.walk(self.data_folder):
            for filename in filenames:
                if filename.endswith('.csv'):
                    all_csv_paths.append(
                        (os.path.join(dirpath, filename), filename))
        return all_csv_paths
    
    def make_df_list(self, csv_paths, keyword):
        activity_labels = {name: label for label, name in WORKOUTS.items() if label is not None}
        dfs = []
        for full_path, filename in csv_paths:
            if keyword in filename:
                df = pd.read_csv(full_path)
                for activity, label in activity_labels.items():
                    if activity in filename:
                        df['activity_label'] = label
                        break
                dfs.append(df)
        return dfs

    def radian_or_degree(self, df):
        for col in df.columns:
            if 'gyro' in col:
                if df[col].abs().max() > 100:
                    return 'degree'
        return 'radian'

    def degree_to_radian(self, df):
        for col in df.columns:
            if 'gyro' in col:
                df[col] = np.deg2rad(df[col])
        return df

    # unit conversion, NaN drop, timestamp normalization
    def preprocess(self, dfs):
        for df in dfs:
            if self.radian_or_degree(df) == 'degree':
                self.degree_to_radian(df)

        dfs = [df.dropna() for df in dfs]

        normalized = []
        for df in dfs:
            df_tmp = df.copy()
            df_tmp['timestamp'] = df_tmp['timestamp'] - \
                df_tmp['timestamp'].min()
            normalized.append(df_tmp)

        return normalized

    def get_windows(self, df, window_size):
        step = int(window_size * (1 - OVERLAP))
        return [df.iloc[start:start + window_size]
                for start in range(0, len(df) - window_size + 1, step)]

    def get_dominant_frequency(self, series, sampling_rate):
        n = len(series)
        freqs = np.fft.rfftfreq(n, d=1 / sampling_rate)
        fft_magnitude = np.abs(np.fft.rfft(series))
        return freqs[1:][np.argmax(fft_magnitude[1:])]

    def get_correlation(self, window, col1, col2):
        corr = window[col1].corr(window[col2])
        return corr if not np.isnan(corr) else 0.0

    # get all features
    def extract_features_from_window(self, window, sampling_rate):
        window = window.copy()
        window['acc_magnitude'] = np.sqrt(
            window['acc_x']**2 + window['acc_y']**2 + window['acc_z']**2)
        window['gyro_magnitude'] = np.sqrt(
            window['gyro_x']**2 + window['gyro_y']**2 + window['gyro_z']**2)

        cols = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y',
                'gyro_z', 'acc_magnitude', 'gyro_magnitude']
        features = {'activity_label': window['activity_label'].iloc[0]}

        for col in cols:
            features[f'{col}_max'] = window[col].max()
            features[f'{col}_median'] = window[col].median()
            features[f'{col}_std'] = window[col].std()
            features[f'{col}_dominant_freq'] = self.get_dominant_frequency(
                window[col], sampling_rate)

        features['acc_x_y_corr'] = self.get_correlation(
            window, 'acc_x', 'acc_y')
        features['acc_x_z_corr'] = self.get_correlation(
            window, 'acc_x', 'acc_z')
        features['acc_y_z_corr'] = self.get_correlation(
            window, 'acc_y', 'acc_z')
        features['gyro_x_y_corr'] = self.get_correlation(
            window, 'gyro_x', 'gyro_y')
        features['gyro_x_z_corr'] = self.get_correlation(
            window, 'gyro_x', 'gyro_z')
        features['gyro_y_z_corr'] = self.get_correlation(
            window, 'gyro_y', 'gyro_z')

        return features

    def build_feature_df(self, dfs, window_size, sampling_rate):
        all_features = []
        for df in dfs:
            for window in self.get_windows(df, window_size):
                all_features.append(
                    self.extract_features_from_window(window, sampling_rate))
        return pd.DataFrame(all_features)

    def train_models(self):
        csv_paths = self.get_files()

        for key, (keyword, window_size, sampling_rate) in self.groups.items():
            params = self.best_params[key]
            dfs = self.make_df_list(csv_paths, keyword)
            dfs = self.preprocess(dfs)

            train_dfs, _ = train_test_split(
                dfs, test_size=0.2, random_state=42)
            feature_df = self.build_feature_df(
                train_dfs, window_size, sampling_rate)

            X_train = feature_df.drop(columns=['activity_label'])
            y_train = feature_df['activity_label']

            model = Pipeline([
                ('scaler', StandardScaler()),
                ('svc', OneVsRestClassifier(SVC(
                    C=params['C'],
                    gamma=params['gamma'],
                    kernel=params['kernel'],
                    probability=True
                )))
            ])
            model.fit(X_train, y_train)
            self.models[key] = model
            
        return self.models


