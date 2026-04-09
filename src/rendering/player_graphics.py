import math
from types import SimpleNamespace

import pygame

from src.constants import BOOSTER_TIERS, PAYLOAD_TIERS, SCREEN_WIDTH, SLED_TIERS

_SPRITE_CACHE = {}


def _build_player_sprite(size):
    cached = _SPRITE_CACHE.get(size)
    if cached is not None:
        return cached

    sprite = pygame.Surface((size * 4, size * 3), pygame.SRCALPHA)
    body = pygame.Rect(0, 0, int(size * 3.45), int(size * 1.5))
    body.center = (int(size * 2.0), int(size * 1.5))

    cx_body = body.x + body.w * 0.5
    cy_body = body.y + body.h * 0.5
    rx = body.w * 0.5
    ry = body.h * 0.5

    half_body = [(cx_body, cy_body - ry)]
    for i in range(23):
        t = -math.pi / 2 + (math.pi * i / 22)
        half_body.append((cx_body + rx * math.cos(t), cy_body + ry * math.sin(t)))
    half_body.append((cx_body, cy_body + ry))

    pygame.draw.polygon(sprite, (20, 26, 35), half_body)
    pygame.draw.polygon(
        sprite,
        (8, 12, 18),
        [
            (cx_body - size * 0.08, cy_body - ry),
            (cx_body, cy_body - ry),
            (cx_body, cy_body + ry),
            (cx_body - size * 0.08, cy_body + ry),
        ],
    )

    for i in range(8):
        tx0 = cx_body + size * (0.10 + i * 0.19)
        ty0 = cy_body - ry * (0.60 - i * 0.08)
        tx1 = tx0 + size * 0.30
        ty1 = ty0 + size * 0.21
        pygame.draw.line(sprite, (34, 44, 56), (tx0, ty0), (tx1, ty1), 1)

    pygame.draw.ellipse(
        sprite,
        (235, 240, 246),
        (cx_body + size * 0.40, cy_body + size * 0.00, size * 1.30, size * 0.66),
    )
    pygame.draw.ellipse(
        sprite,
        (255, 255, 255),
        (cx_body + size * 0.54, cy_body + size * 0.06, size * 0.74, size * 0.28),
    )
    pygame.draw.ellipse(
        sprite,
        (205, 215, 225),
        (cx_body + size * 0.68, cy_body + size * 0.20, size * 0.72, size * 0.30),
    )

    pygame.draw.ellipse(sprite, (18, 23, 32), (cx_body + size * 0.32, cy_body + size * 0.08, size * 0.88, size * 0.32))
    pygame.draw.ellipse(sprite, (28, 36, 48), (cx_body + size * 0.54, cy_body + size * 0.20, size * 0.54, size * 0.20))

    beak = [
        (cx_body + rx * 0.96, cy_body - size * 0.10),
        (cx_body + rx * 1.38, cy_body),
        (cx_body + rx * 0.96, cy_body + size * 0.10),
    ]
    pygame.draw.polygon(sprite, (255, 155, 20), beak)
    pygame.draw.polygon(
        sprite,
        (210, 118, 6),
        [
            (cx_body + rx * 0.96, cy_body - size * 0.10),
            (cx_body + rx * 1.20, cy_body - size * 0.02),
            (cx_body + rx * 0.96, cy_body + size * 0.04),
        ],
    )

    eye_x = int(cx_body + rx * 0.60)
    eye_y = int(cy_body - ry * 0.28)
    pygame.draw.circle(sprite, (255, 255, 255), (eye_x, eye_y), int(size * 0.13))
    pygame.draw.circle(sprite, (12, 12, 22), (eye_x + int(size * 0.03), eye_y - int(size * 0.01)), int(size * 0.06))
    pygame.draw.circle(sprite, (255, 255, 255), (eye_x + int(size * 0.05), eye_y - int(size * 0.03)), int(size * 0.02))

    feet_w = size * 0.68
    feet_h = size * 0.24
    foot_a = (cx_body - size * 0.14, cy_body + ry - size * 0.70)
    foot_b = (cx_body - size * 0.55, cy_body + ry - size * 0.67)
    dx = foot_b[0] - foot_a[0]
    dy = foot_b[1] - foot_a[1]
    foot_b = (foot_a[0] + dy, foot_a[1] - dx)

    for fx, fy in (foot_a, foot_b):
        pygame.draw.ellipse(sprite, (255, 168, 24), (fx - feet_w / 2, fy - feet_h / 2, feet_w, feet_h))
        pygame.draw.ellipse(sprite, (225, 128, 8), (fx - feet_w * 0.22, fy - feet_h * 0.10, feet_w * 0.44, feet_h * 0.35))

    _SPRITE_CACHE[size] = sprite
    return sprite


