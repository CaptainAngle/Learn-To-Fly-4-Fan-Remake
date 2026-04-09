import pygame

from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH


def draw_terrain_with_camera(game, surface):
    """Draw terrain with camera offset applied."""
    terrain = game.environment.terrain
    offset = game.camera_x
    offset_y = game.camera_y

    for cloud in terrain.clouds:
        cx = cloud["x"] - offset * 0.95
        cloud_world_y = terrain.get_ground_y_at(cloud["x"]) - cloud["terrain_gap"]
        cy = cloud_world_y - offset_y
        s = cloud["s"]
        if -120 < cx < SCREEN_WIDTH + 120:
            pygame.draw.circle(surface, (220, 225, 235), (int(cx + 1), int(cy + 1)), int(s * 1.05))
            pygame.draw.circle(surface, (250, 251, 255), (int(cx), int(cy)), s)
            pygame.draw.circle(surface, (250, 251, 255), (int(cx + s * 0.9), int(cy + s * 0.05)), int(s * 1.05))
            pygame.draw.circle(surface, (250, 251, 255), (int(cx - s * 0.8), int(cy + s * 0.05)), int(s * 0.85))
            pygame.draw.circle(surface, (255, 255, 255), (int(cx + s * 0.2), int(cy - s * 0.35)), int(s * 0.95))
            # Soft cloud base shading for thickness.
            pygame.draw.ellipse(surface, (230, 236, 245), (int(cx - s * 0.9), int(cy + s * 0.25), int(s * 1.8), int(s * 0.45)))

    if len(terrain.points) > 1:
        terrain_points = [(x - offset, y - offset_y) for x, y in terrain.points]
        terrain_points.append((game.environment.terrain.width - offset, SCREEN_HEIGHT * 2))
        terrain_points.append((0 - offset, SCREEN_HEIGHT * 2))
        pygame.draw.polygon(surface, (200, 215, 235), terrain_points)

    for i in range(len(terrain.points) - 1):
        x1, y1 = terrain.points[i]
        x2, y2 = terrain.points[i + 1]
        mid_x = (x1 + x2) * 0.5
        mat = terrain.get_surface_type_at(mid_x)
        if mat == "ice":
            top_color = (150, 210, 250)
            edge_color = (210, 240, 255)
            width = 6
        elif mat == "snow":
            top_color = (250, 251, 255)
            edge_color = (240, 245, 255)
            width = 8
        else:
            continue

        pygame.draw.line(surface, top_color, (x1 - offset, y1 - offset_y), (x2 - offset, y2 - offset_y), width)
        pygame.draw.line(surface, edge_color, (x1 - offset, y1 - offset_y), (x2 - offset, y2 - offset_y), 2)
        pygame.draw.line(surface, (200, 220, 240), (x1 - offset, y1 - offset_y + 2), (x2 - offset, y2 - offset_y + 2), 1)

        seg_len = max(1.0, ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
        mark_step = 22 if mat == "snow" else 22
        mark_count = int(seg_len // mark_step)
        for j in range(mark_count + 1):
            t = 0 if mark_count == 0 else j / max(1, mark_count)
            mx = x1 + (x2 - x1) * t
            my = y1 + (y2 - y1) * t

            if mat == "snow":
                seed = int(mx * 0.37 + my * 1.91 + j * 13 + i * 101)
                rand_a = ((seed * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF
                rand_b = (((seed + 77) * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF
                rand_c = (((seed + 173) * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF

                jitter_x = -4 + int(rand_c * 9)
                start_x = mx - offset + jitter_x
                start_y = my - offset_y + 2 + int(rand_a * 3)

                depth = 14 + int(rand_b * 34)
                drift = -2 + int(rand_a * 5)

                end_x = start_x + drift
                end_y = start_y + depth

                color = (218, 226, 236) if rand_b > 0.5 else (230, 236, 244)
                pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), 1)

                if rand_c > 0.62:
                    sx2 = start_x + 2
                    sy2 = start_y + 3
                    ex2 = sx2 + max(-1, drift - 1)
                    ey2 = sy2 + max(8, depth - 8)
                    pygame.draw.line(surface, (235, 240, 247), (sx2, sy2), (ex2, ey2), 1)
            else:
                pygame.draw.line(
                    surface,
                    (170, 225, 245),
                    (mx - offset - 3, my - offset_y - 1),
                    (mx - offset + 3, my - offset_y + 1),
                    1,
                )
                seed = int(mx * 0.37 + my * 1.91 + j * 13 + i * 101)
                rand_d = ((seed * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF
                if rand_d > 0.7:
                    pygame.draw.line(surface, (190, 235, 252), (mx - offset, my - offset_y - 2), (mx - offset + 1, my - offset_y + 2), 1)

    for i in range(len(terrain.points) - 1):
        x1, y1 = terrain.points[i]
        x2, y2 = terrain.points[i + 1]
        pygame.draw.line(surface, (150, 165, 185), (x1 - offset, y1 - offset_y), (x2 - offset, y2 - offset_y), 2)

    for i in range(len(terrain.points) - 1):
        x1, y1 = terrain.points[i]
        x2, y2 = terrain.points[i + 1]
        mid_x = (x1 + x2) * 0.5
        if terrain.get_surface_type_at(mid_x) == "ice":
            pygame.draw.line(surface, (190, 235, 255), (x1 - offset, y1 - offset_y - 4), (x2 - offset, y2 - offset_y - 4), 1)

    for p in terrain.wind_particles:
        if -50 < p["x"] - offset < SCREEN_WIDTH + 50:
            size = max(1, int(2 * (p["life"] / 30)))
            pygame.draw.circle(surface, (200, 220, 240), (int(p["x"] - offset), int(p["y"] - offset_y)), size)

    for hazard in game.environment.hazards:
        if hazard.destroyed:
            continue
        hazard_screen_x = hazard.x - offset
        hazard_screen_y = hazard.y - offset_y
        if -180 < hazard_screen_x < SCREEN_WIDTH + 180:
            size_boost = 1.0
            base_w = max(40, int(hazard.width * size_boost))
            base_h = max(60, int(hazard.height * size_boost))
            hp_ratio = max(0.0, min(1.0, hazard.hp / max(1.0, hazard.max_hp)))
            # Ground contact shadow for depth/readability.
            shadow_w = int(base_w * 0.85)
            shadow_h = max(8, int(base_h * 0.12))
            pygame.draw.ellipse(surface, (120, 135, 155), (int(hazard_screen_x - shadow_w * 0.5), int(hazard_screen_y - shadow_h * 0.35), shadow_w, shadow_h))

            if hazard.type == "snowman":
                body_r = max(22, int(base_h * 0.24))
                head_r = max(16, int(base_h * 0.17))
                body_y = int(hazard_screen_y - body_r)
                head_y = int(body_y - body_r - head_r + 8)
                pygame.draw.circle(surface, (250, 252, 255), (int(hazard_screen_x), body_y), body_r)
                pygame.draw.circle(surface, (250, 252, 255), (int(hazard_screen_x), head_y), head_r)
                pygame.draw.circle(surface, (232, 240, 248), (int(hazard_screen_x - body_r * 0.25), int(body_y - body_r * 0.2)), int(body_r * 0.6))
                pygame.draw.circle(surface, (35, 40, 45), (int(hazard_screen_x - head_r * 0.3), int(head_y - head_r * 0.25)), max(2, head_r // 6))
                pygame.draw.circle(surface, (35, 40, 45), (int(hazard_screen_x + head_r * 0.3), int(head_y - head_r * 0.25)), max(2, head_r // 6))
                pygame.draw.polygon(surface, (255, 140, 30), [
                    (hazard_screen_x + 1, head_y - 1),
                    (hazard_screen_x + head_r, head_y + 1),
                    (hazard_screen_x + 1, head_y + 3),
                ])
                # Coal buttons
                for bi in range(3):
                    pygame.draw.circle(surface, (30, 34, 38), (int(hazard_screen_x), int(body_y - body_r * 0.45 + bi * body_r * 0.35)), max(2, head_r // 8))
            elif hazard.type == "snowmound":
                w = max(100, int(base_w))
                h = max(70, int(base_h * 0.50))
                mound_pts = [
                    (hazard_screen_x - int(w * 0.55), hazard_screen_y),
                    (hazard_screen_x - int(w * 0.42), hazard_screen_y - int(h * 0.22)),
                    (hazard_screen_x - int(w * 0.25), hazard_screen_y - int(h * 0.44)),
                    (hazard_screen_x - int(w * 0.08), hazard_screen_y - int(h * 0.70)),
                    (hazard_screen_x + int(w * 0.14), hazard_screen_y - int(h * 0.78)),
                    (hazard_screen_x + int(w * 0.34), hazard_screen_y - int(h * 0.56)),
                    (hazard_screen_x + int(w * 0.50), hazard_screen_y - int(h * 0.28)),
                    (hazard_screen_x + int(w * 0.62), hazard_screen_y),
                ]
                pygame.draw.polygon(surface, (236, 243, 252), mound_pts)
                # Packed-snow inner shading.
                inner_pts = [
                    (hazard_screen_x - int(w * 0.42), hazard_screen_y),
                    (hazard_screen_x - int(w * 0.30), hazard_screen_y - int(h * 0.16)),
                    (hazard_screen_x - int(w * 0.08), hazard_screen_y - int(h * 0.44)),
                    (hazard_screen_x + int(w * 0.12), hazard_screen_y - int(h * 0.56)),
                    (hazard_screen_x + int(w * 0.30), hazard_screen_y - int(h * 0.38)),
                    (hazard_screen_x + int(w * 0.42), hazard_screen_y),
                ]
                pygame.draw.polygon(surface, (224, 233, 245), inner_pts)
                # Crisp top ridge and tiny contour grooves.
                pygame.draw.lines(surface, (248, 252, 255), False, mound_pts[1:-1], 2)
                for gi in range(4):
                    gx0 = hazard_screen_x - int(w * 0.30) + gi * int(w * 0.16)
                    gy0 = hazard_screen_y - int(h * (0.20 + 0.08 * (gi % 2)))
                    gx1 = gx0 + int(w * 0.11)
                    gy1 = gy0 - int(h * 0.08)
                    pygame.draw.line(surface, (210, 222, 238), (gx0, gy0), (gx1, gy1), 1)
            elif hazard.type == "rocky_hill":
                rx = int(base_w * 0.50)
                ry = int(base_h * 0.70)
                pygame.draw.polygon(surface, (120, 125, 132), [
                    (hazard_screen_x - rx, hazard_screen_y),
                    (hazard_screen_x - int(rx * 0.42), hazard_screen_y - int(ry * 0.78)),
                    (hazard_screen_x + int(rx * 0.15), hazard_screen_y - ry),
                    (hazard_screen_x + rx, hazard_screen_y),
                ])
                pygame.draw.line(surface, (148, 156, 168), (hazard_screen_x - int(rx * 0.3), hazard_screen_y - int(ry * 0.52)), (hazard_screen_x + int(rx * 0.36), hazard_screen_y - int(ry * 0.2)), 2)
            elif hazard.type == "iceberg":
                ix = int(base_w * 0.50)
                iy = int(base_h * 0.75)
                pygame.draw.polygon(surface, (170, 220, 250), [
                    (hazard_screen_x - int(ix * 0.86), hazard_screen_y),
                    (hazard_screen_x - int(ix * 0.5), hazard_screen_y - int(iy * 0.72)),
                    (hazard_screen_x + int(ix * 0.12), hazard_screen_y - iy),
                    (hazard_screen_x + int(ix * 0.8), hazard_screen_y - int(iy * 0.5)),
                    (hazard_screen_x + ix, hazard_screen_y),
                ])
                pygame.draw.polygon(surface, (210, 242, 255), [
                    (hazard_screen_x - int(ix * 0.26), hazard_screen_y - int(iy * 0.58)),
                    (hazard_screen_x + int(ix * 0.13), hazard_screen_y - int(iy * 0.84)),
                    (hazard_screen_x + int(ix * 0.45), hazard_screen_y - int(iy * 0.54)),
                ])
            elif hazard.type == "glacier_wall":
                ww = int(base_w)
                hh = int(base_h)
                pygame.draw.rect(surface, (150, 195, 235), (hazard_screen_x - ww // 2, hazard_screen_y - hh, ww, hh), border_radius=8)
                pygame.draw.rect(surface, (200, 236, 255), (hazard_screen_x - int(ww * 0.43), hazard_screen_y - int(hh * 0.96), int(ww * 0.30), int(hh * 0.92)), border_radius=4)
                pygame.draw.rect(surface, (182, 224, 248), (hazard_screen_x - int(ww * 0.08), hazard_screen_y - int(hh * 0.96), int(ww * 0.25), int(hh * 0.92)), border_radius=4)
                pygame.draw.rect(surface, (205, 240, 255), (hazard_screen_x + int(ww * 0.22), hazard_screen_y - int(hh * 0.96), int(ww * 0.24), int(hh * 0.92)), border_radius=4)

            # Damage cracks to communicate remaining HP visually.
            if hp_ratio < 0.95:
                crack_count = int((1.0 - hp_ratio) * 8) + 1
                for ci in range(crack_count):
                    cx = int(hazard_screen_x - hazard.width * 0.45 * size_boost + ci * (hazard.width * 0.9 * size_boost / max(1, crack_count)))
                    cy = int(hazard_screen_y - base_h * 0.7 + (ci % 3) * 18)
                    pygame.draw.line(surface, (88, 104, 126), (cx, cy), (cx + 10, cy + 18), 2)
                    pygame.draw.line(surface, (88, 104, 126), (cx + 10, cy + 18), (cx + 4, cy + 30), 2)

            bar_w = max(60, int(base_w * 1.08))
            bar_x = int(hazard_screen_x - bar_w * 0.5)
            bar_y = int(hazard_screen_y - base_h - 26)
            pygame.draw.rect(surface, (40, 45, 55), (bar_x, bar_y, bar_w, 7), border_radius=3)
            pygame.draw.rect(surface, (255, 125, 95), (bar_x, bar_y, int(bar_w * hp_ratio), 7), border_radius=3)
            pygame.draw.rect(surface, (235, 235, 240), (bar_x, bar_y, bar_w, 7), 1, border_radius=3)
            label = game.ui_manager.font_small.render(hazard.name, True, (235, 242, 250))
            surface.blit(label, (bar_x, bar_y - 16))

