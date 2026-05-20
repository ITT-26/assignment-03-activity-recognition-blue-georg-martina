[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/QwFWBwI4)
 
# 0 Requirements

- Python (3.13.13)
- Install requirements using pip install -r requirements.txt

# 1 Gathering Training Data

We used the scripts gather_data.py and gather_data_martina.py (because of the missing gyro functionality) to record our data.

To run the file use python gather_data.py

In the console the user can choose their name, the sampling rate, DIPPID-device placement and the activity. After a brief countdown the recording starts. All the Output is on the console and csv-files are saved automatically.

# 2 Activity Recognition

## 2.1 Model Training

The notebook pre_processing_and_model_testing.ipynb documents the full pipeline for training and evaluating the activity recognition models. It covers data pre-processing (gyroscope unit normalization, NaN removal, timestamp normalization), feature extraction (38 features per window across 8 signal channels), and systematic comparisons of SVM kernels, multiclass strategies, window sizes, overlap, train-test split ratios, and scalers. All decisions and results are documented with plots and explanations.

The best parameters found are used directly in the fitness trainer application.

The notebook can be run to reproduce all comparisons and results.


## 2.2 The Application

Since all of our configurations delivered solid models we wanted to adjust our application so that the user can choose any combination of parameters (phone placement and sampling frequency).

For Testing purposes we created continous_prediction_test.py (to run use python continous_prediction_test.py). We used it to configure the parameters in constants.py

If you want to change some stuff use this script and try to change the constants file according to your desires.

In activity_recognizer.py we export a class that gives us a prediction according to the constants. We are using a majority voting system. This means not every data point is deciding for a single point in time. It has to be the most frequent classification in the last few meassurements.

This Recognizer is used in continuous_test_recognizer.py, which works somewhat similar to continous_prediction_test.py but with less prints and the Recognizer. To try it out use: python continous_test_recognizer.py

The actual application is fitness_trainer.py. To start it use: python fitness_trainer.py

The usual flow of this script is:
- menu
- exercise preview
- countdown
- exercise
- exercise complete screen

Every of these steps gets repeated until there are no more exercises left (the menu screen won't loop)

The exercises are put in a random order and the User can use their DIPPID-device to control the timing of the exercises (should prevent exhaustion if they need a break)

During the exercise, the user can see, if they are doing it correctly, incorrectly or if the model still has to calculate an evaluation.

After all the exercises are completed you can start it again with a new order or return to the menu screen.