# this program visualizes activities with pyglet

from activity_recognizer import ActivityRecognizer
import pyglet
import random
from constants import *
from DIPPID import SensorUDP

import time
import threading

# variables for prediction thread -> frequency differences are being avoided this way
prediction_lock = threading.Lock()
prediction_thread_running = True

sensor = SensorUDP(PORT)

# screen for each game state
game_states = ["loading", "menu", "exercise_instructions", "exercise_countdown",
               "exercise", "exercise_done"]
game_state = "loading"

# what exercise
current_exercise = None

# sprite depending on the exercise
sprite = None

# exercise countdown (how long the user has left to do the exercise)
exercise_countdown = None

# is button_1 queued -> avoid doing too much in callback
button_1_queued = False

# for instructions countdown -> set in constants
instruction_entered_at = 0

# gathering data
current_acc_data = None
current_gyro_data = None

# keep track on how many exercises are done
exercises_done = 0

# list of exercises to do
exercises_to_go = ["running", "rowing", "jumpingjacks", "lifting"]

# window
win = pyglet.window.Window(
    WINDOW_WIDTH, WINDOW_HEIGHT, caption="Fitness Trainer")

# background
pyglet.gl.glClearColor(
    BACKGROUND[0]/255, BACKGROUND[1]/255, BACKGROUND[2]/255, 1)

# default settings -> can be changed in menu
settings = {
    "countdown_time": 3,
    "running_time": 15,
    "rowing_time": 15,
    "jumpingjacks_time": 15,
    "lifting_time": 15,
    "frequency": 20,
    "placement": "hand"
}

# labels for discplaying settings
setting_labels = {
    "countdown_time": "Countdown Time [s]",
    "running_time": "Running Time [s]",
    "rowing_time": "Rowing Time [s]",
    "jumpingjacks_time": "Jumping Jacks Time [s]",
    "lifting_time": "Lifting Time [s]",
    "frequency": "Frequency [Hz]",
    "placement": "Placement"
}

# labels for displaying exercises
exercise_labels = {
    "running": "Running",
    "rowing": "Rowing",
    "jumpingjacks": "Jumping Jacks",
    "lifting": "Lifting"
}

# current predicted activity
predicted_activity = "unknown"

# True if predicted activity == current_exercise
is_correct = False

# for scheduling new window
next_window_time = 0

# activity recognizer
recognizer = None

# all settings
menu_keys = list(settings.keys())

# selected option in the menu
setting_index = 0

# countdown before the start
start_countdown = settings["countdown_time"]


# keyboard controls for menu
def menu_controls(symbol):
    global setting_index, settings

    # currently selected setting
    setting = menu_keys[setting_index]

    # go through settings (can only go up and down within the bounds of the settings)
    if symbol == pyglet.window.key.UP:
        setting_index = (setting_index - 1) % len(menu_keys)
    elif symbol == pyglet.window.key.DOWN:
        setting_index = (setting_index + 1) % len(menu_keys)

    # change settings (left and right arrow keys)
    elif symbol == pyglet.window.key.LEFT:
        # change each setting
        match setting:
            case "countdown_time":
                settings[setting] = max(settings[setting] - 1, MIN_COUNTDOWN)
            case "running_time" | "rowing_time" | "jumpingjacks_time" | "lifting_time":
                settings[setting] = max(
                    settings[setting] - EXERCISE_DURATION_STEP, MIN_EXERCISE_DURATION)
            case "frequency":
                settings[setting] = 20 if settings[setting] == 100 else 100
            case "placement":
                settings[setting] = "hand" if settings[setting] == "pocket" else "pocket"

    elif symbol == pyglet.window.key.RIGHT:
        match setting:
            case "countdown_time":
                settings[setting] = min(settings[setting] + 1, MAX_COUNTDOWN)
            case "running_time" | "rowing_time" | "jumpingjacks_time" | "lifting_time":
                settings[setting] = min(
                    settings[setting] + EXERCISE_DURATION_STEP, MAX_EXERCISE_DURATION)
            case "frequency":
                settings[setting] = 20 if settings[setting] == 100 else 100
            case "placement":
                settings[setting] = "hand" if settings[setting] == "pocket" else "pocket"


