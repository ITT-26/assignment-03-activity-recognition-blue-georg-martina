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
game_states = ["menu", "exercise_instructions", "exercise_countdown",
               "exercise", "exercise_done"]
game_state = "menu"

current_exercise = None
sprite = None
exercise_countdown = None

window_counter = 0
first_window = True

button_1_queued = False
instruction_entered_at = 0

current_acc_data = None
current_gyro_data = None

exercises_done = 0
exercises_to_go = ["running", "rowing", "jumpingjacks", "lifting"]

win = pyglet.window.Window(
    WINDOW_WIDTH, WINDOW_HEIGHT, caption="Fitness Trainer")
pyglet.gl.glClearColor(
    BACKGROUND[0]/255, BACKGROUND[1]/255, BACKGROUND[2]/255, 1)

settings = {
    "countdown_time": 1,
    "running_time": 1,
    "rowing_time": 1,
    "jumpingjacks_time": 15,
    "lifting_time": 1,
    "frequency": 20,
    "placement": "hand"
}

setting_labels = {
    "countdown_time": "Countdown Time [s]",
    "running_time": "Running Time [s]",
    "rowing_time": "Rowing Time [s]",
    "jumpingjacks_time": "Jumping Jacks Time [s]",
    "lifting_time": "Lifting Time [s]",
    "frequency": "Frequency [Hz]",
    "placement": "Placement"
}

exercise_labels = {
    "running": "Running",
    "rowing": "Rowing",
    "jumpingjacks": "Jumping Jacks",
    "lifting": "Lifting"
}

predicted_activity = "unknown"
is_correct = False
next_window_time = 0
sampling_scheduled = False
recognizer = ActivityRecognizer(settings["frequency"], settings["placement"])


menu_keys = list(settings.keys())
setting_index = 0

# TODO: call this after the user has selected settings
start_countdown = settings["countdown_time"]


def menu_controls(symbol):
    global setting_index, settings

    setting = menu_keys[setting_index]

    # go through settings
    if symbol == pyglet.window.key.UP:
        setting_index = (setting_index - 1) % len(menu_keys)
    elif symbol == pyglet.window.key.DOWN:
        setting_index = (setting_index + 1) % len(menu_keys)

    # change settings
    elif symbol == pyglet.window.key.LEFT:
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


def reset_recognition():
    global predicted_activity, is_correct, next_window_time, first_window
    recognizer.change_configuration(settings["frequency"], settings["placement"])
    predicted_activity = "unknown"
    is_correct = False
    next_window_time = 0.0
    first_window = True


# dippid callbacks

def handle_button_1(data):

    if data == 0:
        return

    global button_1_queued
    button_1_queued = True


def go_to_instructions():
    global game_state, instruction_entered_at
    game_state = "exercise_instructions"
    instruction_entered_at = time.time()


# can't do all that in the callback because of the pyglet loop -> queue button_press
def button_1_pressed_earlier():
    global game_state, start_countdown, exercises_to_go, button_1_queued, recognizer, exercises_done
    if game_state == "menu":
        exercises_to_go = ["running", "rowing", "jumpingjacks", "lifting"]
        randomly_select_exercise()
        reset_recognition()
        go_to_instructions()

    elif game_state == "exercise_instructions":

        elapsed = time.time() - instruction_entered_at
        if elapsed < MIN_INSTRUCTION_DURATION:
            button_1_queued = False
            return

        game_state = "exercise_countdown"
        start_countdown = settings["countdown_time"]

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

    if game_state == "exercise_done" and exercises_done <= len(exercise_labels):
        game_state = "menu"
        exercises_done = 0
        exercises_to_go = ["running", "rowing", "jumpingjacks", "lifting"]


def handle_accelerometer(data):
    global current_acc_data
    current_acc_data = data


def handle_gyroscope(data):
    global current_gyro_data
    current_gyro_data = data


sensor.register_callback("button_1", handle_button_1)
sensor.register_callback("button_2", handle_button_2)
sensor.register_callback('accelerometer', handle_accelerometer)
sensor.register_callback('gyroscope', handle_gyroscope)

# menu screen
# countdown time [s]
# running [s]
# rowing [s]
# jumping jacks [s]
# lifting [s]
# frequency
# placement


def draw_menu():
    title = pyglet.text.Label(
        "Settings",
        font_size=36,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT - 50,
        anchor_x="center",
        color=TEXT_COLOR
    )

    title.draw()

    y_start = WINDOW_HEIGHT - 150
    y_step = 50

    for idx, (setting, value) in enumerate(settings.items()):

        label_setting = pyglet.text.Label(
            setting_labels[setting],
            font_size=24,
            x=WINDOW_WIDTH//2 - 200,
            y=y_start - idx * y_step,
            anchor_x="left",
            color=TEXT_COLOR
        )

        display_value = f"  {value}  "
        if idx == setting_index:
            display_value = f"< {value} >"

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