def _draw_sled(canvas, cx, cy, size, player, gear_scale):
    if (not player.sled_attached) or player.sled not in SLED_TIERS:
        return
    sled_color = {
        "the_plank": (142, 95, 50),
        "plank_mk2": (126, 81, 40),
        "good_ol_sled": (116, 68, 32),
        "bobsled": (64, 98, 142),
    }[player.sled]
    pygame.draw.ellipse(canvas, sled_color, (cx - size * 0.74 * gear_scale, cy + size * 0.72 * gear_scale, size * 1.60 * gear_scale, size * 0.29 * gear_scale))
    pygame.draw.ellipse(canvas, tuple(min(c + 36, 255) for c in sled_color), (cx - size * 0.72 * gear_scale, cy + size * 0.73 * gear_scale, size * 1.44 * gear_scale, size * 0.10 * gear_scale))
    pygame.draw.line(canvas, (68, 78, 90), (cx - size * 0.64 * gear_scale, cy + size * 0.86 * gear_scale), (cx + size * 0.72 * gear_scale, cy + size * 0.86 * gear_scale), 1)


def _draw_glider(canvas, cx, cy, size, player, gear_scale):
    if player.glider == "kite":
        mast_base = (cx - size * 0.03 * gear_scale, cy + size * 0.02 * gear_scale)
        mast_top = (cx - size * 0.05 * gear_scale, cy - size * 0.24 * gear_scale)
        pygame.draw.line(canvas, (126, 126, 130), mast_base, mast_top, 2)

        kite_x = mast_top[0]
        kite_y = mast_top[1] - size * 0.03 * gear_scale
        kite_w = size * 0.74 * gear_scale
        kite_h = size * 0.12 * gear_scale
        slant = size * 0.15 * gear_scale

        pygame.draw.polygon(canvas, (70, 184, 110), [
            (kite_x - kite_w * 0.5 + slant, kite_y - kite_h * 0.5),
            (kite_x + kite_w * 0.5 + slant, kite_y - kite_h * 0.5),
            (kite_x + kite_w * 0.5 - slant, kite_y + kite_h * 0.5),
            (kite_x - kite_w * 0.5 - slant, kite_y + kite_h * 0.5),
        ])
        pygame.draw.line(canvas, (170, 240, 186), (kite_x - kite_w * 0.44 + slant, kite_y - kite_h * 0.14), (kite_x + kite_w * 0.44 + slant, kite_y - kite_h * 0.14), 2)
        return

    if player.glider not in ("old_glider", "hand_glider"):
        return

    if player.glider == "old_glider":
        wing_len = 0.98
        wing_thickness = 0.10
        mast_h = 0.62
        color_main = (88, 124, 165)
        color_high = (194, 228, 255)
        color_shadow = (56, 84, 122)
    else:
        wing_len = 1.22
        wing_thickness = 0.11
        mast_h = 0.68
        color_main = (84, 136, 188)
        color_high = (206, 236, 255)
        color_shadow = (50, 76, 112)

    mast_base = (cx - size * 0.12 * gear_scale, cy + size * 0.05 * gear_scale)
    mast_top = (cx - size * 0.18 * gear_scale, cy - size * (mast_h - 0.28) * gear_scale)
    pygame.draw.line(canvas, (126, 126, 130), mast_base, mast_top, 2)

    wing_x = mast_top[0]
    wing_y = mast_top[1] + size * 0.18 * gear_scale
    shadow_poly = [
        (wing_x + size * 0.14 * gear_scale, wing_y - size * wing_thickness * gear_scale + 1),
        (wing_x - size * wing_len * gear_scale + 1, wing_y - size * (wing_thickness * 0.55) * gear_scale + 1),
        (wing_x - size * (wing_len - 0.20) * gear_scale, wing_y + size * wing_thickness * gear_scale + 1),
        (wing_x + size * 0.11 * gear_scale, wing_y + size * (wing_thickness * 0.72) * gear_scale + 1),
    ]
    main_poly = [
        (wing_x + size * 0.12 * gear_scale, wing_y - size * wing_thickness * gear_scale),
        (wing_x - size * wing_len * gear_scale, wing_y - size * (wing_thickness * 0.55) * gear_scale),
        (wing_x - size * (wing_len - 0.20) * gear_scale, wing_y + size * wing_thickness * gear_scale),
        (wing_x + size * 0.09 * gear_scale, wing_y + size * (wing_thickness * 0.72) * gear_scale),
    ]
    pygame.draw.polygon(canvas, color_shadow, shadow_poly)
    pygame.draw.polygon(canvas, color_main, main_poly)
    pygame.draw.line(canvas, color_high, (wing_x + size * 0.08 * gear_scale, wing_y - size * (wing_thickness * 0.2) * gear_scale), (wing_x - size * (wing_len - 0.15) * gear_scale, wing_y - size * (wing_thickness * 0.04) * gear_scale), 2)
    pygame.draw.line(canvas, (126, 126, 130), (cx + size * 0.14 * gear_scale, cy + size * 0.10 * gear_scale), (wing_x + size * 0.03 * gear_scale, wing_y + size * 0.02 * gear_scale), 1)


