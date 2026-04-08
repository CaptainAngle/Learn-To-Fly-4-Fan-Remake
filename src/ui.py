import math
import pygame
from src.constants import *


class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hovered = False
    
    def update(self, mouse_pos):
        """Update button state based on mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface, font):
        """Draw button."""
        color = tuple(min(c + 30, 255) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        
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
        pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        
        # Draw progress
        progress_width = int(bar_width * progress)
        if progress >= 1.0:
            color = (0, 255, 0)  # Green when complete
        else:
            color = (100, 150, 255)  # Blue while progressing
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
        pygame.draw.rect(surface, (15, 25, 35), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(surface, (220, 230, 240), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        # Speed dial.
        dial_cx = panel_x + 70
        dial_cy = panel_y + 75
        dial_r = 46
        pygame.draw.circle(surface, (30, 40, 50), (dial_cx, dial_cy), dial_r)
        pygame.draw.circle(surface, (220, 230, 240), (dial_cx, dial_cy), dial_r, 2)

        # Tick marks.
        for i in range(0, 9):
            ang = math.radians(210 - i * 22.5)
            inner = dial_r - 6
            outer = dial_r - (2 if i % 2 == 0 else 0)
            x1 = dial_cx + math.cos(ang) * inner
            y1 = dial_cy - math.sin(ang) * inner
            x2 = dial_cx + math.cos(ang) * outer
            y2 = dial_cy - math.sin(ang) * outer
            pygame.draw.line(surface, (180, 190, 200), (x1, y1), (x2, y2), 2)

        # Speed value mapped to dial (px/frame to approx m/s).
        speed_px = math.hypot(player.vx, player.vy)
        speed_mps = speed_px * 60 / PIXELS_PER_METER
        speed_max = 80.0
        speed_pct = min(1.0, speed_mps / speed_max)
        needle_ang = math.radians(210 - 180 * speed_pct)
        needle_len = dial_r - 10
        nx = dial_cx + math.cos(needle_ang) * needle_len
        ny = dial_cy - math.sin(needle_ang) * needle_len
        pygame.draw.line(surface, (255, 120, 80), (dial_cx, dial_cy), (nx, ny), 3)
        pygame.draw.circle(surface, (255, 120, 80), (dial_cx, dial_cy), 4)

        speed_label = self.font_small.render("SPEED", True, (230, 235, 240))
        surface.blit(speed_label, (panel_x + 20, panel_y + 10))
        speed_val = self.font_medium.render(f"{speed_mps:0.1f}", True, (255, 255, 255))
        speed_unit = self.font_small.render("m/s", True, (180, 190, 200))
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
        pygame.draw.rect(surface, (220, 230, 240), (bar_x, bar_y, bar_w, bar_h), 2)

        fill_pct = min(1.0, altitude_m / alt_max)
        fill_h = int(bar_h * fill_pct)
        fill_rect = (bar_x + 2, bar_y + bar_h - fill_h + 2, bar_w - 4, fill_h - 4 if fill_h > 4 else fill_h)
        if fill_h > 0:
            pygame.draw.rect(surface, (90, 210, 255), fill_rect)

        alt_val = self.font_medium.render(f"{altitude_m:0.0f}", True, (255, 255, 255))
        alt_unit = self.font_small.render("m", True, (180, 190, 200))
        surface.blit(alt_val, (panel_x + 125, panel_y + 58))
        surface.blit(alt_unit, (panel_x + 128, panel_y + 87))
    
    def draw_menu(self, surface, buttons):
        """Draw main menu."""
        surface.fill(COLOR_DARK)
        
        title = self.font_large.render("Learn to Fly 4", True, COLOR_TEXT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        surface.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Skyward Evolution", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 160))
        surface.blit(subtitle, subtitle_rect)
        
        for button in buttons:
            button.draw(surface, self.font_medium)
    
    def draw_mission_select(self, surface, missions, buttons):
        """Draw mission selection screen."""
        surface.fill(COLOR_DARK)
        
        title = self.font_large.render("Select Mission", True, COLOR_TEXT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 30))
        surface.blit(title, title_rect)
        
        y = 100
        for i, mission in enumerate(missions):
            status = "✓ COMPLETED" if mission.completed else "  [ ]"
            mission_text = f"{status} - {mission.name}: {mission.description} | Reward: {mission.reward_coins}$"
            self.draw_text(surface, mission_text, self.font_small, COLOR_TEXT, 20, y)
            y += 40
        
        for button in buttons:
            button.draw(surface, self.font_medium)
    
    def draw_upgrade_screen(self, surface, player, game_data, buttons):
        """Draw upgrade/shop screen."""
        surface.fill(COLOR_DARK)
        
        title = self.font_large.render("Flight Gear Shop", True, COLOR_TEXT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 20))
        surface.blit(title, title_rect)
        
        self.draw_text(surface, f"Coins: {player.coins}", self.font_medium, (255, 215, 0), 20, 70)
        
        y = 110
        self.draw_text(surface, "SLED", self.font_medium, (180, 220, 255), 20, y)
        y += 30
        for key, stats in SLED_TIERS.items():
            is_owned = key in game_data["unlocked_sleds"]
            is_equipped = key == player.sled
            status = "EQUIPPED" if is_equipped else ("OWNED" if is_owned else "LOCKED")
            status_color = (0, 255, 0) if is_equipped else ((140, 140, 140) if is_owned else (255, 120, 120))
            text = f"{stats['name']} | Ramp Grip- {stats['ramp_friction_mult']:.2f} | Cost: {stats['cost']}$ [{status}]"
            self.draw_text(surface, text, self.font_small, status_color, 20, y)
            y += 30

        y += 8
        self.draw_text(surface, "GLIDER", self.font_medium, (180, 220, 255), 20, y)
        y += 30
        for key, stats in GLIDER_TIERS.items():
            is_owned = key in game_data["unlocked_gliders"]
            is_equipped = key == player.glider
            status = "EQUIPPED" if is_equipped else ("OWNED" if is_owned else "LOCKED")
            status_color = (0, 255, 0) if is_equipped else ((140, 140, 140) if is_owned else (255, 120, 120))
            text = f"{stats['name']} | Glide x{stats['glide_mult']:.2f} | Cost: {stats['cost']}$ [{status}]"
            self.draw_text(surface, text, self.font_small, status_color, 20, y)
            y += 30

        y += 8
        self.draw_text(surface, "BOOSTER", self.font_medium, (180, 220, 255), 20, y)
        y += 30
        for key, stats in BOOSTER_TIERS.items():
            is_owned = key in game_data["unlocked_boosters"]
            is_equipped = key == player.booster
            status = "EQUIPPED" if is_equipped else ("OWNED" if is_owned else "LOCKED")
            status_color = (0, 255, 0) if is_equipped else ((140, 140, 140) if is_owned else (255, 120, 120))
            text = f"{stats['name']} | Boost x{stats['boost_mult']:.2f} Fuel {stats['fuel']} | Cost: {stats['cost']}$ [{status}]"
            self.draw_text(surface, text, self.font_small, status_color, 20, y)
            y += 30
        
        for button in buttons:
            button.draw(surface, self.font_medium)
    
    def draw_results_screen(self, surface, distance, coins_earned, mission_completed, buttons):
        """Draw results screen after flight."""
        surface.fill(COLOR_DARK)
        
        title = self.font_large.render("Flight Complete!", True, COLOR_TEXT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title, title_rect)
        
        result_text = [
            f"Distance: {int(distance)} m",
            f"Coins Earned: +{coins_earned}",
        ]
        
        if mission_completed:
            result_text.append("MISSION COMPLETED! ✓")
        
        y = 200
        for text in result_text:
            color = (0, 255, 0) if "MISSION" in text else COLOR_TEXT
            self.draw_text(surface, text, self.font_medium, color, SCREEN_WIDTH // 2 - 100, y)
            y += 50
        
        for button in buttons:
            button.draw(surface, self.font_medium)

