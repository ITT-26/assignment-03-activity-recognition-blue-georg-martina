# this program gathers sensor data

# Note:
# To change the frequency of the data collection or the placement of the device,
# the program needs to be restarted and the user needs to input the desired settings before starting the workout.

import time
import pandas as pd
from DIPPID import SensorUDP
import os

# constants for time delay and workout duration
COUNTDOWN_TIME = 3
SET_TIME = 10
SLEEP_TIME_AFTER_WORKOUT = 1

# use UPD (via WiFi) for communication
PORT = 5700
sensor = SensorUDP(PORT)

# buttons mapped to workouts
workouts = {
    1: "running",
    2: "rowing",
    3: "jumpingjacks",
    4: "lifting"
}

# variables to keep track of the current workout and if the user is working out
current_workout = None
working_out = False

# placements and frequencies should be chosen before the workout starts
placements = ["hand", "pocket"]
freqs = [20, 100]
placement = None
freq = None

# variables for time tracking during the workout
now = None
w_start_time = None
w_end_time = None

last_time = 0

# temporary dictionary to record data
dict_tmp = {"id": [], "timestamp": [], "gyro": [], "acc": []}

# variables to store current data
current_acc_data = None
current_gyro_data = None

# to see if any workout should be able to start
ready = False

# once the workout is complete, recorded data is saved to a csv file


def finalize_workout():
    global current_workout, dict_tmp, working_out, ready

    # workout is complete -> working_out = False
    working_out = False

    # organizing data into desired format
    new_df = pd.DataFrame({
        "id": dict_tmp["id"],
        "timestamp": dict_tmp["timestamp"],
        "acc_x": [d["x"] for d in dict_tmp["acc"]],
        "acc_y": [d["y"] for d in dict_tmp["acc"]],
        "acc_z": [d["z"] for d in dict_tmp["acc"]],
        "gyro_x": [d["x"] for d in dict_tmp["gyro"]],
        "gyro_y": [d["y"] for d in dict_tmp["gyro"]],
        "gyro_z": [d["z"] for d in dict_tmp["gyro"]],
    })

    # clear temporary dictionary
    for data_type in dict_tmp:
        dict_tmp[data_type] = []

    # let the user know the workout is complete
    print("Workout complete")

    # save data to csv file
    f_name = get_filename()
    new_df.to_csv(f"data/{f_name}", index=False)

    # sleep for a bit before letting the user start another workout
    time.sleep(SLEEP_TIME_AFTER_WORKOUT)
    ready = True

# callback function for button press


def handle_button_press(data, button_id):
    global current_workout, now, w_start_time, w_end_time, working_out, ready

    # data is 0 when button is released
    if data == 0:
        return

    # ignore button press when there is a workout in progress or when the user hasn't inputted settings
    if working_out or not ready:
        return

    # ready is set to False to prevent the user from starting another workout before the current workout ends
    ready = False

    # display which button is pressed
    print(f"Button {button_id} pressed")

    # set current workout label based on pressed button
    current_workout = workouts[button_id]

    # initialize time variables for the workout
    now = time.time()
    w_start_time = now + COUNTDOWN_TIME
    w_end_time = w_start_time + SET_TIME

    # set working_out to True to indicate that a workout is in progress
    working_out = True

    # display chosen workout
    print(f"Current workout: {current_workout}")


# differentiate between what button is pressed and call the actual handler function with the button id
def handle_button_1(data):
    handle_button_press(data, 1)


def handle_button_2(data):
    handle_button_press(data, 2)


def handle_button_3(data):
    handle_button_press(data, 3)


def handle_button_4(data):
    handle_button_press(data, 4)


# callbacks for sensor data -> stores data in global variables
def gyro_callback(data):
    global current_gyro_data
    current_gyro_data = data


def acc_callback(data):
    global current_acc_data
    current_acc_data = data


# register every callback
sensor.register_callback("button_1", handle_button_1)
sensor.register_callback("button_2", handle_button_2)
sensor.register_callback("button_3", handle_button_3)
sensor.register_callback("button_4", handle_button_4)

sensor.register_callback('accelerometer', acc_callback)
sensor.register_callback('gyroscope', gyro_callback)


# START OF INPUTS

# name for file name
name = input("Your name: ")

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


# iterators, to see what repition of the workout is being recorded
iterators = {
    "running": 1,
    "rowing": 1,
    "jumpingjacks": 1,
    "lifting": 1
}


# get the name for the csv
def get_filename():

    # all previously recorded files in the data folder
    filenames = os.listdir("data")

    # update iterators
    for w_name in iterators:

        iterators[w_name] = 1

        start_string = f"{name}-{w_name}-{freq}Hz-{placement}-"

        for f_name in filenames:
            if f_name.startswith(start_string):
                iterators[w_name] += 1

    # build the file name
    workout = current_workout
    repetition = iterators[workout]
    return f"{name}-{workout}-{freq}Hz-{placement}-{repetition}.csv"


# iterator for the while loop -> number of data point
iterator = 1

# ready for workout
ready = True

print("Ready to start. Press the corresponding button on your device to start a workout")
for workout_name, button in workouts.items():
    print(f"> {workout_name}: {button}")

started = False

# workout loop
while True:

    # there is no workout in progress
    if not working_out or w_end_time is None:
        time.sleep(0.001)
        continue

    # countdown
    elif time.time() < w_start_time:
        print(int(w_start_time - time.time()) + 1)
        time.sleep(1)
        continue

    # workout in progress
    elif time.time() <= w_end_time:

        if not started:
            print("Workout started!")
            started = True

        if time.time() - last_time >= 1/freq or last_time == 0:
            dict_tmp["id"].append(iterator)
            iterator += 1
            dict_tmp["timestamp"].append(time.time())
            dict_tmp["acc"].append(current_acc_data)
            dict_tmp["gyro"].append(current_gyro_data)
            last_time = time.time()

    # workout complete
    elif time.time() > w_end_time:
        finalize_workout()
        iterator = 1
        started = False