def _draw_payload(canvas, cx, cy, size, player, gear_scale):
    payload_key = player.payload
    if payload_key not in PAYLOAD_TIERS:
        return

    ptype = PAYLOAD_TIERS[payload_key].get("payload_type")
    if ptype == "regular":
        fill = {
            "sand": (216, 194, 128),
            "iron_pellets": (145, 152, 164),
            "cast_iron": (108, 114, 126),
            "osmium": (82, 102, 132),
        }.get(payload_key, (145, 145, 145))
        pack_x = cx - size * 0.58 * gear_scale
        pack_y = cy + size * 0.18 * gear_scale
        pack_w = size * 0.48 * gear_scale
        pack_h = size * 0.34 * gear_scale
        pygame.draw.rect(canvas, fill, (pack_x, pack_y, pack_w, pack_h), border_radius=4)
        pygame.draw.rect(canvas, (235, 240, 246), (pack_x + size * 0.04 * gear_scale, pack_y + size * 0.04 * gear_scale, pack_w * 0.50, pack_h * 0.22), border_radius=2)
        pygame.draw.line(canvas, (108, 118, 130), (pack_x + pack_w, pack_y + size * 0.06 * gear_scale), (cx - size * 0.04 * gear_scale, cy + size * 0.08 * gear_scale), 2)
        pygame.draw.line(canvas, (108, 118, 130), (pack_x + pack_w, pack_y + pack_h - size * 0.06 * gear_scale), (cx - size * 0.04 * gear_scale, cy + size * 0.22 * gear_scale), 2)
        return

    body = {
        "dyna_might": (178, 80, 62),
        "c4": (132, 148, 124),
    }.get(payload_key, (136, 188, 104))
    pack_x = cx - size * 0.62 * gear_scale
    pack_y = cy + size * 0.16 * gear_scale
    pack_w = size * 0.54 * gear_scale
    pack_h = size * 0.30 * gear_scale
    pygame.draw.rect(canvas, body, (pack_x, pack_y, pack_w, pack_h), border_radius=4)
    pygame.draw.circle(canvas, (244, 206, 96), (int(pack_x + pack_w - size * 0.02 * gear_scale), int(pack_y + pack_h * 0.5)), int(size * 0.05 * gear_scale))
    pygame.draw.line(canvas, (244, 206, 96), (pack_x + pack_w - size * 0.02 * gear_scale, pack_y + pack_h * 0.5), (pack_x + pack_w + size * 0.08 * gear_scale, pack_y + pack_h * 0.2), 2)


