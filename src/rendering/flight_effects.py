import math
import random
import pygame

from src.constants import (
    BOOST_PARTICLE_LIFE_S,
    COLOR_SKY,
    COLOR_SKY_DARK,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SPEED_LINE_SPAWN_SPEED_MPS,
    TRAIL_POINT_LIFE_S,
    TRAIL_SPAWN_SPEED_MPS,
)


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_color(c0, c1, t):
    t = max(0.0, min(1.0, t))
    return (
        int(_lerp(c0[0], c1[0], t)),
        int(_lerp(c0[1], c1[1], t)),
        int(_lerp(c0[2], c1[2], t)),
    )


def update_flight_visuals(game, dt, speed_mps, controls):
    """Update non-gameplay visual effects for flight readability and feel."""
    for p in game.player_trail:
        p["life"] -= dt
    game.player_trail = [p for p in game.player_trail if p["life"] > 0.0]

    if (not game.player_exploding) and speed_mps >= TRAIL_SPAWN_SPEED_MPS:
        spawn_rate = 16.0 + (speed_mps - TRAIL_SPAWN_SPEED_MPS) * 0.45
        game._trail_spawn_accum += dt * spawn_rate
        while game._trail_spawn_accum >= 1.0:
            game._trail_spawn_accum -= 1.0
            game.player_trail.append(
                {
                    "x": game.player.x - game.player.vx * random.uniform(0.8, 1.3),
                    "y": game.player.y + game.player.size * random.uniform(0.15, 0.55),
                    "life": TRAIL_POINT_LIFE_S,
                    "max": TRAIL_POINT_LIFE_S,
                }
            )

    for bp in game.boost_particles:
        bp["life"] -= dt
        bp["x"] += bp["vx"] * dt
        bp["y"] += bp["vy"] * dt
        bp["vy"] += 18.0 * dt
        bp["vx"] *= 0.988
    game.boost_particles = [bp for bp in game.boost_particles if bp["life"] > 0.0]

    if (not game.player_exploding) and game.player.is_thrusting:
        burst = 1 if random.random() < 0.45 else 2
        for _ in range(burst):
            game.boost_particles.append(
                {
                    "x": game.player.x - game.player.size * random.uniform(0.35, 0.65),
                    "y": game.player.y + game.player.size * random.uniform(0.10, 0.45),
                    "vx": -random.uniform(90.0, 190.0),
                    "vy": random.uniform(-40.0, 40.0),
                    "life": BOOST_PARTICLE_LIFE_S,
                    "max": BOOST_PARTICLE_LIFE_S,
                }
            )

    for sl in game.speed_lines:
        sl["x"] += sl["vx"] * dt
        sl["life"] -= dt
    game.speed_lines = [sl for sl in game.speed_lines if sl["life"] > 0.0 and sl["x"] > -120]

    if speed_mps >= SPEED_LINE_SPAWN_SPEED_MPS:
        density = (speed_mps - SPEED_LINE_SPAWN_SPEED_MPS) * 0.22
        game._speed_line_spawn_accum += dt * density
        while game._speed_line_spawn_accum >= 1.0:
            game._speed_line_spawn_accum -= 1.0
            game.speed_lines.append(
                {
                    "x": SCREEN_WIDTH + random.uniform(20, 160),
                    "y": random.uniform(30, SCREEN_HEIGHT - 140),
                    "len": random.uniform(18, 68),
                    "vx": -random.uniform(220.0, 520.0),
                    "life": random.uniform(0.28, 0.62),
                    "max": 0.62,
                }
            )