# exercise screen
# show label and image of exercise
# press button to start countdown
# give feedback on if the exercise is performed correctly -> green/red background (?)
# show time left
# feedback stops when time is up
# press button to show next exercise / go to result screen if all exercises are done
# press another button to go back to menu

def select_exercise(exercise):
    global current_exercise, sprite, exercise_countdown
    current_exercise = exercise
    images = []
    for img_path in IMG_PATHS[exercise]:
        images.append(pyglet.image.load(img_path))

    animation = pyglet.image.Animation.from_image_sequence(
        images, duration=0.5, loop=True)
    sprite = pyglet.sprite.Sprite(animation)
    sprite.scale = 0.3
    sprite.update(x=WINDOW_WIDTH//2 - sprite.width//2,
                  y=WINDOW_HEIGHT//2 - sprite.height//2)

    exercise_countdown = settings[f"{exercise}_time"]


def randomly_select_exercise():
    choice = random.choice(exercises_to_go)
    select_exercise(choice)
    exercises_to_go.remove(choice)


def draw_exercise_instructions():

    exercise_label = pyglet.text.Label(
        f"Get ready for: {exercise_labels[current_exercise]}!",
        font_size=36,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT - 50,
        anchor_x="center",
        color=TEXT_COLOR
    )
    exercise_label.draw()

    sprite.draw()

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


def draw_countdown():
    countdown_label = pyglet.text.Label(
        f"{int(start_countdown) + 1}",
        font_size=72,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT//2,
        anchor_x="center",
        color=TEXT_COLOR
    )
    countdown_label.draw()

    # result screen
    # show summary -> simplistic
    # press button to go back to menu
    # press another button to start a new workout with the same settings


def draw_exercise():
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

    sprite.draw()

    test = is_correct

    text = "CORRECT" if test else "INCORRECT"
    text_color = T_COLOR_CORRECT if test else T_COLOR_INCORRECT

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


def draw_exercise_done():
    global exercises_done

    text = None

    if exercises_done >= len(exercise_labels):
        text = "Workout complete! Great job!\nPress Button 1 to start a new workout with the same settings\nPress Button 2 to go back to the menu"

    else:
        text = f"Exercise complete! You still have {len(exercise_labels) - exercises_done} exercises to go!\nPress Button 1 to start the next exercise"

    label = pyglet.text.Label(
        text,
        font_size=22,
        x=WINDOW_WIDTH//2,
        y=WINDOW_HEIGHT//2,
        anchor_x="center",
        color=TEXT_COLOR,
        multiline=True,
        width=WINDOW_WIDTH - 100,
        align="center"
    )

    label.draw()


@win.event
def on_key_press(symbol, modifiers):
    if game_state == "menu":
        menu_controls(symbol)


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


# thread for prediction
def prediction_worker():
    global predicted_activity, is_correct, next_window_time, first_window

    next_sample_time = 0.0

    # loop
    while prediction_thread_running:
        # only predict while exercising
        if game_state != "exercise":
            next_sample_time = 0.0
            time.sleep(0.001)
            continue

        now = time.time()
        sample_period = 1.0 / settings["frequency"]

        if now >= next_sample_time:
            with prediction_lock:
                recognizer.dict_tmp["acc"].append(current_acc_data)
                recognizer.dict_tmp["gyro"].append(current_gyro_data)
            next_sample_time = now + sample_period

        if now >= next_window_time:
            with prediction_lock:
                predicted_activity = recognizer.return_classification()
                is_correct = (predicted_activity == current_exercise)
                next_window_time = now + WINDOWS_SIZE_SECONDS * (1 - OVERLAP)

        time.sleep(0.00001)


def update(dt):
    global game_state, start_countdown, exercise_countdown, settings, exercises_done, button_1_queued, next_window_time, first_window
    if button_1_queued:
        button_1_pressed_earlier()

    if game_state == "exercise_countdown":
        if start_countdown > 0:
            start_countdown -= dt
            if start_countdown <= 0:
                game_state = "exercise"
                start_countdown = settings["countdown_time"]
                next_window_time = time.time() + WINDOWS_SIZE_SECONDS
                first_window = False

    if game_state == "exercise":
        if exercise_countdown > 0:
            exercise_countdown -= dt
            if exercise_countdown <= 0:
                game_state = "exercise_done"
                exercise_countdown = settings[f"{current_exercise}_time"]
                exercises_done += 1


@win.event
def on_close():
    global prediction_thread_running
    prediction_thread_running = False
    sensor.disconnect()
    if worker.is_alive():
        worker.join(timeout=1)
    pyglet.app.exit()


worker = threading.Thread(target=prediction_worker, daemon=False)
worker.start()

pyglet.clock.schedule_interval(update, 1/60)
pyglet.app.run()