def _draw_booster(canvas, cx, cy, size, player, gear_scale):
    gear = player.booster
    nozzle_pos = None

    if gear == "sugar_rocket":
        body_x = cx - size * 0.78 * gear_scale
        body_y = cy - size * 0.02 * gear_scale
        body_w = size * 0.88 * gear_scale
        body_h = size * 0.24 * gear_scale
        pygame.draw.rect(canvas, (200, 208, 222), (body_x, body_y, body_w, body_h), border_radius=5)
        pygame.draw.rect(canvas, (238, 243, 250), (body_x + size * 0.09 * gear_scale, body_y + size * 0.03 * gear_scale, body_w * 0.55, body_h * 0.28), border_radius=3)
        pygame.draw.polygon(canvas, (205, 84, 84), [(body_x + body_w, body_y + body_h * 0.5), (body_x + body_w + size * 0.16 * gear_scale, body_y + body_h * 0.3), (body_x + body_w + size * 0.16 * gear_scale, body_y + body_h * 0.7)])
        pygame.draw.polygon(canvas, (178, 66, 66), [(body_x + size * 0.08 * gear_scale, body_y + body_h * 0.02), (body_x - size * 0.10 * gear_scale, body_y - size * 0.07 * gear_scale), (body_x + size * 0.12 * gear_scale, body_y + body_h * 0.38)])
        pygame.draw.polygon(canvas, (178, 66, 66), [(body_x + size * 0.08 * gear_scale, body_y + body_h * 0.98), (body_x - size * 0.10 * gear_scale, body_y + body_h + size * 0.07 * gear_scale), (body_x + size * 0.12 * gear_scale, body_y + body_h * 0.62)])
        pygame.draw.rect(canvas, (94, 102, 118), (body_x - size * 0.10 * gear_scale, body_y + body_h * 0.30, size * 0.11 * gear_scale, body_h * 0.40), border_radius=2)
        pygame.draw.line(canvas, (96, 102, 114), (cx - size * 0.10 * gear_scale, cy + size * 0.05 * gear_scale), (body_x + size * 0.18 * gear_scale, body_y + body_h * 0.25), 2)
        pygame.draw.line(canvas, (96, 102, 114), (cx - size * 0.10 * gear_scale, cy + size * 0.21 * gear_scale), (body_x + size * 0.18 * gear_scale, body_y + body_h * 0.75), 2)
        nozzle_pos = (body_x - size * 0.10 * gear_scale, body_y + body_h * 0.5)

    elif gear == "pulse_jet":
        tube_x = cx - size * 1.04 * gear_scale
        tube_y = cy + size * 0.03 * gear_scale
        tube_w = size * 1.22 * gear_scale
        tube_h = size * 0.14 * gear_scale
        pygame.draw.rect(canvas, (98, 106, 124), (tube_x, tube_y, tube_w, tube_h), border_radius=3)
        pygame.draw.rect(canvas, (146, 156, 176), (tube_x + size * 0.08 * gear_scale, tube_y + size * 0.02 * gear_scale, tube_w * 0.65, tube_h * 0.24), border_radius=2)
        intake_x = tube_x + tube_w - size * 0.02 * gear_scale
        intake_y = tube_y - size * 0.03 * gear_scale
        intake_w = size * 0.30 * gear_scale
        intake_h = size * 0.20 * gear_scale
        pygame.draw.ellipse(canvas, (124, 136, 154), (intake_x, intake_y, intake_w, intake_h))
        pygame.draw.ellipse(canvas, (76, 84, 99), (intake_x + size * 0.04 * gear_scale, intake_y + size * 0.03 * gear_scale, intake_w * 0.66, intake_h * 0.66))
        pygame.draw.line(canvas, (96, 102, 114), (cx - size * 0.04 * gear_scale, cy + size * 0.05 * gear_scale), (tube_x + size * 0.36 * gear_scale, tube_y + tube_h * 0.2), 2)
        pygame.draw.line(canvas, (96, 102, 114), (cx - size * 0.04 * gear_scale, cy + size * 0.22 * gear_scale), (tube_x + size * 0.36 * gear_scale, tube_y + tube_h * 0.8), 2)
        nozzle_pos = (tube_x - size * 0.03 * gear_scale, tube_y + tube_h * 0.5)

    elif gear == "ramjet":
        nacelle_x = cx - size * 1.02 * gear_scale
        nacelle_y = cy - size * 0.03 * gear_scale
        nacelle_w = size * 1.10 * gear_scale
        nacelle_h = size * 0.24 * gear_scale
        pygame.draw.ellipse(canvas, (94, 108, 136), (nacelle_x, nacelle_y, nacelle_w, nacelle_h))
        pygame.draw.ellipse(canvas, (148, 172, 200), (nacelle_x + size * 0.11 * gear_scale, nacelle_y + size * 0.04 * gear_scale, nacelle_w * 0.44, nacelle_h * 0.25))
        intake_cx = nacelle_x + nacelle_w + size * 0.03 * gear_scale
        intake_cy = nacelle_y + nacelle_h * 0.5
        intake_r = size * 0.12 * gear_scale
        pygame.draw.circle(canvas, (170, 188, 210), (int(intake_cx), int(intake_cy)), int(intake_r))
        pygame.draw.circle(canvas, (66, 76, 92), (int(intake_cx), int(intake_cy)), int(intake_r * 0.58))
        pygame.draw.polygon(canvas, (80, 94, 116), [(nacelle_x - size * 0.20 * gear_scale, nacelle_y + nacelle_h * 0.35), (nacelle_x, nacelle_y + nacelle_h * 0.12), (nacelle_x, nacelle_y + nacelle_h * 0.88), (nacelle_x - size * 0.20 * gear_scale, nacelle_y + nacelle_h * 0.65)])
        pygame.draw.line(canvas, (96, 102, 114), (cx - size * 0.02 * gear_scale, cy + size * 0.08 * gear_scale), (nacelle_x + size * 0.34 * gear_scale, nacelle_y + nacelle_h * 0.3), 2)
        pygame.draw.line(canvas, (96, 102, 114), (cx - size * 0.02 * gear_scale, cy + size * 0.24 * gear_scale), (nacelle_x + size * 0.34 * gear_scale, nacelle_y + nacelle_h * 0.7), 2)
        nozzle_pos = (nacelle_x - size * 0.20 * gear_scale, nacelle_y + nacelle_h * 0.5)

    elif gear == "balloon":
        pod_x = cx - size * 1.05 * gear_scale
        pod_y = cy - size * 0.18 * gear_scale
        pod_w = size * 1.22 * gear_scale
        pod_h = size * 0.24 * gear_scale
        pygame.draw.ellipse(canvas, (98, 208, 120), (pod_x, pod_y, pod_w, pod_h))
        pygame.draw.ellipse(canvas, (176, 240, 188), (pod_x + size * 0.08 * gear_scale, pod_y + size * 0.04 * gear_scale, pod_w * 0.45, pod_h * 0.35))
        pygame.draw.ellipse(canvas, (68, 172, 90), (pod_x - 1, pod_y + 1, pod_w - 2, pod_h - 2), 2)
        pygame.draw.line(canvas, (134, 140, 154), (cx - size * 0.08 * gear_scale, cy + size * 0.04 * gear_scale), (cx - size * 0.32 * gear_scale, cy - size * 0.02 * gear_scale), 2)
        pygame.draw.line(canvas, (134, 140, 154), (cx - size * 0.08 * gear_scale, cy + size * 0.24 * gear_scale), (cx - size * 0.32 * gear_scale, cy + size * 0.12 * gear_scale), 2)
        pygame.draw.rect(canvas, (124, 128, 144), (pod_x - size * 0.08 * gear_scale, pod_y + size * 0.07 * gear_scale, size * 0.10 * gear_scale, size * 0.10 * gear_scale), border_radius=2)
        pygame.draw.rect(canvas, (154, 160, 176), (pod_x - size * 0.074 * gear_scale, pod_y + size * 0.074 * gear_scale, size * 0.06 * gear_scale, size * 0.06 * gear_scale), border_radius=1)
        nozzle_pos = (pod_x - size * 0.08 * gear_scale, pod_y + size * 0.12 * gear_scale)

    return nozzle_pos


