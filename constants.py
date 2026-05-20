import os

# DIPPID constants
PORT = 5700

# model specifications
FREQUENCIES = [20, 100]
PLACEMENTS = ['hand', 'pocket']

# window specifications
WINDOWS_SIZE_SECONDS = 2
WINDOW_SIZE_20HZ = WINDOWS_SIZE_SECONDS * 20
WINDOW_SIZE_100HZ = WINDOWS_SIZE_SECONDS * 100
OVERLAP = 0.5

# thresholds for predictions -> stuff you can fine tune, this worked well for us
CLASSIFIER_THRESHOLDS = {
    '20Hz_hand': 0.95,
    '20Hz_pocket': 0.95,
    '100Hz_hand': 0.95,
    '100Hz_pocket': 0.95
}

# threshold for majority voting in the prediction history
MAJORITY_THRESHOLD = 0.5

# max length of the prediction history (for majority voting)
MAX_HISTORY_LENGTH = 3

# mapping of model output to activity name (None if below threshold)
WORKOUTS = {
    0: "running",
    1: "rowing",
    2: "jumpingjacks",
    3: "lifting",
    None: "unknown"
}

# constants for the window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BACKGROUND = (255, 255, 255)
TEXT_COLOR = (0, 0, 0, 255)
T_COLOR_CORRECT = (0, 255, 0, 255)
T_COLOR_INCORRECT = (255, 0, 0, 255)
T_COLOR_THINKING = (190, 190, 0, 255)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def rel_path(filename):
    return os.path.join(BASE_DIR, filename)


# image paths for activities
IMG_PATHS_JUMPING_JACKS = [rel_path("img/jumpingjack_1.png"),
                           rel_path("img/jumpingjack_2.png")]

IMG_PATHS_LIFTING = [rel_path("img/lifting_1.png"),
                     rel_path("img/lifting_2.png")]

IMG_PATHS_ROWING = [rel_path("img/rowing_1.png"),
                    rel_path("img/rowing_2.png")]

IMG_PATHS_RUNNING = [rel_path("img/running_1.png"),
                     rel_path("img/running_2.png")]

IMG_PATHS = {
    "jumpingjacks": IMG_PATHS_JUMPING_JACKS,
    "lifting": IMG_PATHS_LIFTING,
    "rowing": IMG_PATHS_ROWING,
    "running": IMG_PATHS_RUNNING
}

# example usage (https://docs.pyglet.org/en/development/modules/image/animation.html):
# ani = pyglet.image.Animation.from_image_sequence(images, duration=0.1, loop=True)

MIN_COUNTDOWN = 3
MAX_COUNTDOWN = 10

MIN_EXERCISE_DURATION = 10
MAX_EXERCISE_DURATION = 60
EXERCISE_DURATION_STEP = 5

MIN_INSTRUCTION_DURATION = 1
