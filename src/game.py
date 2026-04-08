import pygame
from src.constants import *
from src.player import Player
from src.environment import Environment
from src.mission import MissionManager
from src.save_system import SaveSystem
from src.ui import UIManager, Button


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Learn to Fly 4: Skyward Evolution")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.state = STATE_MENU
        self.previous_state = None
        
        # Systems
        self.save_system = SaveSystem()
        self.ui_manager = UIManager()
        self.mission_manager = MissionManager()
        
        # Game objects
        self.player = None
        self.environment = None
        self.game_data = None
        
        # Camera system for scrolling
        self.camera_x = 0  # Camera position for horizontal scrolling
        self.camera_y = 0  # Camera position for vertical scrolling
        
        # Load or create save
        self.load_or_create_save()
        
        # UI buttons
        self.buttons = {}
        self.create_menu_buttons()
        
        # Flight state tracking
        self.flight_distance = 0
        self.flight_coins_earned = 0
        self.mission_completed_this_flight = False
        self.low_speed_frames = 0
    
    def load_or_create_save(self):
        """Load existing save or create new one."""
        save_data = self.save_system.load_game()
        if save_data is None:
            save_data = self.save_system.create_new_save()
        self.game_data = save_data
        
        # Create a dummy player for menus
        self.player = Player(100, 200)
        self.player.coins = self.game_data.get("total_coins", 0)
        if "equipped_gear" in self.game_data:
            self.player.equip_gear(self.game_data["equipped_gear"])
    
    def save_game(self):
        """Save current game state."""
        self.save_system.save_game(self.game_data)
    
    def create_menu_buttons(self):
        """Create buttons for different menus."""
        # Main menu buttons
        self.buttons["menu"] = [
            Button(SCREEN_WIDTH // 2 - 75, 250, 150, 60, "Start Flight", (100, 150, 100)),
            Button(SCREEN_WIDTH // 2 - 75, 350, 150, 60, "Gear Shop", (100, 100, 150)),
            Button(SCREEN_WIDTH // 2 - 75, 450, 150, 60, "Settings", (150, 100, 100)),
            Button(SCREEN_WIDTH // 2 - 75, 550, 150, 60, "Quit", (150, 50, 50)),
        ]
        
        # Mission select buttons
        self.buttons["mission_select"] = [
            Button(50, SCREEN_HEIGHT - 80, 120, 60, "Back", (100, 100, 100)),
        ]
        
        # For each mission
        for i in range(len(self.mission_manager.missions)):
            btn = Button(SCREEN_WIDTH - 200, 130 + (i * 50), 150, 40, "Select", (100, 150, 100))
            if "mission_buttons" not in self.buttons:
                self.buttons["mission_buttons"] = []
            self.buttons["mission_buttons"].append(btn)
        
        # Upgrade screen buttons
        self.buttons["upgrade"] = [
            Button(50, SCREEN_HEIGHT - 80, 120, 60, "Back", (100, 100, 100)),
        ]
        
        # For each gear
        for i, (gear_name, stats) in enumerate(GEAR_TYPES.items()):
            if gear_name == "base":
                continue
            btn = Button(SCREEN_WIDTH - 150, 150 + (i * 35), 120, 30, "Equip/Buy", (100, 150, 100))
            if "gear_buttons" not in self.buttons:
                self.buttons["gear_buttons"] = []
            self.buttons["gear_buttons"].append((gear_name, btn))
        
        # Results screen buttons
        self.buttons["results"] = [
            Button(SCREEN_WIDTH // 2 - 75, 450, 150, 60, "Continue", (100, 150, 100)),
        ]
    
    def start_flight(self):
        """Initialize a new flight."""
        self.environment = Environment()
        spawn_x = 80
        spawn_y = self.environment.terrain.get_ground_y_at(spawn_x) - 18
        self.player = Player(spawn_x, spawn_y)
        self.player.coins = self.game_data.get("total_coins", 0)
        self.player.vx = 1.0
        self.player.angle = 0
        self.camera_x = 0
        self.camera_y = 0
        self.flight_distance = 0
        self.flight_coins_earned = 0
        self.mission_completed_this_flight = False
        self.low_speed_frames = 0
        
        # Equip the current gear
        if "equipped_gear" in self.game_data:
            self.player.equip_gear(self.game_data["equipped_gear"])
        
        self.state = STATE_PLAYING
    
    def handle_input(self):
        """Handle player input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
                    self.save_game()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.handle_click(mouse_pos)
        
        # Continuous input for flight
        if self.state == STATE_PLAYING:
            keys = pygame.key.get_pressed()
            controls = {
                "left": keys[pygame.K_LEFT] or keys[pygame.K_a],
                "right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
                "boost": keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w],
            }
            return controls
        return {}
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks on buttons."""
        if self.state == STATE_MENU:
            for i, button in enumerate(self.buttons["menu"]):
                if button.is_clicked(mouse_pos, True):
                    if i == 0:  # Start Flight
                        self.state = STATE_MISSION_SELECT
                    elif i == 1:  # Gear Shop
                        self.state = STATE_UPGRADE
                    elif i == 2:  # Settings
                        pass  # TODO: Settings
                    elif i == 3:  # Quit
                        self.running = False
        
        elif self.state == STATE_MISSION_SELECT:
            if self.buttons["mission_select"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
            
            for i, button in enumerate(self.buttons.get("mission_buttons", [])):
                if button.is_clicked(mouse_pos, True):
                    mission = self.mission_manager.select_mission(i + 1)
                    if mission:
                        self.start_flight()
        
        elif self.state == STATE_UPGRADE:
            if self.buttons["upgrade"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
            
            for gear_name, button in self.buttons.get("gear_buttons", []):
                if button.is_clicked(mouse_pos, True):
                    self.try_purchase_gear(gear_name)
        
        elif self.state == STATE_RESULTS:
            if self.buttons["results"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
    
    def try_purchase_gear(self, gear_name):
        """Try to purchase or equip gear."""
        gear_info = GEAR_TYPES.get(gear_name)
        if not gear_info:
            return
        
        if gear_name in self.game_data["unlocked_gear"]:
            # Already owned, equip it
            self.player.equip_gear(gear_name)
            self.game_data["equipped_gear"] = gear_name
        else:
            # Not owned, try to purchase
            if self.player.coins >= gear_info["cost"]:
                self.player.coins -= gear_info["cost"]
                self.game_data["unlocked_gear"].append(gear_name)
                self.player.equip_gear(gear_name)
                self.game_data["equipped_gear"] = gear_name
    
    def update(self, controls):
        """Update game state."""
        if self.state == STATE_PLAYING:
            terrain_y = self.environment.terrain.get_ground_y_at(self.player.x)
            slope = self.environment.terrain.apply_ramp_boost(self.player, terrain_y)
            surface_type = self.environment.terrain.get_surface_type_at(self.player.x)

            # Ground contact: slide on ramp when touching terrain, otherwise airborne.
            grounded = self.player.y + self.player.size >= terrain_y - 2 and self.player.vy >= -1.5
            if grounded:
                self.player.y = terrain_y - self.player.size

            # Material friction: ice is slippery, snow is much stickier.
            if surface_type == "ice":
                friction = 0.998
            elif surface_type == "snow":
                friction = 0.92
            else:
                friction = 0.995

            self.player.update(
                controls,
                terrain_slope=slope,
                boosting=controls.get("boost", False),
                grounded=grounded,
                surface_friction=friction,
            )
            self.environment.update()

            # End the day if the penguin has effectively stopped.
            speed = (self.player.vx ** 2 + self.player.vy ** 2) ** 0.5
            if grounded and speed < 0.2:
                self.low_speed_frames += 1
            else:
                self.low_speed_frames = 0

            if self.low_speed_frames >= 30:
                self.flight_distance = self.player.distance_traveled
                if self.mission_manager.current_mission:
                    if self.mission_manager.current_mission.check_completion(self.flight_distance):
                        self.flight_coins_earned = self.mission_manager.current_mission.reward_coins
                        self.mission_completed_this_flight = True

                base_coins = int(self.flight_distance / 10)
                self.flight_coins_earned += base_coins
                self.player.coins += self.flight_coins_earned
                self.game_data["total_coins"] += self.flight_coins_earned
                self.game_data["total_distance"] += self.flight_distance
                self.save_game()
                self.state = STATE_RESULTS
                return

            # Keep penguin mostly stationary on screen while map scrolls.
            target_x = self.player.x - 120
            self.camera_x = max(0, min(target_x, self.environment.terrain.width - SCREEN_WIDTH))
            target_y = self.player.y - SCREEN_HEIGHT * 0.45
            self.camera_y += (target_y - self.camera_y) * 0.15

            # World bounds
            if self.player.x < 0:
                self.player.x = 0
                self.player.vx = 0
            elif self.player.x > self.environment.terrain.width - 50:
                self.flight_distance = self.player.distance_traveled
                if self.mission_manager.current_mission:
                    if self.mission_manager.current_mission.check_completion(self.flight_distance):
                        self.flight_coins_earned = self.mission_manager.current_mission.reward_coins
                        self.mission_completed_this_flight = True
                
                base_coins = int(self.flight_distance / 10)
                self.flight_coins_earned += base_coins
                self.player.coins += self.flight_coins_earned
                self.game_data["total_coins"] += self.flight_coins_earned
                self.game_data["total_distance"] += self.flight_distance
                self.save_game()
                self.state = STATE_RESULTS
    
    def draw(self):
        """Render game."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button states
        if self.state == STATE_MENU:
            for button in self.buttons["menu"]:
                button.update(mouse_pos)
            self.ui_manager.draw_menu(self.screen, self.buttons["menu"])
        
        elif self.state == STATE_MISSION_SELECT:
            for button in self.buttons["mission_select"]:
                button.update(mouse_pos)
            for button in self.buttons.get("mission_buttons", []):
                button.update(mouse_pos)
            self.ui_manager.draw_mission_select(self.screen, self.mission_manager.missions, 
                                               self.buttons["mission_select"] + self.buttons.get("mission_buttons", []))
        
        elif self.state == STATE_UPGRADE:
            for button in self.buttons["upgrade"]:
                button.update(mouse_pos)
            for _, button in self.buttons.get("gear_buttons", []):
                button.update(mouse_pos)
            self.ui_manager.draw_upgrade_screen(self.screen, self.player, self.game_data, 
                                               self.buttons["upgrade"] + [b for _, b in self.buttons.get("gear_buttons", [])])
        
        elif self.state == STATE_PLAYING:
            # Draw game with camera offset
            # Draw background (not affected by camera)
            self.screen.fill((135, 206, 235))
            
            # Draw clouds
            for i in range(5):
                cloud_y = 50 + (i * 100)
                parallax_x = int(100 + i * 200 - self.camera_x * 0.3)
                parallax_y = int(cloud_y - self.camera_y * 0.2)
                pygame.draw.circle(self.screen, (255, 255, 255), (parallax_x, parallax_y), 30)
                pygame.draw.circle(self.screen, (255, 255, 255), (parallax_x + 30, parallax_y), 35)
                pygame.draw.circle(self.screen, (255, 255, 255), (parallax_x - 30, parallax_y), 25)
            
            # Draw game elements with camera offset applied
            self.draw_terrain_with_camera(self.screen)
            self.draw_player_with_camera(self.screen)
            
            self.ui_manager.draw_stats(self.screen, self.player, self.environment)
            
            # Draw mission progress bar
            if self.mission_manager.current_mission:
                self.ui_manager.draw_mission_progress(self.screen, self.player, self.mission_manager.current_mission)
        
        elif self.state == STATE_RESULTS:
            for button in self.buttons["results"]:
                button.update(mouse_pos)
            self.ui_manager.draw_results_screen(self.screen, self.flight_distance, 
                                               self.flight_coins_earned, self.mission_completed_this_flight,
                                               self.buttons["results"])
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        while self.running:
            controls = self.handle_input()
            self.update(controls)
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
    
    def draw_terrain_with_camera(self, surface):
        """Draw terrain with camera offset applied."""
        terrain = self.environment.terrain
        offset = self.camera_x
        offset_y = self.camera_y
        
        # Draw terrain base polygon (snow shadow)
        if len(terrain.points) > 1:
            terrain_points = [(x - offset, y - offset_y) for x, y in terrain.points]
            terrain_points.append((self.environment.terrain.width - offset, SCREEN_HEIGHT * 2))
            terrain_points.append((0 - offset, SCREEN_HEIGHT * 2))
            
            pygame.draw.polygon(surface, (210, 220, 235), terrain_points)

        # Draw top surface by material.
        for i in range(len(terrain.points) - 1):
            x1, y1 = terrain.points[i]
            x2, y2 = terrain.points[i + 1]
            mid_x = (x1 + x2) * 0.5
            mat = terrain.get_surface_type_at(mid_x)
            if mat == "ice":
                top_color = (160, 220, 255)
                edge_color = (220, 245, 255)
                width = 6
            elif mat == "snow":
                top_color = (245, 248, 255)
                edge_color = (255, 255, 255)
                width = 8
            else:
                continue

            pygame.draw.line(surface, top_color, (x1 - offset, y1 - offset_y), (x2 - offset, y2 - offset_y), width)
            pygame.draw.line(surface, edge_color, (x1 - offset, y1 - offset_y), (x2 - offset, y2 - offset_y), 2)
        
        # Draw terrain outline
        for i in range(len(terrain.points) - 1):
            x1, y1 = terrain.points[i]
            x2, y2 = terrain.points[i + 1]
            pygame.draw.line(surface, (150, 165, 185), (x1 - offset, y1 - offset_y), (x2 - offset, y2 - offset_y), 2)
        
        # Subtle ice sheen on launch ramp.
        for i in range(len(terrain.points) - 1):
            x1, y1 = terrain.points[i]
            x2, y2 = terrain.points[i + 1]
            mid_x = (x1 + x2) * 0.5
            if terrain.get_surface_type_at(mid_x) == "ice":
                pygame.draw.line(surface, (190, 235, 255), (x1 - offset, y1 - offset_y - 4), (x2 - offset, y2 - offset_y - 4), 1)
        
        # Draw wind particles
        for p in terrain.wind_particles:
            if -50 < p["x"] - offset < SCREEN_WIDTH + 50:
                size = max(1, int(2 * (p["life"] / 30)))
                pygame.draw.circle(surface, (180, 180, 180), (int(p["x"] - offset), int(p["y"] - offset_y)), size)
        
        # Draw hazards with camera offset
        for hazard in self.environment.hazards:
            hazard_screen_x = hazard.x - offset
            hazard_screen_y = hazard.y - offset_y
            if -50 < hazard_screen_x < SCREEN_WIDTH + 50:  # Only draw if visible
                if hazard.type == "spike":
                    pygame.draw.polygon(surface, (255, 0, 0), [
                        (hazard_screen_x, hazard_screen_y - hazard.size),
                        (hazard_screen_x - hazard.size, hazard_screen_y + hazard.size),
                        (hazard_screen_x + hazard.size, hazard_screen_y + hazard.size),
                    ])
                elif hazard.type == "wall":
                    pygame.draw.rect(surface, (128, 128, 128), 
                                   (hazard_screen_x - hazard.size, hazard_screen_y - hazard.size * 2, 
                                    hazard.size * 2, hazard.size * 4))
    
    def draw_player_with_camera(self, surface):
        """Draw player with camera offset applied."""
        offset = self.camera_x
        offset_y = self.camera_y
        size = self.player.size
        player_screen_x = self.player.x - offset
        player_screen_y = self.player.y - offset_y

        if -size * 2 < player_screen_x < SCREEN_WIDTH + size * 2:
            sprite = pygame.Surface((size * 4, size * 3), pygame.SRCALPHA)
            cx = int(size * 2)
            cy = int(size * 1.5)

            # Side-profile penguin facing right.
            pygame.draw.ellipse(sprite, (20, 20, 20), (size * 0.8, size * 0.7, size * 2.1, size * 1.6))
            pygame.draw.ellipse(sprite, (230, 230, 230), (size * 1.35, size * 1.0, size * 1.15, size * 1.15))
            pygame.draw.circle(sprite, (20, 20, 20), (int(size * 2.45), int(size * 0.9)), int(size * 0.45))
            pygame.draw.circle(sprite, (255, 255, 255), (int(size * 2.55), int(size * 0.85)), int(size * 0.13))
            pygame.draw.circle(sprite, (0, 0, 0), (int(size * 2.6), int(size * 0.85)), int(size * 0.06))
            pygame.draw.polygon(sprite, (255, 160, 0), [
                (size * 2.8, size * 0.95),
                (size * 3.25, size * 1.05),
                (size * 2.82, size * 1.18),
            ])
            pygame.draw.ellipse(sprite, (15, 15, 15), (size * 1.3, size * 1.1, size * 0.85, size * 0.6))
            pygame.draw.ellipse(sprite, (255, 165, 0), (size * 1.2, size * 2.1, size * 0.45, size * 0.18))
            pygame.draw.ellipse(sprite, (255, 165, 0), (size * 1.7, size * 2.12, size * 0.45, size * 0.18))

            rotated = pygame.transform.rotozoom(sprite, self.player.angle, 1.0)
            rect = rotated.get_rect(center=(player_screen_x, player_screen_y))
            surface.blit(rotated, rect)
            self.draw_equipment_overlay(surface, player_screen_x, player_screen_y, size, self.player.current_gear, self.player.angle)
            
            # Fuel bar
            if self.player.fuel > 0:
                bar_width = 25
                bar_height = 5
                bar_x = player_screen_x - bar_width // 2
                bar_y = player_screen_y - size - 15
                
                pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
                
                fuel_width = int(bar_width * (self.player.fuel / self.player.max_fuel))
                fuel_color = (int(255 * (1 - self.player.fuel / self.player.max_fuel)), 
                            int(255 * (self.player.fuel / self.player.max_fuel)), 0)
                pygame.draw.rect(surface, fuel_color, (bar_x, bar_y, fuel_width, bar_height))
                
                pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)

    def draw_equipment_overlay(self, surface, px, py, size, gear, angle):
        """Draw oversized equipment overlay attached to penguin."""
        if gear == "base":
            return

        # Halved from previous value and re-centered around penguin body.
        gear_scale = 3.5
        canvas = pygame.Surface((size * 24, size * 24), pygame.SRCALPHA)
        cx = size * 12
        cy = size * 12

        if gear == "jetpack_mk1":
            pygame.draw.rect(
                canvas,
                (120, 120, 130),
                (cx - size * 0.95 * gear_scale, cy - size * 0.1 * gear_scale, size * 0.45 * gear_scale, size * 0.8 * gear_scale),
                border_radius=6,
            )
            pygame.draw.rect(canvas, (230, 90, 30), (cx - size * 1.0 * gear_scale, cy + size * 0.55 * gear_scale, size * 0.16 * gear_scale, size * 0.22 * gear_scale))
            pygame.draw.rect(canvas, (230, 90, 30), (cx - size * 0.62 * gear_scale, cy + size * 0.55 * gear_scale, size * 0.16 * gear_scale, size * 0.22 * gear_scale))

        elif gear == "wingsuit":
            pygame.draw.polygon(canvas, (80, 110, 150), [
                (cx - size * 0.08 * gear_scale, cy),
                (cx - size * 1.0 * gear_scale, cy + size * 0.4 * gear_scale),
                (cx - size * 0.35 * gear_scale, cy + size * 0.78 * gear_scale),
            ])
            pygame.draw.polygon(canvas, (80, 110, 150), [
                (cx + size * 0.08 * gear_scale, cy),
                (cx + size * 1.0 * gear_scale, cy + size * 0.4 * gear_scale),
                (cx + size * 0.35 * gear_scale, cy + size * 0.78 * gear_scale),
            ])

        elif gear == "rocket_boots":
            pygame.draw.rect(canvas, (190, 70, 70), (cx - size * 0.48 * gear_scale, cy + size * 0.72 * gear_scale, size * 0.32 * gear_scale, size * 0.16 * gear_scale), border_radius=5)
            pygame.draw.rect(canvas, (190, 70, 70), (cx + size * 0.02 * gear_scale, cy + size * 0.72 * gear_scale, size * 0.32 * gear_scale, size * 0.16 * gear_scale), border_radius=5)
            pygame.draw.circle(canvas, (255, 190, 60), (int(cx - size * 0.52 * gear_scale), int(cy + size * 0.81 * gear_scale)), int(size * 0.05 * gear_scale))
            pygame.draw.circle(canvas, (255, 190, 60), (int(cx + size * 0.38 * gear_scale), int(cy + size * 0.81 * gear_scale)), int(size * 0.05 * gear_scale))

        elif gear == "propeller_hat":
            pygame.draw.ellipse(canvas, (90, 90, 95), (cx - size * 0.22 * gear_scale, cy - size * 0.92 * gear_scale, size * 0.44 * gear_scale, size * 0.18 * gear_scale))
            pygame.draw.line(canvas, (120, 120, 120), (cx, cy - size * 0.92 * gear_scale), (cx, cy - size * 1.18 * gear_scale), 3)
            pygame.draw.line(canvas, (170, 170, 175), (cx - size * 0.38 * gear_scale, cy - size * 1.18 * gear_scale), (cx + size * 0.38 * gear_scale, cy - size * 1.18 * gear_scale), 4)

        rotated_overlay = pygame.transform.rotozoom(canvas, angle, 1.0)
        overlay_rect = rotated_overlay.get_rect(center=(px, py))
        surface.blit(rotated_overlay, overlay_rect)


if __name__ == "__main__":
    game = Game()
    game.run()

