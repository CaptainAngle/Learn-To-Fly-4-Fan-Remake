import math
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

        # Migrate legacy save keys to categorized gear keys.
        if "unlocked_sleds" not in save_data:
            save_data["unlocked_sleds"] = []
        if "unlocked_gliders" not in save_data:
            save_data["unlocked_gliders"] = []
        if "unlocked_boosters" not in save_data:
            save_data["unlocked_boosters"] = []
        if "equipped_sled" not in save_data:
            save_data["equipped_sled"] = None
        if "equipped_glider" not in save_data:
            save_data["equipped_glider"] = None
        if "equipped_booster" not in save_data:
            save_data["equipped_booster"] = None

        self.game_data = save_data
        
        # Create a dummy player for menus
        self.player = Player(100, 200)
        self.player.coins = self.game_data.get("total_coins", 0)
        self.player.equip_sled(self.game_data["equipped_sled"])
        self.player.equip_glider(self.game_data["equipped_glider"])
        self.player.equip_booster(self.game_data["equipped_booster"])
    
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

        self.buttons["gear_buttons"] = []
        y = 145
        for gear_name in SLED_TIERS.keys():
            btn = Button(SCREEN_WIDTH - 170, y, 140, 28, "Equip/Buy", (100, 150, 100))
            self.buttons["gear_buttons"].append(("sled", gear_name, btn))
            y += 34
        y += 10
        for gear_name in GLIDER_TIERS.keys():
            btn = Button(SCREEN_WIDTH - 170, y, 140, 28, "Equip/Buy", (100, 150, 100))
            self.buttons["gear_buttons"].append(("glider", gear_name, btn))
            y += 34
        y += 10
        for gear_name in BOOSTER_TIERS.keys():
            btn = Button(SCREEN_WIDTH - 170, y, 140, 28, "Equip/Buy", (100, 150, 100))
            self.buttons["gear_buttons"].append(("booster", gear_name, btn))
            y += 34
        
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
        
        self.player.equip_sled(self.game_data["equipped_sled"])
        self.player.equip_glider(self.game_data["equipped_glider"])
        self.player.equip_booster(self.game_data["equipped_booster"])
        
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
            
            for category, gear_name, button in self.buttons.get("gear_buttons", []):
                if button.is_clicked(mouse_pos, True):
                    self.try_purchase_gear(category, gear_name)
        
        elif self.state == STATE_RESULTS:
            if self.buttons["results"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
    
    def try_purchase_gear(self, category, gear_name):
        """Try to purchase or equip categorized gear."""
        if category == "sled":
            gear_info = SLED_TIERS.get(gear_name)
            unlock_key = "unlocked_sleds"
            equip_key = "equipped_sled"
            equip_fn = self.player.equip_sled
        elif category == "glider":
            gear_info = GLIDER_TIERS.get(gear_name)
            unlock_key = "unlocked_gliders"
            equip_key = "equipped_glider"
            equip_fn = self.player.equip_glider
        elif category == "booster":
            gear_info = BOOSTER_TIERS.get(gear_name)
            unlock_key = "unlocked_boosters"
            equip_key = "equipped_booster"
            equip_fn = self.player.equip_booster
        else:
            return

        if not gear_info:
            return

        if gear_name in self.game_data[unlock_key]:
            equip_fn(gear_name)
            self.game_data[equip_key] = gear_name
        else:
            if self.player.coins >= gear_info["cost"]:
                self.player.coins -= gear_info["cost"]
                self.game_data[unlock_key].append(gear_name)
                equip_fn(gear_name)
                self.game_data[equip_key] = gear_name
    
    def update(self, controls, dt=1.0 / FPS):
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
                friction = 0.985
            else:
                friction = 0.995

            # Sled reduces ramp friction while attached and on ice.
            if grounded and surface_type == "ice" and self.player.sled_attached and self.player.sled in SLED_TIERS:
                sled_mult = SLED_TIERS[self.player.sled]["ramp_friction_mult"]
                friction = min(0.9995, friction * sled_mult)

            # Sled is launched away once the penguin leaves the ramp.
            if not grounded and self.player.sled_attached:
                self.player.sled_attached = False

            self.player.update(
                controls,
                terrain_slope=slope,
                boosting=controls.get("boost", False),
                grounded=grounded,
                surface_friction=friction,
                can_rotate=not (grounded and surface_type == "ice"),
                dt=dt,
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
            for _, _, button in self.buttons.get("gear_buttons", []):
                button.update(mouse_pos)
            self.ui_manager.draw_upgrade_screen(self.screen, self.player, self.game_data, 
                                               self.buttons["upgrade"] + [b for _, _, b in self.buttons.get("gear_buttons", [])])
        
        elif self.state == STATE_PLAYING:
            # Draw game with camera offset
            # Draw background (not affected by camera)
            self.screen.fill((135, 206, 235))
            
            # Draw game elements with camera offset applied
            self.draw_terrain_with_camera(self.screen)
            self.draw_player_with_camera(self.screen)
            
            self.ui_manager.draw_stats(self.screen, self.player, self.environment)
            terrain_y = self.environment.terrain.get_ground_y_at(self.player.x)
            self.ui_manager.draw_flight_hud(self.screen, self.player, terrain_y)
            
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
            dt = self.clock.tick(FPS) / 1000.0
            controls = self.handle_input()
            self.update(controls, dt)
            self.draw()
        
        pygame.quit()
    
    def draw_terrain_with_camera(self, surface):
        """Draw terrain with camera offset applied."""
        terrain = self.environment.terrain
        offset = self.camera_x
        offset_y = self.camera_y

        # Draw clouds as terrain-anchored world objects behind the ground.
        for cloud in terrain.clouds:
            cx = cloud["x"] - offset * 0.95
            cy = cloud["y"] - offset_y * 0.10
            s = cloud["s"]
            if -120 < cx < SCREEN_WIDTH + 120:
                pygame.draw.circle(surface, (248, 248, 248), (int(cx), int(cy)), s)
                pygame.draw.circle(surface, (248, 248, 248), (int(cx + s * 0.9), int(cy + s * 0.05)), int(s * 1.05))
                pygame.draw.circle(surface, (248, 248, 248), (int(cx - s * 0.8), int(cy + s * 0.05)), int(s * 0.85))
                pygame.draw.circle(surface, (245, 245, 245), (int(cx + s * 0.2), int(cy - s * 0.35)), int(s * 0.95))
        
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

            # Texture marks anchored to world coordinates so ground motion is visible.
            seg_len = max(1.0, ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
            mark_step = 22 if mat == "snow" else 22
            mark_count = int(seg_len // mark_step)
            for j in range(mark_count + 1):
                t = 0 if mark_count == 0 else j / max(1, mark_count)
                mx = x1 + (x2 - x1) * t
                my = y1 + (y2 - y1) * t

                if mat == "snow":
                    # Deterministic pseudo-random variation by world position.
                    seed = int(mx * 0.37 + my * 1.91 + j * 13 + i * 101)
                    rand_a = ((seed * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF
                    rand_b = (((seed + 77) * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF
                    rand_c = (((seed + 173) * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF

                    # Draw downward streaks into the snow body, not just at the border.
                    jitter_x = -4 + int(rand_c * 9)
                    start_x = mx - offset + jitter_x
                    start_y = my - offset_y + 2 + int(rand_a * 3)

                    depth = 14 + int(rand_b * 34)
                    drift = -2 + int(rand_a * 5)

                    end_x = start_x + drift
                    end_y = start_y + depth

                    color = (218, 226, 236) if rand_b > 0.5 else (230, 236, 244)
                    pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), 1)

                    # Occasional secondary streak for a more natural random pattern.
                    if rand_c > 0.62:
                        sx2 = start_x + 2
                        sy2 = start_y + 3
                        ex2 = sx2 + max(-1, drift - 1)
                        ey2 = sy2 + max(8, depth - 8)
                        pygame.draw.line(surface, (235, 240, 247), (sx2, sy2), (ex2, ey2), 1)
                else:  # ice
                    pygame.draw.line(
                        surface,
                        (185, 235, 250),
                        (mx - offset - 3, my - offset_y - 1),
                        (mx - offset + 3, my - offset_y + 1),
                        1,
                    )
        
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
        size = int(self.player.size * 1.5)
        player_screen_x = self.player.x - offset
        player_screen_y = self.player.y - offset_y

        if -size * 2 < player_screen_x < SCREEN_WIDTH + size * 2:
            sprite = pygame.Surface((size * 4, size * 3), pygame.SRCALPHA)
            cx = int(size * 2)
            cy = int(size * 1.5)

            # Belly-sliding penguin: half-ellipse cut on the MINOR diameter (vertical cut).
            body_left = size * 0.36
            body_top = size * 0.68
            body_w = size * 3.45
            body_h = size * 1.50
            cx_body = body_left + body_w * 0.50
            cy_body = body_top + body_h * 0.50
            rx = body_w * 0.50
            ry = body_h * 0.50

            # Right half of ellipse, with flat vertical back edge at x = cx_body.
            half_body = [(cx_body, cy_body - ry)]
            samples = 22
            for i in range(samples + 1):
                theta = -math.pi / 2 + (math.pi * i / samples)
                x = cx_body + rx * math.cos(theta)
                y = cy_body + ry * math.sin(theta)
                half_body.append((x, y))
            half_body.append((cx_body, cy_body + ry))
            pygame.draw.polygon(sprite, (20, 20, 20), half_body)

            # White belly patch in the lower-front part.
            belly_left = cx_body + size * 0.42
            belly_top = cy_body + size * 0.02
            belly_w = size * 1.25
            belly_h = size * 0.62
            pygame.draw.ellipse(sprite, (236, 236, 236), (belly_left, belly_top, belly_w, belly_h))

            # Side beak at front.
            pygame.draw.polygon(sprite, (255, 160, 0), [
                (cx_body + rx * 0.97, cy_body - size * 0.08),
                (cx_body + rx * 1.36, cy_body),
                (cx_body + rx * 0.97, cy_body + size * 0.09),
            ])

            # Eye near front/top.
            pygame.draw.circle(sprite, (255, 255, 255), (int(cx_body + rx * 0.60), int(cy_body - ry * 0.30)), int(size * 0.11))
            pygame.draw.circle(sprite, (0, 0, 0), (int(cx_body + rx * 0.66), int(cy_body - ry * 0.28)), int(size * 0.05))

            # Feet under body for sliding silhouette.
            feet_w = size * 0.52
            feet_h = size * 0.20

            # Original centers before rotation (right foot is pivot).
            right_center_x = cx_body - size * 0.17
            # Move feet up by about 50% of penguin height.
            right_center_y = cy_body + ry - size * 0.70
            left_center_x = cx_body - size * 0.57
            left_center_y = cy_body + ry - size * 0.67

            # Rotate left foot around right foot by 90 deg clockwise.
            dx = left_center_x - right_center_x
            dy = left_center_y - right_center_y
            left_rot_x = right_center_x + dy
            left_rot_y = right_center_y - dx

            pygame.draw.ellipse(sprite, (255, 165, 0), (right_center_x - feet_w / 2, right_center_y - feet_h / 2, feet_w, feet_h))
            pygame.draw.ellipse(sprite, (255, 165, 0), (left_rot_x - feet_w / 2, left_rot_y - feet_h / 2, feet_w, feet_h))

            rotated = pygame.transform.rotozoom(sprite, self.player.angle, 1.0)
            rect = rotated.get_rect(center=(player_screen_x, player_screen_y))
            surface.blit(rotated, rect)
            self.draw_equipment_overlay(surface, player_screen_x, player_screen_y, size, self.player, self.player.angle)
            
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

    def draw_equipment_overlay(self, surface, px, py, size, player, angle):
        """Draw oversized equipment overlay attached to penguin."""
        gear_scale = 3.5
        canvas = pygame.Surface((size * 24, size * 24), pygame.SRCALPHA)
        cx = size * 12
        cy = size * 12

        # Sled layer (only while attached on ramp).
        if player.sled_attached:
            sled_color = {
                "the_plank": (142, 98, 59),
                "plank_mk2": (124, 86, 52),
                "good_ol_sled": (116, 62, 34),
                "bobsled": (70, 90, 120),
            }[player.sled]
            pygame.draw.ellipse(
                canvas,
                sled_color,
                (cx - size * 0.7 * gear_scale, cy + size * 0.72 * gear_scale, size * 1.55 * gear_scale, size * 0.28 * gear_scale),
            )

        # Glider layer.
        if player.glider == "kite":
            # Skinny green parallelogram directly on top of the penguin.
            mast_base = (cx - size * 0.02 * gear_scale, cy + size * 0.02 * gear_scale)
            mast_top = (cx - size * 0.02 * gear_scale, cy - size * 0.24 * gear_scale)
            pygame.draw.line(canvas, (120, 120, 120), mast_base, mast_top, 2)

            kite_x = mast_top[0]
            kite_y = mast_top[1] - size * 0.02 * gear_scale
            kite_w = size * 0.70 * gear_scale
            kite_h = size * 0.10 * gear_scale
            slant = size * 0.16 * gear_scale

            pygame.draw.polygon(canvas, (70, 200, 95), [
                (kite_x - kite_w * 0.5 + slant, kite_y - kite_h * 0.5),
                (kite_x + kite_w * 0.5 + slant, kite_y - kite_h * 0.5),
                (kite_x + kite_w * 0.5 - slant, kite_y + kite_h * 0.5),
                (kite_x - kite_w * 0.5 - slant, kite_y + kite_h * 0.5),
            ])
            pygame.draw.line(
                canvas,
                (150, 235, 165),
                (kite_x - kite_w * 0.45 + slant, kite_y - kite_h * 0.18),
                (kite_x + kite_w * 0.45 + slant, kite_y - kite_h * 0.18),
                1,
            )

        elif player.glider in ("old_glider", "hand_glider"):
            if player.glider == "old_glider":
                wing_len = 0.95
                wing_thickness = 0.10
                mast_h = 0.62
                color_main = (95, 115, 150)
                color_highlight = (185, 205, 235)
            else:  # hand_glider
                wing_len = 1.20
                wing_thickness = 0.11
                mast_h = 0.68
                color_main = (78, 102, 140)
                color_highlight = (170, 195, 235)

            # Back-mounted anchor (penguin faces right, so back is left side).
            mast_base = (cx - size * 0.12 * gear_scale, cy + size * 0.05 * gear_scale)
            mast_top = (cx - size * 0.18 * gear_scale, cy - size * (mast_h - 0.28) * gear_scale)

            # Strap/mast from penguin to glider.
            pygame.draw.line(canvas, (125, 125, 125), mast_base, mast_top, 2)

            # Thin side-view wing profile above penguin.
            wing_x = mast_top[0]
            wing_y = mast_top[1] + size * 0.18 * gear_scale
            pygame.draw.polygon(canvas, color_main, [
                (wing_x + size * 0.12 * gear_scale, wing_y - size * wing_thickness * gear_scale),
                (wing_x - size * wing_len * gear_scale, wing_y - size * (wing_thickness * 0.55) * gear_scale),
                (wing_x - size * (wing_len - 0.18) * gear_scale, wing_y + size * wing_thickness * gear_scale),
                (wing_x + size * 0.08 * gear_scale, wing_y + size * (wing_thickness * 0.7) * gear_scale),
            ])
            pygame.draw.line(
                canvas,
                color_highlight,
                (wing_x + size * 0.08 * gear_scale, wing_y - size * (wing_thickness * 0.2) * gear_scale),
                (wing_x - size * (wing_len - 0.15) * gear_scale, wing_y - size * (wing_thickness * 0.05) * gear_scale),
                1,
            )
            # Small rear support strap to keep the glider looking strapped on.
            pygame.draw.line(
                canvas,
                (125, 125, 125),
                (cx + size * 0.14 * gear_scale, cy + size * 0.10 * gear_scale),
                (wing_x + size * 0.03 * gear_scale, wing_y + size * 0.02 * gear_scale),
                1,
            )

        # Booster layer.
        gear = player.booster
        if gear == "sugar_rocket":
            pygame.draw.rect(
                canvas,
                (120, 120, 130),
                (cx - size * 0.95 * gear_scale, cy - size * 0.1 * gear_scale, size * 0.45 * gear_scale, size * 0.8 * gear_scale),
                border_radius=6,
            )
            pygame.draw.rect(canvas, (230, 90, 30), (cx - size * 1.0 * gear_scale, cy + size * 0.55 * gear_scale, size * 0.16 * gear_scale, size * 0.22 * gear_scale))
            pygame.draw.rect(canvas, (230, 90, 30), (cx - size * 0.62 * gear_scale, cy + size * 0.55 * gear_scale, size * 0.16 * gear_scale, size * 0.22 * gear_scale))

        elif gear == "pulse_jet":
            pygame.draw.rect(canvas, (98, 98, 112), (cx - size * 1.05 * gear_scale, cy - size * 0.12 * gear_scale, size * 0.52 * gear_scale, size * 0.88 * gear_scale), border_radius=6)
            pygame.draw.circle(canvas, (255, 185, 60), (int(cx - size * 1.08 * gear_scale), int(cy + size * 0.72 * gear_scale)), int(size * 0.09 * gear_scale))

        elif gear == "ramjet":
            pygame.draw.rect(canvas, (70, 76, 92), (cx - size * 1.15 * gear_scale, cy - size * 0.16 * gear_scale, size * 0.58 * gear_scale, size * 0.95 * gear_scale), border_radius=7)
            pygame.draw.circle(canvas, (255, 200, 80), (int(cx - size * 1.2 * gear_scale), int(cy + size * 0.74 * gear_scale)), int(size * 0.1 * gear_scale))
            pygame.draw.circle(canvas, (255, 120, 70), (int(cx - size * 1.24 * gear_scale), int(cy + size * 0.74 * gear_scale)), int(size * 0.05 * gear_scale))

        elif gear == "balloon":
            # Thin green pod aligned parallel to penguin body, with rear exhaust for forward thrust.
            pod_x = cx - size * 1.05 * gear_scale
            pod_y = cy - size * 0.18 * gear_scale
            pod_w = size * 1.22 * gear_scale
            pod_h = size * 0.24 * gear_scale
            pygame.draw.ellipse(canvas, (90, 210, 110), (pod_x, pod_y, pod_w, pod_h))
            pygame.draw.ellipse(canvas, (160, 235, 170), (pod_x + size * 0.08 * gear_scale, pod_y + size * 0.04 * gear_scale, pod_w * 0.45, pod_h * 0.35))
            # Mount struts to body.
            pygame.draw.line(canvas, (120, 120, 120), (cx - size * 0.08 * gear_scale, cy + size * 0.04 * gear_scale), (cx - size * 0.32 * gear_scale, cy - size * 0.02 * gear_scale), 2)
            pygame.draw.line(canvas, (120, 120, 120), (cx - size * 0.08 * gear_scale, cy + size * 0.24 * gear_scale), (cx - size * 0.32 * gear_scale, cy + size * 0.12 * gear_scale), 2)
            # Rear nozzle + flame (left side), indicating forward propulsion.
            pygame.draw.rect(canvas, (110, 110, 120), (pod_x - size * 0.08 * gear_scale, pod_y + size * 0.07 * gear_scale, size * 0.09 * gear_scale, size * 0.1 * gear_scale), border_radius=2)
            pygame.draw.polygon(canvas, (255, 170, 70), [
                (pod_x - size * 0.1 * gear_scale, pod_y + size * 0.12 * gear_scale),
                (pod_x - size * 0.32 * gear_scale, pod_y + size * 0.08 * gear_scale),
                (pod_x - size * 0.32 * gear_scale, pod_y + size * 0.16 * gear_scale),
            ])

        rotated_overlay = pygame.transform.rotozoom(canvas, angle, 1.0)
        overlay_rect = rotated_overlay.get_rect(center=(px, py))
        surface.blit(rotated_overlay, overlay_rect)


if __name__ == "__main__":
    game = Game()
    game.run()

