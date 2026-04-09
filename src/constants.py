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
WORLD_LENGTH_M = 6000

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
RAMP_FRICTION_LOSS_DIVISOR = 20.0

# Obstacle progression
OBSTACLE_LAYOUT = [
    {"name": "Snowman", "distance_m": 50, "kind": "snowman", "hp": 26, "destruction_points": 1},
    {"name": "Snowmound", "distance_m": 400, "kind": "snowmound", "hp": 44, "destruction_points": 2},
    {"name": "Rocky Hill", "distance_m": 1000, "kind": "rocky_hill", "hp": 76, "destruction_points": 3},
    {"name": "Iceberg", "distance_m": 2200, "kind": "iceberg", "hp": 118, "destruction_points": 4},
    {"name": "The Wall", "distance_m": 4500, "kind": "glacier_wall", "hp": 190, "destruction_points": 6},
]

# End-of-day earnings weights
# dollars = distance*k + max_speed*l + max_altitude*m + duration*n + destruction*o
EARNING_K_DISTANCE = 0.72
EARNING_L_MAX_SPEED = 3.4
EARNING_M_MAX_ALTITUDE = 6.0
EARNING_N_DURATION = 1.35
EARNING_O_DESTRUCTION = 180.0

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

PAYLOAD_TIERS = {
    # Regular payloads: strong speed-scaling impact damage.
    "sand": {"name": "Sand", "payload_type": "regular", "impact_mult": 1.45, "impact_flat": 4.0, "explosion_damage": 0.0, "cost": 220},
    "iron_pellets": {"name": "Iron Pellets", "payload_type": "regular", "impact_mult": 1.85, "impact_flat": 7.0, "explosion_damage": 0.0, "cost": 620},
    "cast_iron": {"name": "Cast Iron", "payload_type": "regular", "impact_mult": 2.25, "impact_flat": 10.0, "explosion_damage": 0.0, "cost": 1180},
    "osmium": {"name": "Osmium", "payload_type": "regular", "impact_mult": 2.75, "impact_flat": 14.0, "explosion_damage": 0.0, "cost": 2100},
    # Explosive payloads: weaker impact hit, then bonus explosion if obstacle survives.
    "dyna_might": {"name": "Dyna-MIGHT", "payload_type": "explosive", "impact_mult": 0.65, "impact_flat": 3.0, "explosion_damage": 26.0, "cost": 900},
    "c4": {"name": "C4", "payload_type": "explosive", "impact_mult": 0.70, "impact_flat": 4.0, "explosion_damage": 48.0, "cost": 1750},
    "nuclear_warhead": {"name": "Nuclear Warhead", "payload_type": "explosive", "impact_mult": 0.75, "impact_flat": 6.0, "explosion_damage": 95.0, "cost": 3900},
}

RAMP_HEIGHT_TIERS = [
    {"name": "Ramp Height Lv1", "launch_gap_m": 1.0, "cost": 0},
    {"name": "Ramp Height Lv2", "launch_gap_m": 1.4, "cost": 200},
    {"name": "Ramp Height Lv3", "launch_gap_m": 1.9, "cost": 380},
    {"name": "Ramp Height Lv4", "launch_gap_m": 2.5, "cost": 620},
    {"name": "Ramp Height Lv5", "launch_gap_m": 3.2, "cost": 920},
    {"name": "Ramp Height Lv6", "launch_gap_m": 4.0, "cost": 1280},
    {"name": "Ramp Height Lv7", "launch_gap_m": 4.9, "cost": 1720},
    {"name": "Ramp Height Lv8", "launch_gap_m": 5.9, "cost": 2240},
    {"name": "Ramp Height Lv9", "launch_gap_m": 7.0, "cost": 2860},
    {"name": "Ramp Height Lv10", "launch_gap_m": 8.2, "cost": 3600},
]

RAMP_DROP_TIERS = [
    {"name": "Ramp Length Lv1", "extra_drop_m": 0.00, "cost": 0},
    {"name": "Ramp Length Lv2", "extra_drop_m": 0.20, "cost": 220},
    {"name": "Ramp Length Lv3", "extra_drop_m": 0.42, "cost": 440},
    {"name": "Ramp Length Lv4", "extra_drop_m": 0.66, "cost": 700},
    {"name": "Ramp Length Lv5", "extra_drop_m": 0.92, "cost": 1020},
    {"name": "Ramp Length Lv6", "extra_drop_m": 1.20, "cost": 1410},
    {"name": "Ramp Length Lv7", "extra_drop_m": 1.50, "cost": 1870},
    {"name": "Ramp Length Lv8", "extra_drop_m": 1.82, "cost": 2420},
    {"name": "Ramp Length Lv9", "extra_drop_m": 2.16, "cost": 3060},
    {"name": "Ramp Length Lv10", "extra_drop_m": 2.52, "cost": 3820},
]

FUEL_CAPACITY_TIERS = [
    {"name": "Fuel Lv1", "fuel_mult": 1.00, "cost": 0},
    {"name": "Fuel Lv2", "fuel_mult": 1.12, "cost": 260},
    {"name": "Fuel Lv3", "fuel_mult": 1.25, "cost": 520},
    {"name": "Fuel Lv4", "fuel_mult": 1.39, "cost": 840},
    {"name": "Fuel Lv5", "fuel_mult": 1.54, "cost": 1240},
    {"name": "Fuel Lv6", "fuel_mult": 1.70, "cost": 1720},
    {"name": "Fuel Lv7", "fuel_mult": 1.87, "cost": 2280},
    {"name": "Fuel Lv8", "fuel_mult": 2.05, "cost": 2920},
    {"name": "Fuel Lv9", "fuel_mult": 2.24, "cost": 3640},
    {"name": "Fuel Lv10", "fuel_mult": 2.44, "cost": 4450},
]

# Visual tuning
UI_EASE_SPEED = 8.0
HUD_SPEED_MAX = 260.0
HUD_ALT_MAX = 320.0
CATALOG_ANIM_SPEED = 7.5
TRAIL_POINT_LIFE_S = 0.65
TRAIL_SPAWN_SPEED_MPS = 16.0
SPEED_LINE_SPAWN_SPEED_MPS = 24.0
BOOST_PARTICLE_LIFE_S = 0.28

