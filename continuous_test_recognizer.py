import time
from DIPPID import SensorUDP
from constants import *

from activity_recognizer import ActivityRecognizer

sensor = SensorUDP(PORT)

# selected frequency and placement
freq = None
placement = None

# timestamps for windowing
now = None
next_window_start = None
last_time = 0

# whether the user is currently working out
working_out = False

# gathered data for the current window
current_acc_data = None
current_gyro_data = None

# select frequency
while freq not in FREQUENCIES:
    chosen_freq = input("Press 1 for 20Hz, 2 for 100Hz: ")
    if chosen_freq == "1":
        freq = 20
    elif chosen_freq == "2":
        freq = 100
    else:
        print("Invalid input, please try again")

# select placement
while placement not in PLACEMENTS:
    chosen_placement = input("Press 1 for hand, 2 for pocket: ")
    if chosen_placement == "1":
        placement = "hand"
    elif chosen_placement == "2":
        placement = "pocket"
    else:
        print("Invalid input, please try again")


# the recognizer will handle classification and prediction history for majority voting
recognizer = ActivityRecognizer(freq, placement)


# dippid callbacks

def handle_button_1(data):

    # start recording

    global now, next_window_start, freq, working_out

    if data == 0 or working_out:
        return

    now = time.time()
    next_window_start = now + WINDOWS_SIZE_SECONDS
    working_out = True


def handle_button_2(data):

    # reset and cancel everything

    global working_out, last_time, next_window_start

    if data == 0 or not working_out:
        return

    print("STOP BUTTON RECEIVED")

    working_out = False
    recognizer.change_configuration(freq, placement)

    last_time = 0
    next_window_start = 0


# gather acc data
def acc_callback(data):
    global current_acc_data
    current_acc_data = data


# gather gyro data
def gyro_callback(data):
    global current_gyro_data
    current_gyro_data = data


# register callbacks
sensor.register_callback("button_1", handle_button_1)
sensor.register_callback("button_2", handle_button_2)
sensor.register_callback('accelerometer', acc_callback)
sensor.register_callback('gyroscope', gyro_callback)


# workout loop
while True:

    # there is no workout in progress
    if not working_out:
        time.sleep(0.001)
        continue

    # workout in progress

    # window measurement -> give data to recognizer
    if time.time() - last_time >= 1/freq or last_time == 0:
        recognizer.dict_tmp["acc"].append(current_acc_data)
        recognizer.dict_tmp["gyro"].append(current_gyro_data)
        last_time = time.time()

    # window complete
    if time.time() >= next_window_start:
        if not working_out:
            continue

        # get prediction for current window
        predicted_activity = recognizer.return_classification()

        # set time for next window
        next_window_start = time.time() + WINDOWS_SIZE_SECONDS * (1 - OVERLAP)
        print(f"Predicted activity: {predicted_activity}")

    time.sleep(0.001)