def draw_flight_background(game, surface):
    """Draw animated sky, sun glow, and parallax atmosphere."""
    t = game.render_time_s
    terrain_y = game.environment.terrain.get_ground_y_at(game.player.x)
    altitude_m = max(0.0, (terrain_y - (game.player.y + game.player.size)) / 100.0)
    alt_t = max(0.0, min(1.0, altitude_m / 260.0))

    low_top = (145, 205, 255)
    low_bottom = (190, 230, 255)
    high_top = (20, 35, 78)
    high_bottom = (58, 90, 145)
    top_base = _lerp_color(low_top, high_top, alt_t)
    bottom_base = _lerp_color(low_bottom, high_bottom, alt_t)

    for y in range(SCREEN_HEIGHT):
        ratio = y / max(1, SCREEN_HEIGHT - 1)
        wave = math.sin(t * 0.32 + ratio * 5.1) * (4.0 + 5.0 * (1.0 - alt_t))
        sky_col = _lerp_color(top_base, bottom_base, ratio)
        r = int(max(0, min(255, sky_col[0] + wave * 0.30)))
        g = int(max(0, min(255, sky_col[1] + wave * 0.45)))
        b = int(max(0, min(255, sky_col[2] + wave * 0.65)))
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # High-altitude star field and aurora haze.
    if alt_t > 0.18:
        star_alpha = int(185 * (alt_t - 0.18) / 0.82)
        rng_seed = int(game.camera_x * 0.02) ^ 0x53A9
        rng = random.Random(rng_seed)
        for _ in range(85):
            sx = rng.randint(0, SCREEN_WIDTH - 1)
            sy = rng.randint(0, int(SCREEN_HEIGHT * 0.72))
            rad = 1 if rng.random() < 0.82 else 2
            twinkle = 0.55 + 0.45 * math.sin(t * 2.7 + sx * 0.017 + sy * 0.013)
            a = int(star_alpha * twinkle)
            star = pygame.Surface((rad * 4 + 2, rad * 4 + 2), pygame.SRCALPHA)
            pygame.draw.circle(star, (245, 248, 255, a), (rad * 2 + 1, rad * 2 + 1), rad)
            surface.blit(star, (sx - (rad * 2 + 1), sy - (rad * 2 + 1)))
        # Aurora ribbon
        ribbon = pygame.Surface((SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.45)), pygame.SRCALPHA)
        for x in range(0, SCREEN_WIDTH, 4):
            y0 = int(80 + math.sin(t * 0.42 + x * 0.013) * 26)
            y1 = y0 + 36 + int(math.sin(t * 0.55 + x * 0.019) * 10)
            col = (90, 255, 185, int(44 * alt_t))
            pygame.draw.line(ribbon, col, (x, y0), (x, y1), 2)
        surface.blit(ribbon, (0, 0))

    sun_x = int(SCREEN_WIDTH * 0.83)
    sun_y = int(96 + math.sin(t * 0.25) * 7 - alt_t * 24)
    for radius, alpha in ((120, 36), (88, 52), (58, 84)):
        halo = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 240, 185, int(alpha * (1.0 - 0.45 * alt_t))), (radius + 2, radius + 2), radius)
        surface.blit(halo, (sun_x - radius - 2, sun_y - radius - 2))
    sun_color = _lerp_color((255, 247, 208), (196, 214, 255), alt_t)
    pygame.draw.circle(surface, sun_color, (sun_x, sun_y), 34)

    cam = game.camera_x
    bands = [
        {"speed": 0.06, "y": SCREEN_HEIGHT * 0.52, "amp": 20, "color": _lerp_color((152, 186, 218), (76, 102, 148), alt_t)},
        {"speed": 0.11, "y": SCREEN_HEIGHT * 0.58, "amp": 24, "color": _lerp_color((132, 170, 206), (68, 92, 136), alt_t)},
        {"speed": 0.19, "y": SCREEN_HEIGHT * 0.66, "amp": 34, "color": _lerp_color((108, 146, 184), (58, 78, 116), alt_t)},
    ]
    for band in bands:
        pts = []
        step = 70
        for sx in range(-step, SCREEN_WIDTH + step * 2, step):
            wx = sx + cam * band["speed"]
            y = band["y"] + math.sin(wx * 0.0065 + t * 0.14) * band["amp"] + math.sin(wx * 0.0125) * (band["amp"] * 0.35)
            pts.append((sx, int(y)))
        pts.append((SCREEN_WIDTH + step * 2, SCREEN_HEIGHT))
        pts.append((-step, SCREEN_HEIGHT))
        pygame.draw.polygon(surface, band["color"], pts)

    # Subtle atmospheric fog tint near horizon.
    fog = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    fog_alpha = int(60 * (1.0 - alt_t) + 16)
    pygame.draw.rect(fog, (220, 235, 255, fog_alpha), (0, int(SCREEN_HEIGHT * 0.62), SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.38)))
    surface.blit(fog, (0, 0))

    for sl in game.speed_lines:
        life_k = max(0.0, min(1.0, sl["life"] / max(1e-5, sl["max"])))
        alpha = int(120 * life_k)
        col = (230, 240, 255, alpha)
        streak = pygame.Surface((int(sl["len"]) + 3, 3), pygame.SRCALPHA)
        pygame.draw.line(streak, col, (0, 1), (int(sl["len"]), 1), 2)
        surface.blit(streak, (sl["x"], sl["y"]))


def draw_motion_effects_with_camera(game, surface):
    """Draw world-space trail and boost effects with camera offset."""
    off_x = game.camera_x
    off_y = game.camera_y

    for p in game.player_trail:
        life_k = max(0.0, min(1.0, p["life"] / max(1e-5, p["max"])))
        r = max(1, int(5 * life_k))
        alpha = int(150 * life_k)
        x = int(p["x"] - off_x)
        y = int(p["y"] - off_y)
        blob = pygame.Surface((r * 4 + 2, r * 4 + 2), pygame.SRCALPHA)
        pygame.draw.circle(blob, (212, 232, 252, alpha), (r * 2 + 1, r * 2 + 1), r * 2)
        surface.blit(blob, (x - (r * 2 + 1), y - (r * 2 + 1)))
        if r >= 2:
            pygame.draw.circle(surface, (238, 246, 255), (x, y), max(1, r - 1), 1)

    for bp in game.boost_particles:
        life_k = max(0.0, min(1.0, bp["life"] / max(1e-5, bp["max"])))
        x = int(bp["x"] - off_x)
        y = int(bp["y"] - off_y)
        size = max(1, int(5 * life_k))
        pygame.draw.circle(surface, (255, 172, 92), (x, y), size)
        if life_k > 0.45:
            pygame.draw.circle(surface, (255, 232, 175), (x, y), max(1, size - 1))
        if life_k < 0.50:
            smoke_alpha = int(90 * (1.0 - life_k))
            smoke = pygame.Surface((size * 4 + 4, size * 4 + 4), pygame.SRCALPHA)
            pygame.draw.circle(smoke, (150, 165, 188, smoke_alpha), (size * 2 + 2, size * 2 + 2), size * 2)
            surface.blit(smoke, (x - (size * 2 + 2), y - (size * 2 + 2)))