# resets recognition -> clear history, reset recognizer with new settings
def reset_recognition():
    global predicted_activity, is_correct, next_window_time
    recognizer.change_configuration(
        settings["frequency"], settings["placement"])
    predicted_activity = "unknown"
    is_correct = False
    next_window_time = 0.0


# dippid callbacks

def handle_button_1(data):

    if data == 0:
        return

    # queue button press for the main thread
    global button_1_queued
    button_1_queued = True


# helper function for moving to the instructions (with time for the button lock)
def go_to_instructions():
    global game_state, instruction_entered_at
    game_state = "exercise_instructions"
    instruction_entered_at = time.time()


# can't do all that in the callback because of the pyglet loop -> queue button_press
def button_1_pressed_earlier():
    global game_state, start_countdown, exercises_to_go, button_1_queued, recognizer, exercises_done

    # button 1 functionality in menu -> start workout session
    if game_state == "menu":
        exercises_to_go = ["running", "rowing", "jumpingjacks", "lifting"]
        randomly_select_exercise()
        reset_recognition()
        go_to_instructions()

    # button 1 functionality in instructions -> start countdown for exercise
    elif game_state == "exercise_instructions":

        elapsed = time.time() - instruction_entered_at
        if elapsed < MIN_INSTRUCTION_DURATION:
            button_1_queued = False
            return

        game_state = "exercise_countdown"
        start_countdown = settings["countdown_time"]

    # button 1 functionality in exercise done -> show next exercise (even if completed -> new workout session)
    elif game_state == "exercise_done":
        if exercises_done >= len(exercise_labels):
            exercises_to_go = ["running", "rowing", "jumpingjacks", "lifting"]
            randomly_select_exercise()
            exercises_done = 0
            reset_recognition()
            go_to_instructions()
        else:
            randomly_select_exercise()
            reset_recognition()
            go_to_instructions()
            start_countdown = settings["countdown_time"]

    button_1_queued = False


def handle_button_2(data):
    global game_state, exercises_done, exercises_to_go

    if data == 0:
        return

    # button 2 functionality in exercise done -> go back to menu
    if game_state == "exercise_done" and exercises_done >= len(exercise_labels):
        game_state = "menu"
        exercises_done = 0
        exercises_to_go = ["running", "rowing", "jumpingjacks", "lifting"]


# gather acc data
def handle_accelerometer(data):
    global current_acc_data
    current_acc_data = data


# gather gyro data
def handle_gyroscope(data):
    global current_gyro_data
    current_gyro_data = data


# register callbacks
sensor.register_callback("button_1", handle_button_1)
sensor.register_callback("button_2", handle_button_2)
sensor.register_callback('accelerometer', handle_accelerometer)
sensor.register_callback('gyroscope', handle_gyroscope)


# loading screen while model is being loaded (generated after asking for a loading screen)
def draw_loading():
    dots = "." * (int(time.time() * 2) % 3 + 1)
    label = pyglet.text.Label(
        f"Loading{dots}",
        font_size=36,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT//2,
        anchor_x="center",
        anchor_y="center",
        color=TEXT_COLOR
    )
    label.draw()


# menu screen
def draw_menu():
    # title
    title = pyglet.text.Label(
        "Settings",
        font_size=36,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT - 50,
        anchor_x="center",
        color=TEXT_COLOR
    )

    title.draw()

    # settings (go down from this spot by step for each setting)
    y_start = WINDOW_HEIGHT - 150
    y_step = 50

    # loop over every setting with id to know what setting is selected
    for idx, (setting, value) in enumerate(settings.items()):

        # category column -> doesnt change with selection
        label_setting = pyglet.text.Label(
            setting_labels[setting],
            font_size=24,
            x=WINDOW_WIDTH//2 - 200,
            y=y_start - idx * y_step,
            anchor_x="left",
            color=TEXT_COLOR
        )

        # value text -> changes with selection (< > around value)
        display_value = f"  {value}  "
        if idx == setting_index:
            display_value = f"< {value} >"

        # value column
        label_value = pyglet.text.Label(
            display_value,
            font_size=24,
            x=WINDOW_WIDTH//2 + 200,
            y=y_start - idx * y_step,
            anchor_x="center",
            color=TEXT_COLOR
        )

        label_setting.draw()
        label_value.draw()

    # label for explanation on how to continue (on DIPPID device because you need it for the workout)
    instruction_label = pyglet.text.Label(
        "Press Button 1 on your DIPPID deviceto start the workout with the selected settings",
        font_size=18,
        x=WINDOW_WIDTH//2,
        y=50,
        anchor_x="center",
        color=TEXT_COLOR,
        multiline=True,
        width=WINDOW_WIDTH - 100,
        align="center"
    )
    instruction_label.draw()


