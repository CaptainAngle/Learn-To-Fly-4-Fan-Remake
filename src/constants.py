# Game Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Physics
GRAVITY = 0.4
WIND_SPEED = 0.2
MAX_VELOCITY = 20

# Game States
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_UPGRADE = "upgrade"
STATE_MISSION_SELECT = "mission_select"
STATE_RESULTS = "results"
STATE_PAUSED = "paused"

# Colors
COLOR_SKY = (135, 206, 235)
COLOR_GROUND = (139, 69, 19)
COLOR_SNOW = (255, 255, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_DARK = (20, 20, 20)

# Flight Gear
GEAR_TYPES = {
    "base": {"speed": 1.0, "acceleration": 1.0, "glide": 1.0, "fuel": 100, "cost": 0},
    "jetpack_mk1": {"speed": 1.3, "acceleration": 1.5, "glide": 0.8, "fuel": 80, "cost": 500},
    "wingsuit": {"speed": 1.1, "acceleration": 0.8, "glide": 1.8, "fuel": 150, "cost": 800},
    "rocket_boots": {"speed": 1.8, "acceleration": 2.0, "glide": 0.5, "fuel": 60, "cost": 1200},
    "propeller_hat": {"speed": 1.2, "acceleration": 1.2, "glide": 1.3, "fuel": 100, "cost": 600},
}