def draw_equipment_overlay(surface, px, py, size, player, angle, gear_scale=3.5):
    canvas = pygame.Surface((size * 24, size * 24), pygame.SRCALPHA)
    cx = size * 12
    cy = size * 12

    _draw_sled(canvas, cx, cy, size, player, gear_scale)
    _draw_glider(canvas, cx, cy, size, player, gear_scale)
    _draw_payload(canvas, cx, cy, size, player, gear_scale)
    nozzle_pos = _draw_booster(canvas, cx, cy, size, player, gear_scale)

    if nozzle_pos is not None and player.is_thrusting:
        flicker = (pygame.time.get_ticks() // 45) % 5
        flame_len = size * gear_scale * (0.18 + 0.05 * flicker)
        flame_half = size * gear_scale * 0.06
        nx, ny = nozzle_pos
        pygame.draw.polygon(canvas, (255, 138, 62), [(nx, ny), (nx - flame_len, ny - flame_half), (nx - flame_len, ny + flame_half)])
        pygame.draw.polygon(canvas, (255, 222, 132), [(nx - size * gear_scale * 0.03, ny), (nx - flame_len * 0.58, ny - flame_half * 0.52), (nx - flame_len * 0.58, ny + flame_half * 0.52)])

    rotated_overlay = pygame.transform.rotozoom(canvas, angle, 1.0)
    surface.blit(rotated_overlay, rotated_overlay.get_rect(center=(px, py)))


def draw_player_with_camera(game, surface):
    offset = game.camera_x
    offset_y = game.camera_y
    size = int(game.player.size * 1.5)
    player_screen_x = game.player.x - offset
    player_screen_y = game.player.y - offset_y

    if not (-size * 2 < player_screen_x < SCREEN_WIDTH + size * 2):
        return

    shadow_w = int(size * 2.0)
    shadow_h = int(size * 0.42)
    pygame.draw.ellipse(
        surface,
        (120, 132, 152),
        (
            int(player_screen_x - shadow_w * 0.5),
            int(player_screen_y + size * 0.88),
            shadow_w,
            shadow_h,
        ),
    )

    sprite = _build_player_sprite(size)
    rotated = pygame.transform.rotozoom(sprite, game.player.angle, 1.0)
    rect = rotated.get_rect(center=(player_screen_x, player_screen_y))
    surface.blit(rotated, rect)
    draw_equipment_overlay(surface, player_screen_x, player_screen_y, size, game.player, game.player.angle)

    if game.player.fuel > 0:
        bar_width = 25
        bar_height = 5
        bar_x = player_screen_x - bar_width // 2
        bar_y = player_screen_y - size - 15

        pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))

        fuel_ratio = game.player.fuel / max(1.0, game.player.max_fuel)
        fuel_width = int(bar_width * fuel_ratio)
        fuel_color = (int(255 * (1 - fuel_ratio)), int(255 * fuel_ratio), 0)
        pygame.draw.rect(surface, fuel_color, (bar_x, bar_y, fuel_width, bar_height))

        pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)


