import os

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60  # Frames por segundo

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
DARK_GRAY = (30, 30, 30)
LIGHT_GRAY = (180, 180, 180)

DEFAULT_FONT = "arial"
FONT_SIZE = 32

TIMER_SECONDS = 40
TIMER_WARNING_THRESHOLD = 10  # segundos restantes para tocar alerta de tempo

MAX_PLAYERS = 4
PLAYER_COLORS = [RED, BLUE, GREEN, YELLOW]
PLAYER_IMAGE_FILES = [
    "assets/player1.png",
    "assets/player2.png",
    "assets/player3.png",
    "assets/player4.png"
]

ASSET_PATH = "assets"
BACKGROUND_IMG = os.path.join(ASSET_PATH, "bg.png")


# Sons
SOUND_LETRA = ASSET_PATH + "letra.wav"
SOUND_TIMEOUT = ASSET_PATH + "timeout.wav"


ALPHABET = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
