import math
import pygame
from src.constants import *
from src.player import Player
from src.environment import Environment
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
        self.flight_breakdown = {}
        self.flight_max_speed_mps = 0.0
        self.flight_max_altitude_m = 0.0
        self.flight_duration_s = 0.0
        self.flight_destruction_points = 0
        self.low_speed_frames = 0
        self.shop_catalog_category = None
        self.toast_text = ""
        self.toast_color = (225, 235, 248)
        self.toast_timer = 0.0
        self.controls_hint_timer = 8.0
        self.was_ramp_locked = False
        self.ramp_detached_once = False

    def set_toast(self, text, color=(225, 235, 248), duration=2.0):
        """Show a short transient message for UX feedback."""
        self.toast_text = text
        self.toast_color = color
        self.toast_timer = max(0.0, float(duration))
    
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
        if "ramp_height_level" not in save_data:
            save_data["ramp_height_level"] = 0
        save_data["ramp_height_level"] = max(0, min(int(save_data["ramp_height_level"]), len(RAMP_HEIGHT_TIERS) - 1))
        if "ramp_drop_level" not in save_data:
            save_data["ramp_drop_level"] = 0
        save_data["ramp_drop_level"] = max(0, min(int(save_data["ramp_drop_level"]), len(RAMP_DROP_TIERS) - 1))

        # Gear sanity: a tier can only be equipped if it is unlocked in the matching category.
        did_sanitize = False
        if save_data.get("equipped_sled") not in save_data["unlocked_sleds"]:
            save_data["equipped_sled"] = None
            did_sanitize = True
        if save_data.get("equipped_glider") not in save_data["unlocked_gliders"]:
            save_data["equipped_glider"] = None
            did_sanitize = True
        if save_data.get("equipped_booster") not in save_data["unlocked_boosters"]:
            save_data["equipped_booster"] = None
            did_sanitize = True

        self.game_data = save_data
        if did_sanitize:
            self.save_game()
        
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
        
        # Upgrade screen buttons + box layout + catalog controls.
        self.buttons["upgrade"] = [
            Button(50, SCREEN_HEIGHT - 80, 120, 60, "Back", (100, 100, 100)),
            Button(SCREEN_WIDTH - 190, 86, 150, 30, "Upgrade", (100, 150, 100)),
            Button(SCREEN_WIDTH - 190, 136, 150, 30, "Upgrade", (100, 150, 100)),
        ]
        self.buttons["upgrade_boxes"] = {
            "sled": Button(120, 230, 420, 210, "Sled", (70, 110, 150)),
            "glider": Button(660, 230, 420, 210, "Glider", (70, 120, 165)),
            "booster": Button(120, 490, 420, 210, "Engine", (75, 115, 155)),
            "future": Button(660, 490, 420, 210, "Reserved", (55, 65, 85)),
        }
        self.buttons["catalog_close"] = Button(910, 190, 160, 36, "Close", (120, 90, 90))
        self.buttons["catalog_items"] = [
            Button(860, 255 + i * 92, 180, 38, "", (100, 150, 100)) for i in range(4)
        ]
        
        # Results screen buttons
        self.buttons["results"] = [
            Button(SCREEN_WIDTH // 2 - 75, 450, 150, 60, "Continue", (100, 150, 100)),
        ]
    
    def start_flight(self):
        """Initialize a new flight."""
        self.environment = Environment(
            ramp_height_level=self.game_data.get("ramp_height_level", 0),
            ramp_drop_level=self.game_data.get("ramp_drop_level", 0),
        )
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
        self.flight_breakdown = {}
        self.flight_max_speed_mps = 0.0
        self.flight_max_altitude_m = 0.0
        self.flight_duration_s = 0.0
        self.flight_destruction_points = 0
        self.low_speed_frames = 0
        self.was_ramp_locked = False
        self.ramp_detached_once = False
        
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
                elif event.key == pygame.K_RETURN:
                    if self.state == STATE_MENU:
                        self.start_flight()
                    elif self.state == STATE_RESULTS:
                        self.state = STATE_MENU
                elif event.key == pygame.K_b and self.state == STATE_UPGRADE:
                    self.state = STATE_MENU
            
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
                        self.start_flight()
                    elif i == 1:  # Gear Shop
                        self.state = STATE_UPGRADE
                    elif i == 2:  # Settings
                        pass  # TODO: Settings
                    elif i == 3:  # Quit
                        self.running = False
        
        elif self.state == STATE_UPGRADE:
            if self.buttons["upgrade"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
                self.shop_catalog_category = None
                return

            if self.buttons["upgrade"][1].is_clicked(mouse_pos, True):
                self.try_purchase_ramp_height()
            if self.buttons["upgrade"][2].is_clicked(mouse_pos, True):
                self.try_purchase_ramp_drop()

            if self.shop_catalog_category:
                if self.buttons["catalog_close"].is_clicked(mouse_pos, True):
                    self.shop_catalog_category = None
                    return

                entries = self.get_catalog_entries(self.shop_catalog_category)
                for i, button in enumerate(self.buttons["catalog_items"]):
                    if i < len(entries) and button.is_clicked(mouse_pos, True):
                        gear_name = entries[i][0]
                        self.try_purchase_gear(self.shop_catalog_category, gear_name)
                return

            if self.buttons["upgrade_boxes"]["sled"].is_clicked(mouse_pos, True):
                self.shop_catalog_category = "sled"
            elif self.buttons["upgrade_boxes"]["glider"].is_clicked(mouse_pos, True):
                self.shop_catalog_category = "glider"
            elif self.buttons["upgrade_boxes"]["booster"].is_clicked(mouse_pos, True):
                self.shop_catalog_category = "booster"
        
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
            self.save_game()
            self.set_toast(f"Equipped {gear_info['name']}", (120, 210, 150), duration=1.8)
        else:
            if self.player.coins >= gear_info["cost"]:
                self.player.coins -= gear_info["cost"]
                self.game_data[unlock_key].append(gear_name)
                equip_fn(gear_name)
                self.game_data[equip_key] = gear_name
                self.save_game()
                self.set_toast(f"Purchased {gear_info['name']}", (120, 210, 150), duration=2.1)
            else:
                need = gear_info["cost"] - self.player.coins
                self.set_toast(f"Need {need}$ more", (235, 130, 120), duration=2.0)

    def try_purchase_ramp_height(self):
        """Advance the launch ramp height upgrade."""
        current_level = int(self.game_data.get("ramp_height_level", 0))
        next_level = current_level + 1
        if next_level >= len(RAMP_HEIGHT_TIERS):
            return

        next_tier = RAMP_HEIGHT_TIERS[next_level]
        if self.player.coins >= next_tier["cost"]:
            self.player.coins -= next_tier["cost"]
            self.game_data["ramp_height_level"] = next_level
            self.save_game()
            self.set_toast(f"Ramp Height upgraded to Lv {next_level + 1}", (120, 210, 150), duration=2.0)
        else:
            need = next_tier["cost"] - self.player.coins
            self.set_toast(f"Need {need}$ more", (235, 130, 120), duration=2.0)

    def try_purchase_ramp_drop(self):
        """Advance the downhill ramp depth upgrade."""
        current_level = int(self.game_data.get("ramp_drop_level", 0))
        next_level = current_level + 1
        if next_level >= len(RAMP_DROP_TIERS):
            return

        next_tier = RAMP_DROP_TIERS[next_level]
        if self.player.coins >= next_tier["cost"]:
            self.player.coins -= next_tier["cost"]
            self.game_data["ramp_drop_level"] = next_level
            self.save_game()
            self.set_toast(f"Ramp Length upgraded to Lv {next_level + 1}", (120, 210, 150), duration=2.0)
        else:
            need = next_tier["cost"] - self.player.coins
            self.set_toast(f"Need {need}$ more", (235, 130, 120), duration=2.0)

    def get_catalog_entries(self, category):
        """Return ordered gear tuples for the selected shop catalog."""
        if category == "sled":
            return list(SLED_TIERS.items())
        if category == "glider":
            return list(GLIDER_TIERS.items())
        if category == "booster":
            return list(BOOSTER_TIERS.items())
        return []

    def _get_terrain_slope_at_x(self, x):
        """Return terrain slope under a world x position."""
        points = self.environment.terrain.points
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            if x1 <= x <= x2:
                dx = (x2 - x1)
                return ((y2 - y1) / dx) if dx != 0 else 0.0
        return 0.0

    def _project_velocity_to_slope(self, slope, preserve_ratio=0.0):
        """Resolve ground contact by removing inward normal velocity and keeping tangent motion."""
        vx0 = self.player.vx
        vy0 = self.player.vy
        norm = math.sqrt(1.0 + slope * slope)
        tx = 1.0 / norm
        ty = slope / norm

        # Inward normal (toward ground in screen-space y-down coordinates).
        nx = -slope / norm
        ny = 1.0 / norm
        vn_inward = (vx0 * nx) + (vy0 * ny)
        if vn_inward > 0.0:
            vx0 -= vn_inward * nx
            vy0 -= vn_inward * ny

        tangential_speed = (vx0 * tx) + (vy0 * ty)

        if preserve_ratio > 0.0:
            # Preserve some pre-impact speed through sharp kink transitions on ice.
            preserve_speed = math.hypot(self.player.vx, self.player.vy) * preserve_ratio
            if abs(tangential_speed) < preserve_speed:
                # Do not force a direction when nearly stopped.
                if tangential_speed > 1e-6:
                    tangential_speed = preserve_speed
                elif tangential_speed < -1e-6:
                    tangential_speed = -preserve_speed

        self.player.vx = tx * tangential_speed
        self.player.vy = ty * tangential_speed

    def _resolve_obstacle_hits(self, controls, dt):
        """Handle obstacle collision damage and destruction rewards during flight."""
        for obstacle in self.environment.hazards:
            if obstacle.destroyed or not obstacle.active:
                continue
            if not obstacle.check_collision(self.player):
                continue

            now_ms = pygame.time.get_ticks()
            if now_ms - obstacle.last_hit_ms < 180:
                continue
            obstacle.last_hit_ms = now_ms

            speed_mps = math.hypot(self.player.vx, self.player.vy) * FPS / PIXELS_PER_METER
            impact_damage = (speed_mps * 0.95) + (6.0 if controls.get("boost", False) else 0.0)
            if not obstacle.destroyed:
                obstacle.hp -= impact_damage

            if obstacle.hp <= 0:
                obstacle.destroyed = True
                obstacle.active = False
                self.flight_destruction_points += obstacle.destruction_points
                self.set_toast(f"Destroyed: {obstacle.name}", (120, 220, 150), duration=1.6)
            else:
                # Incomplete impact bleeds speed but does not hard-stop the run.
                self.player.vx *= 0.82
                self.player.vy *= 0.82

    def _finalize_day(self):
        """Compute earnings from flight stats and transition to result screen."""
        self.flight_distance = self.player.distance_traveled
        distance_money = self.flight_distance * EARNING_K_DISTANCE
        speed_money = self.flight_max_speed_mps * EARNING_L_MAX_SPEED
        altitude_money = self.flight_max_altitude_m * EARNING_M_MAX_ALTITUDE
        duration_money = self.flight_duration_s * EARNING_N_DURATION
        destruction_money = self.flight_destruction_points * EARNING_O_DESTRUCTION

        total = int(distance_money + speed_money + altitude_money + duration_money + destruction_money)
        self.flight_coins_earned = max(0, total)
        self.flight_breakdown = {
            "distance": self.flight_distance,
            "max_speed": self.flight_max_speed_mps,
            "max_altitude": self.flight_max_altitude_m,
            "duration": self.flight_duration_s,
            "destruction": self.flight_destruction_points,
            "distance_money": int(distance_money),
            "speed_money": int(speed_money),
            "altitude_money": int(altitude_money),
            "duration_money": int(duration_money),
            "destruction_money": int(destruction_money),
        }

        self.player.coins += self.flight_coins_earned
        self.game_data["total_coins"] += self.flight_coins_earned
        self.game_data["total_distance"] += self.flight_distance
        self.save_game()
        self.state = STATE_RESULTS
    
    def update(self, controls, dt=1.0 / FPS):
        """Update game state."""
        if self.toast_timer > 0.0:
            self.toast_timer = max(0.0, self.toast_timer - dt)

        if self.state == STATE_PLAYING:
            self.controls_hint_timer = max(0.0, self.controls_hint_timer - dt)
            prev_x = self.player.x
            prev_y = self.player.y
            prev_speed = math.hypot(self.player.vx, self.player.vy)
            self.flight_duration_s += dt

            terrain_y = self.environment.terrain.get_ground_y_at(self.player.x)
            slope = self._get_terrain_slope_at_x(self.player.x)
            surface_type = self.environment.terrain.get_surface_type_at(self.player.x)
            ice_end_x = self.environment.terrain.ice_end_x
            in_launch_ramp_zone = (surface_type == "ice" and self.player.x <= ice_end_x)

            # One-way latch: once you leave launch-ramp lock, never reattach to ice ramp geometry this run.
            if (not self.ramp_detached_once) and (
                self.player.x > (ice_end_x + 2)
                or (self.was_ramp_locked and not in_launch_ramp_zone)
            ):
                self.ramp_detached_once = True

            force_ramp_lock = in_launch_ramp_zone and (not self.ramp_detached_once)
            left_ramp_this_frame = self.was_ramp_locked and (not force_ramp_lock)

            # Ground contact: allow small tolerance so steep up-ramp transitions stay attached.
            bottom = self.player.y + self.player.size
            grounded = (bottom >= terrain_y - 3) and (bottom <= terrain_y + 18)
            if self.ramp_detached_once and in_launch_ramp_zone:
                grounded = False
            if force_ramp_lock:
                grounded = True
            if grounded:
                self.player.y = terrain_y - self.player.size

            # Material friction: ice is slippery, snow is much stickier.
            if surface_type == "ice":
                friction = ICE_FRICTION
            elif surface_type == "snow":
                friction = SNOW_FRICTION
            else:
                friction = DEFAULT_GROUND_FRICTION

            # Mid-ramp flat ice should carry speed with much less drag.
            if grounded and surface_type == "ice" and abs(slope) <= FLAT_ICE_SLOPE_THRESHOLD:
                friction = max(friction, FLAT_ICE_FRICTION)

            # Very low slope: treat as effectively zero friction (no drag).
            if grounded and surface_type == "ice" and abs(slope) <= ZERO_FRICTION_SLOPE_THRESHOLD:
                friction = 1.0

            # Sled detaches once the penguin leaves the launch ramp geometry.
            if self.player.sled_attached and self.player.x > (ice_end_x + 2):
                self.player.sled_attached = False

            # Sled reduces ramp friction while attached and on ice.
            if grounded and surface_type == "ice" and self.player.sled_attached and self.player.sled in SLED_TIERS:
                sled_mult = SLED_TIERS[self.player.sled]["ramp_friction_mult"]
                friction = min(0.9995, friction * sled_mult)

            # Ramp friction framework is preserved, but current tuning is true no-loss on ramp.
            if grounded and surface_type == "ice":
                _ramp_friction_preview = 1.0 - ((1.0 - friction) / RAMP_FRICTION_LOSS_DIVISOR)
                friction = 1.0


            self.player.update(
                controls,
                terrain_slope=slope,
                boosting=controls.get("boost", False),
                grounded=grounded,
                surface_friction=friction,
                can_rotate=not (grounded and surface_type == "ice"),
                dt=dt,
            )

            # Sweep along the frame motion to prevent tunneling through steep ramp segments.
            dx = self.player.x - prev_x
            dy = self.player.y - prev_y
            sweep_steps = max(2, int(abs(dx) / max(2.0, self.player.size * 0.35)) + 1)
            hit_ground = False
            for step in range(1, sweep_steps + 1):
                t = step / float(sweep_steps)
                sx = prev_x + dx * t
                sy = prev_y + dy * t
                sy_bottom = sy + self.player.size
                sample_ground_y = self.environment.terrain.get_ground_y_at(sx)
                sample_slope = self._get_terrain_slope_at_x(sx)

                # Ignore near-vertical terrain transitions (e.g., snow step wall).
                if abs(sample_slope) > 2.5:
                    continue

                if sy_bottom >= sample_ground_y:
                    sample_surface = self.environment.terrain.get_surface_type_at(sx)
                    if sample_surface == "ice" and self.ramp_detached_once:
                        continue
                    self.player.x = sx
                    self.player.y = sample_ground_y - self.player.size
                    preserve_ratio = 0.9 if (sample_surface == "ice" and abs(sample_slope) < 0.12) else 0.0
                    self._project_velocity_to_slope(sample_slope, preserve_ratio=preserve_ratio)
                    slope = sample_slope
                    surface_type = sample_surface
                    grounded = True
                    hit_ground = True
                    break

            if not hit_ground:
                terrain_y = self.environment.terrain.get_ground_y_at(self.player.x)
                slope = self._get_terrain_slope_at_x(self.player.x)
                if abs(slope) <= 2.5 and self.player.y + self.player.size >= terrain_y:
                    sample_surface = self.environment.terrain.get_surface_type_at(self.player.x)
                    if sample_surface == "ice" and self.ramp_detached_once:
                        sample_surface = None
                    if sample_surface is None:
                        pass
                    else:
                        self.player.y = terrain_y - self.player.size
                        preserve_ratio = 0.9 if (sample_surface == "ice" and abs(slope) < 0.12) else 0.0
                        self._project_velocity_to_slope(slope, preserve_ratio=preserve_ratio)
                        surface_type = sample_surface
                        grounded = True

            # Hard lock to ramp while still on launch ice so the penguin cannot drop off early.
            surface_type = self.environment.terrain.get_surface_type_at(self.player.x)
            if (not self.ramp_detached_once) and surface_type == "ice" and self.player.x <= ice_end_x:
                lock_terrain_y = self.environment.terrain.get_ground_y_at(self.player.x)
                lock_slope = self._get_terrain_slope_at_x(self.player.x)
                self.player.y = lock_terrain_y - self.player.size
                self._project_velocity_to_slope(lock_slope, preserve_ratio=0.0)
                grounded = True
                slope = lock_slope

            # Keep launch transition continuous: no sudden speed pop on ramp exit.
            if left_ramp_this_frame and not controls.get("boost", False):
                current_speed = math.hypot(self.player.vx, self.player.vy)
                max_exit_speed = (prev_speed * 1.02) + 0.08
                if current_speed > max_exit_speed and current_speed > 1e-6:
                    scale = max_exit_speed / current_speed
                    self.player.vx *= scale
                    self.player.vy *= scale

            self.was_ramp_locked = ((not self.ramp_detached_once) and self.environment.terrain.get_surface_type_at(self.player.x) == "ice" and self.player.x <= ice_end_x)

            self._resolve_obstacle_hits(controls, dt)

            self.environment.update()

            speed = (self.player.vx ** 2 + self.player.vy ** 2) ** 0.5
            speed_mps = speed * FPS / PIXELS_PER_METER
            self.flight_max_speed_mps = max(self.flight_max_speed_mps, speed_mps)

            terrain_y_now = self.environment.terrain.get_ground_y_at(self.player.x)
            altitude_m = max(0.0, (terrain_y_now - (self.player.y + self.player.size)) / PIXELS_PER_METER)
            self.flight_max_altitude_m = max(self.flight_max_altitude_m, altitude_m)

            # End the day if the penguin has effectively stopped.
            if grounded and speed < 0.2:
                self.low_speed_frames += 1
            else:
                self.low_speed_frames = 0

            if self.low_speed_frames >= 30:
                self._finalize_day()
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
                self._finalize_day()
    
    def draw(self):
        """Render game."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button states
        if self.state == STATE_MENU:
            for button in self.buttons["menu"]:
                button.update(mouse_pos)
            self.ui_manager.draw_menu(self.screen, self.buttons["menu"])
        
        elif self.state == STATE_UPGRADE:
            for button in self.buttons["upgrade"]:
                button.update(mouse_pos)
            for button in self.buttons["upgrade_boxes"].values():
                button.update(mouse_pos)
            if self.shop_catalog_category:
                self.buttons["catalog_close"].update(mouse_pos)
                for button in self.buttons["catalog_items"]:
                    button.update(mouse_pos)
            self.ui_manager.draw_upgrade_screen(
                self.screen,
                self.player,
                self.game_data,
                self.buttons["upgrade"],
                self.buttons["upgrade_boxes"],
                self.shop_catalog_category,
                self.get_catalog_entries(self.shop_catalog_category),
                self.buttons["catalog_items"],
                self.buttons["catalog_close"],
            )
        
        elif self.state == STATE_PLAYING:
            # Draw game with camera offset
            # Draw background (not affected by camera)
            # Sky gradient for depth
            for y in range(SCREEN_HEIGHT):
                ratio = y / SCREEN_HEIGHT
                r = int(COLOR_SKY[0] + (COLOR_SKY_DARK[0] - COLOR_SKY[0]) * ratio)
                g = int(COLOR_SKY[1] + (COLOR_SKY_DARK[1] - COLOR_SKY[1]) * ratio)
                b = int(COLOR_SKY[2] + (COLOR_SKY_DARK[2] - COLOR_SKY[2]) * ratio)
                pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
            
            # Draw game elements with camera offset applied
            self.draw_terrain_with_camera(self.screen)
            self.draw_player_with_camera(self.screen)
            
            self.ui_manager.draw_stats(self.screen, self.player, self.environment)
            terrain_y = self.environment.terrain.get_ground_y_at(self.player.x)
            self.ui_manager.draw_flight_hud(self.screen, self.player, terrain_y)
            if self.controls_hint_timer > 0.0:
                self.ui_manager.draw_controls_hint(self.screen)

        if self.toast_timer > 0.0 and self.toast_text:
            self.ui_manager.draw_toast(self.screen, self.toast_text, self.toast_color)
        
        elif self.state == STATE_RESULTS:
            for button in self.buttons["results"]:
                button.update(mouse_pos)
            self.ui_manager.draw_results_screen(self.screen, self.flight_distance, 
                                               self.flight_coins_earned, self.flight_breakdown,
                                               self.buttons["results"])
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        fixed_dt = 1.0 / FPS
        accumulator = 0.0
        while self.running:
            frame_dt = self.clock.tick(FPS) / 1000.0
            # Clamp long frames to avoid giant catch-up jumps after stalls.
            frame_dt = min(frame_dt, 0.1)
            accumulator += frame_dt

            controls = self.handle_input()
            substeps = 0
            while accumulator >= fixed_dt and substeps < 4:
                self.update(controls, fixed_dt)
                accumulator -= fixed_dt
                substeps += 1

            # If rendering outpaces updates, still step once so controls feel responsive.
            if substeps == 0:
                self.update(controls, fixed_dt)
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
            cloud_world_y = terrain.get_ground_y_at(cloud["x"]) - cloud["terrain_gap"]
            cy = cloud_world_y - offset_y
            s = cloud["s"]
            if -120 < cx < SCREEN_WIDTH + 120:
                # Cloud shadow for depth
                pygame.draw.circle(surface, (220, 225, 235), (int(cx + 1), int(cy + 1)), int(s * 1.05))
                # Main cloud
                pygame.draw.circle(surface, (250, 251, 255), (int(cx), int(cy)), s)
                pygame.draw.circle(surface, (250, 251, 255), (int(cx + s * 0.9), int(cy + s * 0.05)), int(s * 1.05))
                pygame.draw.circle(surface, (250, 251, 255), (int(cx - s * 0.8), int(cy + s * 0.05)), int(s * 0.85))
                # Cloud highlight
                pygame.draw.circle(surface, (255, 255, 255), (int(cx + s * 0.2), int(cy - s * 0.35)), int(s * 0.95))
        
        # Draw terrain base polygon (snow shadow)
        if len(terrain.points) > 1:
            terrain_points = [(x - offset, y - offset_y) for x, y in terrain.points]
            terrain_points.append((self.environment.terrain.width - offset, SCREEN_HEIGHT * 2))
            terrain_points.append((0 - offset, SCREEN_HEIGHT * 2))
            
            pygame.draw.polygon(surface, (200, 215, 235), terrain_points)

        # Draw top surface by material.
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
            # Shadow line below surface for depth
            pygame.draw.line(surface, (200, 220, 240), (x1 - offset, y1 - offset_y + 2), (x2 - offset, y2 - offset_y + 2), 1)

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
                        (170, 225, 245),
                        (mx - offset - 3, my - offset_y - 1),
                        (mx - offset + 3, my - offset_y + 1),
                        1,
                    )
                    # Additional subtle marks for ice texture
                    seed = int(mx * 0.37 + my * 1.91 + j * 13 + i * 101)
                    rand_d = ((seed * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF
                    if rand_d > 0.7:
                        pygame.draw.line(surface, (190, 235, 252), (mx - offset, my - offset_y - 2), (mx - offset + 1, my - offset_y + 2), 1)
        
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
                # Wind particles with gradient effect
                alpha = int(100 * (p["life"] / 30))
                color = (200, 220, 240)
                pygame.draw.circle(surface, color, (int(p["x"] - offset), int(p["y"] - offset_y)), size)
        
        # Draw hazards with camera offset
        for hazard in self.environment.hazards:
            if hazard.destroyed:
                continue
            hazard_screen_x = hazard.x - offset
            hazard_screen_y = hazard.y - offset_y
            if -180 < hazard_screen_x < SCREEN_WIDTH + 180:  # Only draw if visible
                if hazard.type == "snowman":
                    pygame.draw.circle(surface, (250, 252, 255), (int(hazard_screen_x), int(hazard_screen_y - 18)), 16)
                    pygame.draw.circle(surface, (250, 252, 255), (int(hazard_screen_x), int(hazard_screen_y - 44)), 12)
                    pygame.draw.circle(surface, (35, 40, 45), (int(hazard_screen_x - 4), int(hazard_screen_y - 47)), 2)
                    pygame.draw.circle(surface, (35, 40, 45), (int(hazard_screen_x + 4), int(hazard_screen_y - 47)), 2)
                    pygame.draw.polygon(surface, (255, 140, 30), [
                        (hazard_screen_x + 1, hazard_screen_y - 43),
                        (hazard_screen_x + 12, hazard_screen_y - 41),
                        (hazard_screen_x + 1, hazard_screen_y - 39),
                    ])
                elif hazard.type == "snowmound":
                    pygame.draw.ellipse(surface, (235, 242, 252), (hazard_screen_x - 42, hazard_screen_y - 38, 84, 40))
                    pygame.draw.ellipse(surface, (222, 232, 244), (hazard_screen_x - 36, hazard_screen_y - 28, 72, 24))
                elif hazard.type == "rocky_hill":
                    pygame.draw.polygon(surface, (120, 125, 132), [
                        (hazard_screen_x - 56, hazard_screen_y),
                        (hazard_screen_x - 24, hazard_screen_y - 48),
                        (hazard_screen_x + 8, hazard_screen_y - 62),
                        (hazard_screen_x + 56, hazard_screen_y),
                    ])
                    pygame.draw.line(surface, (148, 156, 168), (hazard_screen_x - 16, hazard_screen_y - 32), (hazard_screen_x + 24, hazard_screen_y - 12), 2)
                elif hazard.type == "iceberg":
                    pygame.draw.polygon(surface, (170, 220, 250), [
                        (hazard_screen_x - 66, hazard_screen_y),
                        (hazard_screen_x - 38, hazard_screen_y - 78),
                        (hazard_screen_x + 8, hazard_screen_y - 108),
                        (hazard_screen_x + 62, hazard_screen_y - 56),
                        (hazard_screen_x + 76, hazard_screen_y),
                    ])
                    pygame.draw.polygon(surface, (210, 242, 255), [
                        (hazard_screen_x - 20, hazard_screen_y - 64),
                        (hazard_screen_x + 10, hazard_screen_y - 92),
                        (hazard_screen_x + 34, hazard_screen_y - 58),
                    ])
                elif hazard.type == "glacier_wall":
                    pygame.draw.rect(surface, (150, 195, 235), (hazard_screen_x - 84, hazard_screen_y - 220, 168, 220), border_radius=6)
                    pygame.draw.rect(surface, (200, 236, 255), (hazard_screen_x - 72, hazard_screen_y - 212, 48, 204), border_radius=4)
                    pygame.draw.rect(surface, (182, 224, 248), (hazard_screen_x - 14, hazard_screen_y - 212, 42, 204), border_radius=4)
                    pygame.draw.rect(surface, (205, 240, 255), (hazard_screen_x + 34, hazard_screen_y - 212, 40, 204), border_radius=4)

                # HP bar + label
                bar_w = max(44, int(hazard.width * 0.9))
                bar_x = int(hazard_screen_x - bar_w * 0.5)
                bar_y = int(hazard_screen_y - hazard.height - 24)
                hp_ratio = max(0.0, min(1.0, hazard.hp / max(1.0, hazard.max_hp)))
                pygame.draw.rect(surface, (40, 45, 55), (bar_x, bar_y, bar_w, 7), border_radius=3)
                pygame.draw.rect(surface, (255, 125, 95), (bar_x, bar_y, int(bar_w * hp_ratio), 7), border_radius=3)
                pygame.draw.rect(surface, (235, 235, 240), (bar_x, bar_y, bar_w, 7), 1, border_radius=3)
                label = self.ui_manager.font_small.render(hazard.name, True, (235, 242, 250))
                surface.blit(label, (bar_x, bar_y - 16))
    
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
            body_left = size * (2.0 - 3.45 * 0.5)
            body_top = size * (1.5 - 1.50 * 0.5)
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
            pygame.draw.polygon(sprite, (30, 35, 45), half_body)
            # Dark shading on the back
            pygame.draw.polygon(sprite, (15, 18, 25), [(cx_body - size * 0.05, cy_body - ry), (cx_body, cy_body - ry), (cx_body, cy_body + ry), (cx_body - size * 0.05, cy_body + ry)])

            # White belly patch in the lower-front part.
            belly_left = cx_body + size * 0.42
            belly_top = cy_body + size * 0.02
            belly_w = size * 1.25
            belly_h = size * 0.62
            pygame.draw.ellipse(sprite, (245, 248, 250), (belly_left, belly_top, belly_w, belly_h))
            # Subtle belly shading
            pygame.draw.ellipse(sprite, (225, 235, 242), (belly_left + size * 0.08, belly_top + size * 0.15, belly_w - size * 0.16, belly_h * 0.5))

            # Side beak at front.
            pygame.draw.polygon(sprite, (255, 150, 0), [
                (cx_body + rx * 0.97, cy_body - size * 0.08),
                (cx_body + rx * 1.36, cy_body),
                (cx_body + rx * 0.97, cy_body + size * 0.09),
            ])
            pygame.draw.polygon(sprite, (200, 110, 0), [
                (cx_body + rx * 0.97, cy_body - size * 0.08),
                (cx_body + rx * 1.15, cy_body - size * 0.02),
                (cx_body + rx * 0.97, cy_body + size * 0.03),
            ])

            # Eye near front/top.
            eye_x = int(cx_body + rx * 0.60)
            eye_y = int(cy_body - ry * 0.30)
            pygame.draw.circle(sprite, (255, 255, 255), (eye_x, eye_y), int(size * 0.12))
            pygame.draw.circle(sprite, (10, 10, 20), (eye_x + int(size * 0.03), eye_y - int(size * 0.02)), int(size * 0.06))
            pygame.draw.circle(sprite, (255, 255, 255), (eye_x + int(size * 0.05), eye_y - int(size * 0.03)), int(size * 0.02))

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
                "the_plank": (160, 110, 60),
                "plank_mk2": (145, 95, 50),
                "good_ol_sled": (130, 75, 35),
                "bobsled": (65, 100, 145),
            }[player.sled]
            pygame.draw.ellipse(
                canvas,
                sled_color,
                (cx - size * 0.7 * gear_scale, cy + size * 0.72 * gear_scale, size * 1.55 * gear_scale, size * 0.28 * gear_scale),
            )
            # Sled shading/highlight
            pygame.draw.ellipse(
                canvas,
                tuple(min(c + 40, 255) for c in sled_color),
                (cx - size * 0.68 * gear_scale, cy + size * 0.73 * gear_scale, size * 1.40 * gear_scale, size * 0.08 * gear_scale),
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
            # Kite shading
            pygame.draw.polygon(canvas, (90, 220, 115), [
                (kite_x - kite_w * 0.4 + slant, kite_y - kite_h * 0.3),
                (kite_x + kite_w * 0.3 + slant, kite_y - kite_h * 0.3),
                (kite_x + kite_w * 0.25 - slant, kite_y + kite_h * 0.2),
                (kite_x - kite_w * 0.35 - slant, kite_y + kite_h * 0.2),
            ])
            pygame.draw.line(
                canvas,
                (160, 245, 175),
                (kite_x - kite_w * 0.45 + slant, kite_y - kite_h * 0.18),
                (kite_x + kite_w * 0.45 + slant, kite_y - kite_h * 0.18),
                2,
            )

        elif player.glider in ("old_glider", "hand_glider"):
            if player.glider == "old_glider":
                wing_len = 0.95
                wing_thickness = 0.10
                mast_h = 0.62
                color_main = (85, 120, 160)
                color_highlight = (180, 220, 255)
                color_shadow = (60, 85, 120)
            else:  # hand_glider
                wing_len = 1.20
                wing_thickness = 0.11
                mast_h = 0.68
                color_main = (80, 130, 180)
                color_highlight = (200, 235, 255)
                color_shadow = (50, 75, 110)

            # Back-mounted anchor (penguin faces right, so back is left side).
            mast_base = (cx - size * 0.12 * gear_scale, cy + size * 0.05 * gear_scale)
            mast_top = (cx - size * 0.18 * gear_scale, cy - size * (mast_h - 0.28) * gear_scale)

            # Strap/mast from penguin to glider.
            pygame.draw.line(canvas, (125, 125, 125), mast_base, mast_top, 2)

            # Thin side-view wing profile above penguin.
            wing_x = mast_top[0]
            wing_y = mast_top[1] + size * 0.18 * gear_scale
            # Wing shadow for depth
            pygame.draw.polygon(canvas, color_shadow, [
                (wing_x + size * 0.14 * gear_scale, wing_y - size * wing_thickness * gear_scale + 1),
                (wing_x - size * wing_len * gear_scale + 1, wing_y - size * (wing_thickness * 0.55) * gear_scale + 1),
                (wing_x - size * (wing_len - 0.18) * gear_scale, wing_y + size * wing_thickness * gear_scale + 1),
                (wing_x + size * 0.1 * gear_scale, wing_y + size * (wing_thickness * 0.7) * gear_scale + 1),
            ])
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
                2,
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
        nozzle_pos = None
        if gear == "sugar_rocket":
            # Side-mounted model rocket with pointed nose (front/right) and rear nozzle (left).
            body_x = cx - size * 0.78 * gear_scale
            body_y = cy - size * 0.02 * gear_scale
            body_w = size * 0.86 * gear_scale
            body_h = size * 0.22 * gear_scale
            pygame.draw.rect(canvas, (205, 212, 225), (body_x, body_y, body_w, body_h), border_radius=5)
            pygame.draw.rect(canvas, (235, 240, 250), (body_x + size * 0.08 * gear_scale, body_y + size * 0.03 * gear_scale, body_w * 0.58, body_h * 0.28), border_radius=3)
            nose = [
                (body_x + body_w, body_y + body_h * 0.5),
                (body_x + body_w + size * 0.16 * gear_scale, body_y + body_h * 0.3),
                (body_x + body_w + size * 0.16 * gear_scale, body_y + body_h * 0.7),
            ]
            pygame.draw.polygon(canvas, (210, 80, 80), nose)
            fin_back = [
                (body_x + size * 0.08 * gear_scale, body_y + body_h * 0.02),
                (body_x - size * 0.09 * gear_scale, body_y - size * 0.07 * gear_scale),
                (body_x + size * 0.12 * gear_scale, body_y + body_h * 0.36),
            ]
            fin_low = [
                (body_x + size * 0.08 * gear_scale, body_y + body_h * 0.98),
                (body_x - size * 0.09 * gear_scale, body_y + body_h + size * 0.07 * gear_scale),
                (body_x + size * 0.12 * gear_scale, body_y + body_h * 0.64),
            ]
            pygame.draw.polygon(canvas, (185, 65, 65), fin_back)
            pygame.draw.polygon(canvas, (185, 65, 65), fin_low)
            pygame.draw.rect(canvas, (95, 100, 115), (body_x - size * 0.09 * gear_scale, body_y + body_h * 0.32, size * 0.1 * gear_scale, body_h * 0.36), border_radius=2)
            pygame.draw.line(canvas, (95, 100, 110), (cx - size * 0.08 * gear_scale, cy + size * 0.05 * gear_scale), (body_x + size * 0.18 * gear_scale, body_y + body_h * 0.25), 2)
            pygame.draw.line(canvas, (95, 100, 110), (cx - size * 0.08 * gear_scale, cy + size * 0.21 * gear_scale), (body_x + size * 0.18 * gear_scale, body_y + body_h * 0.75), 2)
            nozzle_pos = (body_x - size * 0.09 * gear_scale, body_y + body_h * 0.5)

        elif gear == "pulse_jet":
            # Long skinny pulse jet with thicker intake/front section.
            tube_x = cx - size * 1.02 * gear_scale
            tube_y = cy + size * 0.03 * gear_scale
            tube_w = size * 1.20 * gear_scale
            tube_h = size * 0.13 * gear_scale
            pygame.draw.rect(canvas, (105, 112, 126), (tube_x, tube_y, tube_w, tube_h), border_radius=3)
            pygame.draw.rect(canvas, (145, 152, 168), (tube_x + size * 0.08 * gear_scale, tube_y + size * 0.02 * gear_scale, tube_w * 0.65, tube_h * 0.24), border_radius=2)
            intake_x = tube_x + tube_w - size * 0.02 * gear_scale
            intake_y = tube_y - size * 0.03 * gear_scale
            intake_w = size * 0.28 * gear_scale
            intake_h = size * 0.19 * gear_scale
            pygame.draw.ellipse(canvas, (120, 128, 144), (intake_x, intake_y, intake_w, intake_h))
            pygame.draw.ellipse(canvas, (82, 88, 102), (intake_x + size * 0.04 * gear_scale, intake_y + size * 0.03 * gear_scale, intake_w * 0.66, intake_h * 0.66))
            pygame.draw.line(canvas, (95, 100, 110), (cx - size * 0.04 * gear_scale, cy + size * 0.05 * gear_scale), (tube_x + size * 0.36 * gear_scale, tube_y + tube_h * 0.2), 2)
            pygame.draw.line(canvas, (95, 100, 110), (cx - size * 0.04 * gear_scale, cy + size * 0.22 * gear_scale), (tube_x + size * 0.36 * gear_scale, tube_y + tube_h * 0.8), 2)
            nozzle_pos = (tube_x - size * 0.03 * gear_scale, tube_y + tube_h * 0.5)

        elif gear == "ramjet":
            # Airplane-style ramjet nacelle with intake lip and tapered exhaust.
            nacelle_x = cx - size * 1.00 * gear_scale
            nacelle_y = cy - size * 0.03 * gear_scale
            nacelle_w = size * 1.08 * gear_scale
            nacelle_h = size * 0.24 * gear_scale
            pygame.draw.ellipse(canvas, (98, 112, 136), (nacelle_x, nacelle_y, nacelle_w, nacelle_h))
            pygame.draw.ellipse(canvas, (145, 168, 195), (nacelle_x + size * 0.10 * gear_scale, nacelle_y + size * 0.04 * gear_scale, nacelle_w * 0.45, nacelle_h * 0.25))
            intake_cx = nacelle_x + nacelle_w + size * 0.03 * gear_scale
            intake_cy = nacelle_y + nacelle_h * 0.5
            intake_r = size * 0.12 * gear_scale
            pygame.draw.circle(canvas, (168, 184, 206), (int(intake_cx), int(intake_cy)), int(intake_r))
            pygame.draw.circle(canvas, (70, 78, 94), (int(intake_cx), int(intake_cy)), int(intake_r * 0.58))
            exhaust = [
                (nacelle_x - size * 0.20 * gear_scale, nacelle_y + nacelle_h * 0.35),
                (nacelle_x, nacelle_y + nacelle_h * 0.12),
                (nacelle_x, nacelle_y + nacelle_h * 0.88),
                (nacelle_x - size * 0.20 * gear_scale, nacelle_y + nacelle_h * 0.65),
            ]
            pygame.draw.polygon(canvas, (82, 95, 118), exhaust)
            pygame.draw.line(canvas, (95, 100, 110), (cx - size * 0.02 * gear_scale, cy + size * 0.08 * gear_scale), (nacelle_x + size * 0.34 * gear_scale, nacelle_y + nacelle_h * 0.3), 2)
            pygame.draw.line(canvas, (95, 100, 110), (cx - size * 0.02 * gear_scale, cy + size * 0.24 * gear_scale), (nacelle_x + size * 0.34 * gear_scale, nacelle_y + nacelle_h * 0.7), 2)
            nozzle_pos = (nacelle_x - size * 0.20 * gear_scale, nacelle_y + nacelle_h * 0.5)

        elif gear == "balloon":
            # Thin green pod aligned parallel to penguin body, with rear exhaust for forward thrust.
            pod_x = cx - size * 1.05 * gear_scale
            pod_y = cy - size * 0.18 * gear_scale
            pod_w = size * 1.22 * gear_scale
            pod_h = size * 0.24 * gear_scale
            pygame.draw.ellipse(canvas, (100, 220, 120), (pod_x, pod_y, pod_w, pod_h))
            # Balloon highlight
            pygame.draw.ellipse(canvas, (180, 245, 190), (pod_x + size * 0.08 * gear_scale, pod_y + size * 0.04 * gear_scale, pod_w * 0.45, pod_h * 0.35))
            # Balloon shadow
            pygame.draw.ellipse(canvas, (70, 180, 90), (pod_x - 1, pod_y + 1, pod_w - 2, pod_h - 2), 2)
            # Mount struts to body.
            pygame.draw.line(canvas, (140, 140, 150), (cx - size * 0.08 * gear_scale, cy + size * 0.04 * gear_scale), (cx - size * 0.32 * gear_scale, cy - size * 0.02 * gear_scale), 2)
            pygame.draw.line(canvas, (140, 140, 150), (cx - size * 0.08 * gear_scale, cy + size * 0.24 * gear_scale), (cx - size * 0.32 * gear_scale, cy + size * 0.12 * gear_scale), 2)
            # Rear nozzle (left side), indicating forward propulsion.
            pygame.draw.rect(canvas, (130, 130, 145), (pod_x - size * 0.08 * gear_scale, pod_y + size * 0.07 * gear_scale, size * 0.09 * gear_scale, size * 0.1 * gear_scale), border_radius=2)
            # Nozzle highlight
            pygame.draw.rect(canvas, (160, 160, 175), (pod_x - size * 0.076 * gear_scale, pod_y + size * 0.075 * gear_scale, size * 0.06 * gear_scale, size * 0.06 * gear_scale), border_radius=1)
            nozzle_pos = (pod_x - size * 0.08 * gear_scale, pod_y + size * 0.12 * gear_scale)

        # Exhaust flame only while the engine is actively producing thrust.
        if nozzle_pos is not None and player.is_thrusting:
            flicker = (pygame.time.get_ticks() // 40) % 5
            flame_len = size * gear_scale * (0.18 + 0.05 * flicker)
            flame_half = size * gear_scale * 0.06
            nx, ny = nozzle_pos
            pygame.draw.polygon(canvas, (255, 140, 60), [
                (nx, ny),
                (nx - flame_len, ny - flame_half),
                (nx - flame_len, ny + flame_half),
            ])
            pygame.draw.polygon(canvas, (255, 215, 120), [
                (nx - size * gear_scale * 0.03, ny),
                (nx - flame_len * 0.58, ny - flame_half * 0.52),
                (nx - flame_len * 0.58, ny + flame_half * 0.52),
            ])

        rotated_overlay = pygame.transform.rotozoom(canvas, angle, 1.0)
        overlay_rect = rotated_overlay.get_rect(center=(px, py))
        surface.blit(rotated_overlay, overlay_rect)


if __name__ == "__main__":
    game = Game()
    game.run()

