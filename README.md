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

Since all of our placement and sampling frequency configurations delivered solid models, we wanted to adjust our application so that the user can choose any combination of those to use the fitness trainer.

The best models for each case are loaded at the start of the application, as it is more convenient to have them ready than to repeat the wait if the user decides to change the phone placement or frequency after doing a run with different parameters. Even if this means waiting a bit at the start, a dedicated loading screen is shown during this process.

The user can also choose different durations for each exercise and countdown. This was done with a real fitness trainer in mind: it makes sense that not every type of exercise should last the same amount of time. These options are configured through a settings screen/menu.

For testing purposes we created the script continous_prediction_test.py (to run: python continous_prediction_test.py). We used it to configure the parameters in constants.py.

If you want to tweak something, use this script and adjust the constants file according to your needs.

In activity_recognizer.py we export a class that gives us a prediction based on those constants. We use a majority voting system, meaning not every individual data point determines the classification for a single moment in time, instead, it has to be the most frequent label across the last few measurements.

This Recognizer is used in continuous_test_recognizer.py, which works similarly to continous_prediction_test.py but with fewer prints and the Recognizer integrated. To try it out: python continous_test_recognizer.py

The actual application is fitness_trainer.py. To start it: python fitness_trainer.py

The usual flow of the application is:

- Menu
- Settings
- Exercise preview
- Countdown
- Exercise
- Exercise complete screen

Each of these steps is repeated until there are no more exercises left (the menu screen does not loop).

The exercises are presented in a random order, and the user can use their DIPPID device to control the timing, allowing them to take a break if needed and helping prevent exhaustion.

During an exercise, the user can see in real time whether they are performing it correctly, incorrectly, or whether the model is still computing an evaluation.

After all exercises are completed, the user can start again with a new random order or return to the menu screen.