# change exercise
def select_exercise(exercise):
    global current_exercise, sprite, exercise_countdown

    # set current exercise
    current_exercise = exercise

    # set sprite for current exercise
    images = []
    for img_path in IMG_PATHS[exercise]:
        images.append(pyglet.image.load(img_path))

    # animation for exercise
    animation = pyglet.image.Animation.from_image_sequence(
        images, duration=0.5, loop=True)
    sprite = pyglet.sprite.Sprite(animation)
    sprite.scale = 0.3
    sprite.update(x=WINDOW_WIDTH//2 - sprite.width//2,
                  y=WINDOW_HEIGHT//2 - sprite.height//2)

    # set exercise countdown
    exercise_countdown = settings[f"{exercise}_time"]


# random selection of exercise -> remove selected exercise from list -> new one next time
def randomly_select_exercise():
    # redo the seed
    random.seed(time.time())
    choice = random.choice(exercises_to_go)
    select_exercise(choice)
    exercises_to_go.remove(choice)


# instructions screen
def draw_exercise_instructions():

    # display exercise name
    exercise_label = pyglet.text.Label(
        f"Get ready for: {exercise_labels[current_exercise]}!",
        font_size=36,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT - 50,
        anchor_x="center",
        color=TEXT_COLOR
    )
    exercise_label.draw()

    # show the sprite for the exercise
    sprite.draw()

    # instructions for how to continue on DIPPID device
    instruction_label = pyglet.text.Label(
        "Press Button 1 on your DIPPID device to start the countdown",
        font_size=18,
        x=WINDOW_WIDTH//2,
        y=50,
        anchor_x="center",
        color=TEXT_COLOR,
        multiline=True,
        width=WINDOW_WIDTH - 100,
        align="center"
    )
    instruction_label.draw()


# countdown screen -> show countdown until exercise starts
def draw_countdown():
    # countdown gets updated in update -> just simple display
    countdown_label = pyglet.text.Label(
        f"{int(start_countdown) + 1}",
        font_size=72,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT//2,
        anchor_x="center",
        color=TEXT_COLOR
    )
    countdown_label.draw()


# exercise screen -> show exercise, countdown for exercise and whether the prediction is correct or not (with majority voting)
def draw_exercise():

    # display exercise name and remaining time
    exercise_label = pyglet.text.Label(
        f"Remaining time for {exercise_labels[current_exercise]}:\n{int(exercise_countdown)}s",
        font_size=28,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT - 50,
        anchor_x="center",
        color=TEXT_COLOR,
        multiline=True,
        width=WINDOW_WIDTH - 100,
        align="center"
    )
    exercise_label.draw()

    # show the sprite for the exercise
    sprite.draw()

    # for the thread
    with prediction_lock:
        # check if there is enough for a majority prediction -> let the user know it's not ready for classification yet
        if len(recognizer.prediction_history) < MAX_HISTORY_LENGTH:
            text = "THINKING..."
            text_color = T_COLOR_THINKING
        # ready for classification -> show whether correct or not
        else:
            text = "CORRECT" if is_correct else "INCORRECT"
            text_color = T_COLOR_CORRECT if is_correct else T_COLOR_INCORRECT

    # show the feedback
    instruction_label = pyglet.text.Label(
        text,
        font_size=22,
        x=WINDOW_WIDTH//2,
        y=50,
        anchor_x="center",
        color=text_color,
        multiline=True,
        width=WINDOW_WIDTH - 100,
        align="center"
    )
    instruction_label.draw()


# exercise done screen -> show whether the workout session is complete or how many exercises are left (mainly so the user can take a break)
def draw_exercise_done():
    global exercises_done

    # text that will be displayed
    text = None

    # workout complete -> show controls
    if exercises_done >= len(exercise_labels):
        text = "Workout complete! Great job!\nPress Button 1 to start a new workout with the same settings\nPress Button 2 to go back to the menu"

    # workout not complete -> show how many exercises are left (and controls)
    else:
        text = f"Exercise complete! You still have {len(exercise_labels) - exercises_done} exercises to go!\nPress Button 1 to start the next exercise"

    # display the text
    label = pyglet.text.Label(
        text,
        font_size=22,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT//2,
        anchor_x="center",
        anchor_y="center",
        color=TEXT_COLOR,
        multiline=True,
        width=WINDOW_WIDTH - 100,
        align="center"
    )

    label.draw()


# for keyboard controls (DIPPID buttons not useful for our menu -> maybe whistle controls in the future?)
@win.event
def on_key_press(symbol, modifiers):
    if game_state == "menu":
        menu_controls(symbol)


# draw the correct screen depending on the state
@win.event
def on_draw():
    global game_state
    win.clear()
    if game_state == "menu":
        draw_menu()
    elif game_state == "exercise_instructions":
        draw_exercise_instructions()
    elif game_state == "exercise_countdown":
        draw_countdown()
    elif game_state == "exercise":
        draw_exercise()
    elif game_state == "exercise_done":
        draw_exercise_done()
    elif game_state == "loading":
        draw_loading()


# thread for prediction
def prediction_worker():
    global predicted_activity, is_correct, next_window_time

    # for next measurement
    next_sample_time = 0.0

    # loop
    while prediction_thread_running:

        # only predict while exercising
        if game_state != "exercise":
            next_sample_time = 0.0
            time.sleep(0.001)
            continue

        # timestamp -> check if it's time for the next measurement or the next window
        now = time.time()
        sample_period = 1.0 / settings["frequency"]

        # next measurement -> add data to recognizer
        if now >= next_sample_time:
            with prediction_lock:
                # gather data from sensors
                recognizer.dict_tmp["acc"].append(current_acc_data)
                recognizer.dict_tmp["gyro"].append(current_gyro_data)
            # set next time to collect data
            next_sample_time = now + sample_period

        # window complete
        if now >= next_window_time:
            with prediction_lock:
                # classify window (logic in activity_recognizer.py)
                predicted_activity = recognizer.return_classification()
                # see if it is correct
                is_correct = (predicted_activity == current_exercise)
                # set next window time (with overlap)
                next_window_time = now + WINDOWS_SIZE_SECONDS * (1 - OVERLAP)

        # sleep for a really short time -> no interference with measurements (we had issues)
        time.sleep(0.00001)


# loads recognizer and updates state as soon as its ready
def load_recognizer():
    global recognizer, game_state
    recognizer = ActivityRecognizer(
        settings["frequency"], settings["placement"])
    game_state = "menu"


# start loading as a thread -> main thread does gui
loading_thread = threading.Thread(target=load_recognizer, daemon=True)
loading_thread.start()


# gets called every ui frame -> different refresh rate -> thread was needed (just adjusting the refresh rate didn't work)
def update(dt):
    global game_state, start_countdown, exercise_countdown, settings, exercises_done, button_1_queued, next_window_time

    # if button 1 is queued -> do it's logic
    if button_1_queued:
        button_1_pressed_earlier()

    # automatically countdown before an exercise -> start it when it is 0
    if game_state == "exercise_countdown":
        if start_countdown > 0:
            start_countdown -= dt
            if start_countdown <= 0:
                game_state = "exercise"
                start_countdown = settings["countdown_time"]
                # set the time for the next window -> first window -> no overlap
                next_window_time = time.time() + WINDOWS_SIZE_SECONDS

    # automatically countdown during an exercise -> end it when it is 0
    if game_state == "exercise":
        if exercise_countdown > 0:
            exercise_countdown -= dt
            if exercise_countdown <= 0:
                game_state = "exercise_done"
                # reset exercise countdown
                exercise_countdown = settings[f"{current_exercise}_time"]
                # one more exercise done
                exercises_done += 1


# when closing the window -> stop everything else as well
@win.event
def on_close():
    global prediction_thread_running
    prediction_thread_running = False
    sensor.disconnect()
    if worker.is_alive():
        worker.join(timeout=1)
    pyglet.app.exit()


# start the thread
worker = threading.Thread(target=prediction_worker, daemon=False)
worker.start()

# start the window
pyglet.clock.schedule_interval(update, 1/60)
pyglet.app.run()
