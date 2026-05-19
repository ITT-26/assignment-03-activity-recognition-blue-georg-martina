# this program visualizes activities with pyglet

from activity_recognizer import ActivityRecognizer
import pyglet
from constants import *

# screen for each game state
game_states = ["menu", "exercise", "result"]
game_state = "menu"

win = pyglet.window.Window(
    WINDOW_WIDTH, WINDOW_HEIGHT, caption="Fitness Trainer")
pyglet.gl.glClearColor(
    BACKGROUND[0]/255, BACKGROUND[1]/255, BACKGROUND[2]/255, 1)

settings = {
    "countdown_time": 5,
    "running_time": 15,
    "rowing_time": 15,
    "jumping_jacks_time": 15,
    "lifting_time": 15,
    "frequency": 20,
    "placement": "hand"
}

setting_labels = {
    "countdown_time": "Countdown Time [s]",
    "running_time": "Running Time [s]",
    "rowing_time": "Rowing Time [s]",
    "jumping_jacks_time": "Jumping Jacks Time [s]",
    "lifting_time": "Lifting Time [s]",
    "frequency": "Frequency [Hz]",
    "placement": "Placement"
}


menu_keys = list(settings.keys())
setting_index = 0


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
            case "running_time" | "rowing_time" | "jumping_jacks_time" | "lifting_time":
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
            case "running_time" | "rowing_time" | "jumping_jacks_time" | "lifting_time":
                settings[setting] = min(
                    settings[setting] + EXERCISE_DURATION_STEP, MAX_EXERCISE_DURATION)
            case "frequency":
                settings[setting] = 20 if settings[setting] == 100 else 100
            case "placement":
                settings[setting] = "hand" if settings[setting] == "pocket" else "pocket"


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




# result screen
# show summary -> simplistic
# press button to go back to menu
# press another button to start a new workout with the same settings


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


pyglet.app.run()




