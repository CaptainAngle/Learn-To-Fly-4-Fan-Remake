# Game Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Physics
GRAVITY = 0.35
MAX_VELOCITY = 32
BOOST_FORCE = 0.9
ROTATION_SPEED = 1.5
PIXELS_PER_METER = 100
WORLD_LENGTH_M = 1000

# Aerodynamics (SI units)
GRAVITY_MPS2 = 9.81
AIR_DENSITY = 1.225
PLAYER_MASS_KG = 12.0
BASE_WING_AREA_M2 = 1.8
LIFT_COEFF_0 = 0.30
LIFT_COEFF_ALPHA = 4.8
LIFT_COEFF_MIN = -0.6
LIFT_COEFF_MAX = 2.1
DRAG_COEFF_0 = 0.12
DRAG_INDUCED_K = 0.18
BOOST_THRUST_N = 65.0
BOOST_FUEL_BURN_PER_SEC = 14.0

# Ground material tuning
ICE_FRICTION = 0.9992
SNOW_FRICTION = 0.985
DEFAULT_GROUND_FRICTION = 0.995
FLAT_ICE_SLOPE_THRESHOLD = 0.12
FLAT_ICE_FRICTION = 0.99985
ZERO_FRICTION_SLOPE_THRESHOLD = 0.08
RAMP_GRAVITY_ALONG_SLOPE_MULT = 0.45

# Game States
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_UPGRADE = "upgrade"
STATE_MISSION_SELECT = "mission_select"
STATE_RESULTS = "results"
STATE_PAUSED = "paused"

# Colors
COLOR_SKY = (200, 230, 255)
COLOR_SKY_DARK = (100, 180, 240)
COLOR_GROUND = (120, 100, 80)
COLOR_SNOW = (248, 250, 252)
COLOR_ICE = (200, 235, 255)
COLOR_TEXT = (245, 245, 250)
COLOR_DARK = (25, 30, 40)
COLOR_ACCENT = (255, 140, 60)

# Gear Categories
SLED_TIERS = {
    "the_plank": {"name": "The Plank", "ramp_friction_mult": 1.00, "cost": 0},
    "plank_mk2": {"name": "Plank Mk. 2", "ramp_friction_mult": 1.01, "cost": 250},
    "good_ol_sled": {"name": "Good 'Ol Sled", "ramp_friction_mult": 1.02, "cost": 700},
    "bobsled": {"name": "Bobsled", "ramp_friction_mult": 1.03, "cost": 1500},
}

GLIDER_TIERS = {
    "kite": {"name": "Kite", "glide_mult": 1.20, "camber_deg": 2.0, "cost": 0},
    "old_glider": {"name": "Old Glider", "glide_mult": 1.45, "camber_deg": 3.0, "cost": 500},
    "hand_glider": {"name": "Hand Glider", "glide_mult": 1.75, "camber_deg": 4.0, "cost": 1300},
}

BOOSTER_TIERS = {
    "balloon": {"name": "Balloon", "boost_mult": 0.75, "fuel": 85, "cost": 0},
    "sugar_rocket": {"name": "Sugar Rocket", "boost_mult": 1.00, "fuel": 110, "cost": 400},
    "pulse_jet": {"name": "Pulse Jet", "boost_mult": 1.35, "fuel": 130, "cost": 1000},
    "ramjet": {"name": "Ramjet", "boost_mult": 1.70, "fuel": 150, "cost": 1900},
}

RAMP_HEIGHT_TIERS = [
    {"name": "Base Ramp", "launch_gap_m": 3.0, "cost": 0},
    {"name": "Raised Ramp", "launch_gap_m": 4.0, "cost": 350},
    {"name": "Tall Ramp", "launch_gap_m": 5.0, "cost": 900},
    {"name": "High Ramp", "launch_gap_m": 6.5, "cost": 1700},
]

RAMP_DROP_TIERS = [
    {"name": "Shallow Drop", "extra_drop_m": 0.0, "cost": 0},
    {"name": "Deeper Drop", "extra_drop_m": 0.5, "cost": 450},
    {"name": "Steep Drop", "extra_drop_m": 1.0, "cost": 1100},
    {"name": "Extreme Drop", "extra_drop_m": 1.6, "cost": 2100},
]