def draw_catalog_icon(surface, category, key, rect):
    pygame.draw.rect(surface, (36, 52, 72), rect, border_radius=8)
    pygame.draw.rect(surface, (110, 150, 200), rect, 1, border_radius=8)

    icon_player = SimpleNamespace(
        size=8,
        angle=0,
        vx=0.0,
        is_thrusting=False,
        sled=key if category == "sled" else None,
        glider=key if category == "glider" else None,
        booster=key if category == "booster" else None,
        payload=key if category == "payload" else None,
        sled_attached=(category == "sled"),
    )

    icon = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    center_x = rect.width // 2
    center_y = rect.height // 2 + (4 if category == "sled" else 0)

    body = _build_player_sprite(7)
    body_scaled = pygame.transform.smoothscale(body, (int(body.get_width() * 0.48), int(body.get_height() * 0.48)))
    body_rect = body_scaled.get_rect(center=(center_x, center_y))
    icon.blit(body_scaled, body_rect)

    draw_equipment_overlay(icon, center_x, center_y, 6, icon_player, 0, gear_scale=1.18)
    surface.blit(icon, rect.topleft)


def draw_player_shop_preview(surface, player, panel_rect):
    pygame.draw.rect(surface, (22, 38, 56), panel_rect, border_radius=10)
    pygame.draw.rect(surface, (108, 152, 205), panel_rect, 1, border_radius=10)
    pygame.draw.rect(surface, (236, 242, 250), panel_rect, 2, border_radius=10)

    title_font = pygame.font.Font(None, 30)
    label = title_font.render("Current Loadout", True, (232, 240, 250))
    surface.blit(label, (panel_rect.x + 14, panel_rect.y + 10))

    px = panel_rect.centerx
    py = panel_rect.y + int(panel_rect.height * 0.63)
    size = 20

    shadow_w = int(size * 2.0)
    shadow_h = int(size * 0.38)
    pygame.draw.ellipse(
        surface,
        (110, 128, 150),
        (px - shadow_w // 2, py + int(size * 0.75), shadow_w, shadow_h),
    )

    body = _build_player_sprite(size)
    body_rot = pygame.transform.rotozoom(body, -8, 1.0)
    body_rect = body_rot.get_rect(center=(px, py))
    surface.blit(body_rot, body_rect)

    preview_player = SimpleNamespace(
        size=player.size,
        angle=-8,
        vx=player.vx,
        is_thrusting=player.is_thrusting,
        sled=player.sled,
        glider=player.glider,
        booster=player.booster,
        payload=player.payload,
        sled_attached=True,
    )
    draw_equipment_overlay(surface, px, py, size, preview_player, -8)

    stats_font = pygame.font.Font(None, 22)
    gear_line = " / ".join(
        [
            SLED_TIERS[player.sled]["name"] if player.sled in SLED_TIERS else "No Sled",
            player.glider.replace("_", " ").title() if player.glider else "No Glider",
            BOOSTER_TIERS[player.booster]["name"] if player.booster in BOOSTER_TIERS else "No Booster",
            PAYLOAD_TIERS[player.payload]["name"] if player.payload in PAYLOAD_TIERS else "No Payload",
        ]
    )
    gear_line = gear_line[:58] + "..." if len(gear_line) > 61 else gear_line
    text = stats_font.render(gear_line, True, (188, 210, 232))
    text_rect = text.get_rect(center=(panel_rect.centerx, panel_rect.bottom - 18))
    surface.blit(text, text_rect)



