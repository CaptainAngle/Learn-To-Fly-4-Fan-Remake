import math
import pygame
from src.constants import *


class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color if color != (100, 100, 100) else (80, 110, 150)
        self.text_color = text_color
        self.hovered = False
    
    def update(self, mouse_pos):
        """Update button state based on mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface, font):
        """Draw button."""
        color = tuple(min(c + 30, 255) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        # Button shadow
        pygame.draw.rect(surface, (50, 50, 70), (self.rect.x + 2, self.rect.y + 2, self.rect.width, self.rect.height), 0)
        # Button border with accent color
        border_color = (255, 160, 100) if self.hovered else (255, 200, 150)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)
        
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def is_clicked(self, mouse_pos, mouse_clicked):
        """Check if button is clicked."""
        return self.hovered and mouse_clicked


class UIManager:
    def __init__(self):
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 48)
    
    def draw_text(self, surface, text, font, color, x, y):
        """Draw text on surface."""
        text_surf = font.render(text, True, color)
        surface.blit(text_surf, (x, y))

    def draw_toast(self, surface, text, color=(225, 235, 248)):
        """Draw a centered transient notification panel."""
        panel_w = min(640, max(260, 24 + len(text) * 8))
        panel_h = 44
        x = (SCREEN_WIDTH - panel_w) // 2
        y = 18
        pygame.draw.rect(surface, (22, 34, 48), (x, y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(surface, (100, 150, 200), (x, y, panel_w, panel_h), 1, border_radius=10)
        pygame.draw.rect(surface, (245, 245, 250), (x, y, panel_w, panel_h), 2, border_radius=10)
        text_surf = self.font_medium.render(text, True, color)
        text_rect = text_surf.get_rect(center=(x + panel_w // 2, y + panel_h // 2))
        surface.blit(text_surf, text_rect)

    def draw_controls_hint(self, surface):
        """Draw a short in-flight controls reminder."""
        panel = pygame.Rect(16, SCREEN_HEIGHT - 78, 260, 58)
        pygame.draw.rect(surface, (20, 35, 50), panel, border_radius=8)
        pygame.draw.rect(surface, (100, 150, 200), panel, 1, border_radius=8)
        pygame.draw.rect(surface, (245, 245, 250), panel, 2, border_radius=8)
        self.draw_text(surface, "Controls", self.font_small, (220, 235, 248), panel.x + 10, panel.y + 8)
        self.draw_text(surface, "A/D rotate    W/SPACE boost", self.font_small, (190, 215, 238), panel.x + 10, panel.y + 30)
    
    def draw_stats(self, surface, player, environment):
        """Draw in-game stats."""
        wind_direction = "→" if environment.terrain.wind_speed > 0 else "←" if environment.terrain.wind_speed < 0 else "·"
        stats_text = [
            f"Distance: {int(player.distance_traveled)} m",
            f"Fuel: {int(player.fuel)}/{int(player.max_fuel)}",
            f"Sled: {SLED_TIERS[player.sled]['name'] if player.sled in SLED_TIERS else 'None'}",
            f"Glider: {GLIDER_TIERS[player.glider]['name'] if player.glider in GLIDER_TIERS else 'None'}",
            f"Booster: {BOOSTER_TIERS[player.booster]['name'] if player.booster in BOOSTER_TIERS else 'None'}",
            f"Coins: {player.coins}",
            f"Wind: {wind_direction} {abs(environment.terrain.wind_speed):.2f}",
        ]
        
        y = 10
        for stat in stats_text:
            self.draw_text(surface, stat, self.font_small, COLOR_TEXT, 10, y)
            y += 25
    
    def draw_mission_progress(self, surface, player, mission):
        """Draw mission progress bar at the bottom."""
        if not mission:
            return
        
        # Progress bar dimensions
        bar_width = 300
        bar_height = 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = SCREEN_HEIGHT - 40
        
        progress = min(1.0, player.distance_traveled / mission.target_value)
        
        # Draw background
        pygame.draw.rect(surface, (80, 90, 110), (bar_x, bar_y, bar_width, bar_height))
        # Shadow
        pygame.draw.rect(surface, (50, 55, 70), (bar_x + 1, bar_y + 1, bar_width - 2, bar_height - 2))
        
        # Draw progress
        progress_width = int(bar_width * progress)
        if progress >= 1.0:
            color = (100, 200, 100)  # Green when complete
        else:
            color = (255, 140, 60)  # Orange while progressing
        pygame.draw.rect(surface, color, (bar_x, bar_y, progress_width, bar_height))
        
        # Draw border
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Draw text
        progress_text = f"{int(player.distance_traveled)}/{mission.target_value} m"
        text_surf = self.font_small.render(progress_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height // 2))
        surface.blit(text_surf, text_rect)

    def draw_flight_hud(self, surface, player, terrain_y):
        """Draw lower-right HUD with a speed dial and an altimeter."""
        panel_w = 220
        panel_h = 150
        panel_x = SCREEN_WIDTH - panel_w - 18
        panel_y = SCREEN_HEIGHT - panel_h - 18

        # Panel background.
        pygame.draw.rect(surface, (20, 35, 50), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(surface, (100, 150, 200), (panel_x, panel_y, panel_w, panel_h), 1, border_radius=10)
        pygame.draw.rect(surface, (245, 245, 250), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        # Speed dial.
        dial_cx = panel_x + 70
        dial_cy = panel_y + 75
        dial_r = 46
        pygame.draw.circle(surface, (30, 40, 50), (dial_cx, dial_cy), dial_r)
        pygame.draw.circle(surface, (100, 150, 200), (dial_cx, dial_cy), dial_r, 1)
        pygame.draw.circle(surface, (245, 245, 250), (dial_cx, dial_cy), dial_r, 2)

        # Tick marks.
        for i in range(0, 9):
            ang = math.radians(210 - i * 22.5)
            inner = dial_r - 6
            outer = dial_r - (2 if i % 2 == 0 else 0)
            x1 = dial_cx + math.cos(ang) * inner
            y1 = dial_cy - math.sin(ang) * inner
            x2 = dial_cx + math.cos(ang) * outer
            y2 = dial_cy - math.sin(ang) * outer
            pygame.draw.line(surface, (160, 190, 220), (x1, y1), (x2, y2), 2)

        # Speed value mapped to dial (px/frame to approx m/s).
        speed_px = math.hypot(player.vx, player.vy)
        speed_mps = speed_px * 60 / PIXELS_PER_METER
        speed_max = 180.0
        speed_pct = min(1.0, speed_mps / speed_max)
        needle_ang = math.radians(210 - 180 * speed_pct)
        needle_len = dial_r - 10
        nx = dial_cx + math.cos(needle_ang) * needle_len
        ny = dial_cy - math.sin(needle_ang) * needle_len
        pygame.draw.line(surface, (255, 160, 100), (dial_cx, dial_cy), (nx, ny), 4)
        pygame.draw.circle(surface, (255, 160, 100), (dial_cx, dial_cy), 5)

        speed_label = self.font_small.render("SPEED", True, (230, 235, 240))
        surface.blit(speed_label, (panel_x + 20, panel_y + 10))
        speed_val = self.font_medium.render(f"{speed_mps:0.1f}", True, (255, 255, 255))
        speed_unit = self.font_small.render("m/s", True, (200, 220, 240))
        surface.blit(speed_val, (panel_x + 45, panel_y + 50))
        surface.blit(speed_unit, (panel_x + 45, panel_y + 83))

        # Altimeter.
        alt_label = self.font_small.render("ALT", True, (230, 235, 240))
        surface.blit(alt_label, (panel_x + 140, panel_y + 10))

        altitude_px = max(0.0, terrain_y - (player.y + player.size))
        altitude_m = altitude_px / PIXELS_PER_METER
        alt_max = 200.0
        bar_x = panel_x + 165
        bar_y = panel_y + 28
        bar_w = 18
        bar_h = 95
        pygame.draw.rect(surface, (40, 50, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, (100, 150, 200), (bar_x, bar_y, bar_w, bar_h), 1)
        pygame.draw.rect(surface, (245, 245, 250), (bar_x, bar_y, bar_w, bar_h), 2)

        fill_pct = min(1.0, altitude_m / alt_max)
        fill_h = int(bar_h * fill_pct)
        fill_rect = (bar_x + 2, bar_y + bar_h - fill_h + 2, bar_w - 4, fill_h - 4 if fill_h > 4 else fill_h)
        if fill_h > 0:
            pygame.draw.rect(surface, (150, 210, 255), fill_rect)

        alt_val = self.font_medium.render(f"{altitude_m:0.0f}", True, (255, 255, 255))
        alt_unit = self.font_small.render("m", True, (200, 220, 240))
        surface.blit(alt_val, (panel_x + 125, panel_y + 58))
        surface.blit(alt_unit, (panel_x + 128, panel_y + 87))

        # Engine + fuel status for clearer moment-to-moment feedback.
        thrust_text = "THRUST ON" if player.is_thrusting else "THRUST OFF"
        thrust_color = (255, 175, 90) if player.is_thrusting else (165, 185, 205)
        self.draw_text(surface, thrust_text, self.font_small, thrust_color, panel_x + 18, panel_y + 124)

        if player.max_fuel > 0:
            fuel_ratio = player.fuel / max(1.0, player.max_fuel)
            if fuel_ratio <= 0.2:
                warn_color = (255, 130, 110) if (pygame.time.get_ticks() // 220) % 2 == 0 else (255, 190, 150)
                self.draw_text(surface, "LOW FUEL", self.font_small, warn_color, panel_x + 120, panel_y + 124)
    
    def draw_menu(self, surface, buttons):
        """Draw main menu."""
        # Gradient background for depth
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(25 + (100 * ratio))
            g = int(30 + (130 * ratio))
            b = int(40 + (150 * ratio))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        title = self.font_large.render("Learn to Fly 4", True, (255, 160, 100))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        # Title shadow
        shadow = self.font_large.render("Learn to Fly 4", True, (50, 50, 80))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 102))
        surface.blit(shadow, shadow_rect)
        surface.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Skyward Evolution", True, (220, 230, 245))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 160))
        surface.blit(subtitle, subtitle_rect)
        
        for button in buttons:
            button.draw(surface, self.font_medium)
    
    def draw_mission_select(self, surface, missions, buttons):
        """Draw mission selection screen."""
        # Gradient background
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(25 + (100 * ratio))
            g = int(30 + (130 * ratio))
            b = int(40 + (150 * ratio))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        title = self.font_large.render("Select Mission", True, (255, 160, 100))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 30))
        # Title shadow
        shadow = self.font_large.render("Select Mission", True, (50, 50, 80))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 32))
        surface.blit(shadow, shadow_rect)
        surface.blit(title, title_rect)
        # Separator line under title
        pygame.draw.line(surface, (100, 150, 200), (40, 70), (SCREEN_WIDTH - 40, 70), 2)
        
        y = 100
        for i, mission in enumerate(missions):
            status = "✓ COMPLETED" if mission.completed else "  [ ]"
            mission_text = f"{status} - {mission.name}: {mission.description} | Reward: {mission.reward_coins}$"
            text_color = (100, 200, 100) if mission.completed else (220, 230, 245)
            self.draw_text(surface, mission_text, self.font_small, text_color, 20, y)
            y += 40
        
        for button in buttons:
            button.draw(surface, self.font_medium)
    
    def _draw_catalog_icon(self, surface, category, key, rect):
        """Draw a compact item icon for the catalog page."""
        pygame.draw.rect(surface, (36, 52, 72), rect, border_radius=8)
        pygame.draw.rect(surface, (110, 150, 200), rect, 1, border_radius=8)
        cx = rect.x + rect.width // 2
        cy = rect.y + rect.height // 2

        if category == "sled":
            color = {
                "the_plank": (155, 105, 58),
                "plank_mk2": (142, 90, 48),
                "good_ol_sled": (120, 72, 35),
                "bobsled": (70, 102, 145),
            }.get(key, (130, 95, 60))
            pygame.draw.ellipse(surface, color, (rect.x + 8, cy - 10, rect.width - 16, 16))
            pygame.draw.line(surface, (210, 220, 230), (rect.x + 12, cy - 6), (rect.x + rect.width - 12, cy - 6), 2)
        elif category == "glider":
            wing_color = (75, 205, 110) if key == "kite" else ((90, 130, 170) if key == "old_glider" else (85, 145, 195))
            pygame.draw.polygon(surface, wing_color, [
                (rect.x + 10, cy + 5),
                (rect.x + rect.width - 12, cy - 6),
                (rect.x + rect.width - 18, cy + 10),
                (rect.x + 14, cy + 14),
            ])
            pygame.draw.line(surface, (150, 160, 175), (cx - 4, rect.y + 14), (cx - 4, rect.y + rect.height - 10), 2)
        elif category == "booster":
            if key == "sugar_rocket":
                pygame.draw.rect(surface, (205, 212, 225), (rect.x + 16, cy - 8, rect.width - 36, 16), border_radius=5)
                pygame.draw.polygon(surface, (205, 85, 85), [(rect.x + rect.width - 20, cy), (rect.x + rect.width - 8, cy - 6), (rect.x + rect.width - 8, cy + 6)])
            elif key == "pulse_jet":
                pygame.draw.rect(surface, (110, 118, 132), (rect.x + 10, cy - 5, rect.width - 20, 10), border_radius=3)
                pygame.draw.ellipse(surface, (128, 136, 152), (rect.x + rect.width - 20, cy - 9, 18, 18))
            else:
                pygame.draw.ellipse(surface, (98, 112, 136), (rect.x + 10, cy - 9, rect.width - 20, 18))
                pygame.draw.circle(surface, (170, 185, 205), (rect.x + rect.width - 12, cy), 7)

    def draw_upgrade_screen(self, surface, player, game_data, top_buttons, box_buttons, catalog_category, catalog_items, catalog_buttons, close_button):
        """Draw revamped gear shop with category boxes and catalog modal."""
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(25 + (100 * ratio))
            g = int(30 + (130 * ratio))
            b = int(40 + (150 * ratio))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        title = self.font_large.render("Flight Gear Shop", True, (255, 160, 100))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 28))
        shadow = self.font_large.render("Flight Gear Shop", True, (50, 50, 80))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 30))
        surface.blit(shadow, shadow_rect)
        surface.blit(title, title_rect)
        self.draw_text(surface, f"Coins: {player.coins}", self.font_medium, (255, 205, 120), 22, 62)

        ramp_level = max(0, min(int(game_data.get("ramp_height_level", 0)), len(RAMP_HEIGHT_TIERS) - 1))
        ramp_drop_level = max(0, min(int(game_data.get("ramp_drop_level", 0)), len(RAMP_DROP_TIERS) - 1))
        height_next = RAMP_HEIGHT_TIERS[ramp_level + 1] if ramp_level < len(RAMP_HEIGHT_TIERS) - 1 else None
        length_next = RAMP_DROP_TIERS[ramp_drop_level + 1] if ramp_drop_level < len(RAMP_DROP_TIERS) - 1 else None

        # Top progress bars
        bar_x = 20
        bar_w = 760
        bar_h = 22
        pygame.draw.rect(surface, (46, 66, 88), (bar_x, 92, bar_w, bar_h), border_radius=6)
        fill_w = int(bar_w * ((ramp_level + 1) / len(RAMP_HEIGHT_TIERS)))
        pygame.draw.rect(surface, (100, 176, 240), (bar_x, 92, fill_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, (230, 236, 245), (bar_x, 92, bar_w, bar_h), 2, border_radius=6)
        height_text = f"Ramp Height Lv {ramp_level + 1}/{len(RAMP_HEIGHT_TIERS)}"
        if height_next is None:
            height_text += " - MAX"
        else:
            height_text += f" - Next: {height_next['cost']}$"
        self.draw_text(surface, height_text, self.font_small, (225, 235, 248), bar_x + 8, 95)

        pygame.draw.rect(surface, (46, 66, 88), (bar_x, 142, bar_w, bar_h), border_radius=6)
        fill_w = int(bar_w * ((ramp_drop_level + 1) / len(RAMP_DROP_TIERS)))
        pygame.draw.rect(surface, (110, 194, 170), (bar_x, 142, fill_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, (230, 236, 245), (bar_x, 142, bar_w, bar_h), 2, border_radius=6)
        length_text = f"Ramp Length Lv {ramp_drop_level + 1}/{len(RAMP_DROP_TIERS)}"
        if length_next is None:
            length_text += " - MAX"
        else:
            length_text += f" - Next: {length_next['cost']}$"
        self.draw_text(surface, length_text, self.font_small, (225, 235, 248), bar_x + 8, 145)

        # Update top button labels and draw them (back + 2 upgrades).
        top_buttons[1].text = "MAX" if height_next is None else "Upgrade"
        top_buttons[2].text = "MAX" if length_next is None else "Upgrade"
        for button in top_buttons:
            button.draw(surface, self.font_medium)

        # 2x2 category boxes
        labels = {
            "sled": ("Sled", "Top-left"),
            "glider": ("Glider", "Top-right"),
            "booster": ("Engine", "Bottom-left"),
            "future": ("Unused", "Bottom-right"),
        }
        for key, button in box_buttons.items():
            button.draw(surface, self.font_medium)
            rect = button.rect
            title_text, subtitle = labels[key]
            self.draw_text(surface, title_text, self.font_medium, (235, 242, 252), rect.x + 16, rect.y + 14)
            self.draw_text(surface, subtitle, self.font_small, (175, 200, 228), rect.x + 16, rect.y + 52)
            if key == "future":
                self.draw_text(surface, "Reserved for future upgrades", self.font_small, (160, 170, 188), rect.x + 16, rect.y + 82)
            else:
                self.draw_text(surface, "Click to open catalog", self.font_small, (185, 210, 238), rect.x + 16, rect.y + 82)

        # Catalog modal
        if catalog_category:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 14, 24, 150))
            surface.blit(overlay, (0, 0))

            book_rect = pygame.Rect(120, 170, 960, 520)
            pygame.draw.rect(surface, (236, 229, 210), book_rect, border_radius=10)
            pygame.draw.rect(surface, (172, 150, 118), book_rect, 3, border_radius=10)
            pygame.draw.line(surface, (170, 152, 126), (book_rect.centerx, book_rect.y + 18), (book_rect.centerx, book_rect.bottom - 18), 3)

            title = f"{catalog_category.capitalize()} Catalog"
            self.draw_text(surface, title, self.font_large, (72, 58, 44), book_rect.x + 26, book_rect.y + 18)

            unlocked_map = {
                "sled": game_data["unlocked_sleds"],
                "glider": game_data["unlocked_gliders"],
                "booster": game_data["unlocked_boosters"],
            }
            equipped_map = {
                "sled": player.sled,
                "glider": player.glider,
                "booster": player.booster,
            }
            unlocked = unlocked_map[catalog_category]
            equipped = equipped_map[catalog_category]

            for i, (key, item) in enumerate(catalog_items):
                row_y = 245 + i * 92
                row_rect = pygame.Rect(150, row_y, 680, 76)
                pygame.draw.rect(surface, (246, 239, 224), row_rect, border_radius=8)
                pygame.draw.rect(surface, (195, 176, 144), row_rect, 1, border_radius=8)

                icon_rect = pygame.Rect(row_rect.x + 10, row_rect.y + 8, 110, 60)
                self._draw_catalog_icon(surface, catalog_category, key, icon_rect)

                name = item["name"]
                price = item["cost"]
                is_owned = key in unlocked
                is_equipped = key == equipped
                status = "EQUIPPED" if is_equipped else ("OWNED" if is_owned else "NOT OWNED")
                status_color = (85, 160, 95) if is_equipped else ((110, 120, 132) if is_owned else (180, 78, 78))

                self.draw_text(surface, name, self.font_medium, (62, 52, 42), row_rect.x + 136, row_rect.y + 10)
                self.draw_text(surface, f"Price: {price}$", self.font_small, (90, 75, 60), row_rect.x + 136, row_rect.y + 42)
                self.draw_text(surface, status, self.font_small, status_color, row_rect.x + 300, row_rect.y + 42)

                if i < len(catalog_buttons):
                    button = catalog_buttons[i]
                    if is_equipped:
                        button.text = "Equipped"
                    elif is_owned:
                        button.text = "Equip"
                    else:
                        button.text = "Buy"
                    button.draw(surface, self.font_small)

            close_button.draw(surface, self.font_small)
    
    def draw_results_screen(self, surface, distance, coins_earned, mission_completed, buttons):
        """Draw results screen after flight."""
        # Gradient background
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(25 + (100 * ratio))
            g = int(30 + (130 * ratio))
            b = int(40 + (150 * ratio))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        title = self.font_large.render("Flight Complete!", True, (100, 200, 100))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        shadow = self.font_large.render("Flight Complete!", True, (50, 50, 80))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 52))
        surface.blit(shadow, shadow_rect)
        surface.blit(title, title_rect)
        
        result_text = [
            f"Distance: {int(distance)} m",
            f"Coins Earned: +{coins_earned}",
        ]
        
        if mission_completed:
            result_text.append("🏆 MISSION COMPLETED! 🏆")
        
        y = 200
        for text in result_text:
            color = (255, 160, 100) if "MISSION" in text else (220, 230, 245)
            self.draw_text(surface, text, self.font_medium, color, SCREEN_WIDTH // 2 - 100, y)
            y += 50
        
        for button in buttons:
            button.draw(surface, self.font_medium)

