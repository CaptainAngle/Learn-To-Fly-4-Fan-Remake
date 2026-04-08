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
            f"Gear: {player.current_gear}",
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
        
        y = 130
        for gear_name, stats in GEAR_TYPES.items():
            if gear_name == "base":
                continue
            
            is_owned = gear_name in game_data["unlocked_gear"]
            is_equipped = gear_name == player.current_gear
            
            status = "EQUIPPED" if is_equipped else ("OWNED" if is_owned else "LOCKED")
            status_color = (0, 255, 0) if is_equipped else ((100, 100, 100) if is_owned else (255, 0, 0))
            
            gear_text = f"{gear_name.upper()} - Speed:{stats['speed']:.1f} Accel:{stats['acceleration']:.1f} Glide:{stats['glide']:.1f} | Cost: {stats['cost']}$ [{status}]"
            self.draw_text(surface, gear_text, self.font_small, status_color, 20, y)
            y += 35
        
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

