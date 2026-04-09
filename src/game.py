import math
import pygame
from src.constants import *
from src.player import Player
from src.environment import Environment
from src.save_system import SaveSystem
from src.ui import UIManager, Button
from src.gameplay.terrain_math import get_terrain_slope_at_x, project_velocity_to_slope
from src.gameplay.earnings import compute_flight_earnings
from src.gameplay.fuel import apply_fuel_capacity_upgrade
from src.gameplay import shop as shop_helpers
from src.rendering import flight_effects as flight_fx
from src.rendering.world import draw_terrain_with_camera as draw_world_with_camera
from src.rendering.player_graphics import draw_player_with_camera as draw_player_actor_with_camera


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
        self.obstacle_contacts = set()
        self.low_speed_frames = 0
        self.shop_catalog_category = None
        self.toast_text = ""
        self.toast_color = (225, 235, 248)
        self.toast_timer = 0.0
        self.controls_hint_timer = 8.0
        self.was_ramp_locked = False
        self.ramp_detached_once = False
        self.impact_stopped = False
        self.pending_payload_explosion = None
        self.payload_explosion_delay_s = 0.0
        self.player_exploding = False
        self.player_explosion_anim_s = 0.0
        self.player_explosion_world = (0.0, 0.0)
        self.post_explosion_end_delay_s = 1.0
        self.post_explosion_wait_s = 0.0

        # Flight visual state (render-only, no gameplay impact).
        self.render_time_s = 0.0
        self.player_trail = []
        self.boost_particles = []
        self.speed_lines = []
        self._trail_spawn_accum = 0.0
        self._speed_line_spawn_accum = 0.0

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
        if "unlocked_payloads" not in save_data:
            save_data["unlocked_payloads"] = []
        if "equipped_payload" not in save_data:
            save_data["equipped_payload"] = None
        if "ramp_height_level" not in save_data:
            save_data["ramp_height_level"] = 0
        save_data["ramp_height_level"] = max(0, min(int(save_data["ramp_height_level"]), len(RAMP_HEIGHT_TIERS) - 1))
        if "ramp_drop_level" not in save_data:
            save_data["ramp_drop_level"] = 0
        save_data["ramp_drop_level"] = max(0, min(int(save_data["ramp_drop_level"]), len(RAMP_DROP_TIERS) - 1))
        if "fuel_level" not in save_data:
            save_data["fuel_level"] = 0
        save_data["fuel_level"] = max(0, min(int(save_data["fuel_level"]), len(FUEL_CAPACITY_TIERS) - 1))

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
        if save_data.get("equipped_payload") not in save_data["unlocked_payloads"]:
            save_data["equipped_payload"] = None
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
        self._apply_fuel_capacity_upgrade()
        self.player.equip_payload(self.game_data["equipped_payload"])
    
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
            Button(SCREEN_WIDTH - 190, 186, 150, 30, "Upgrade", (100, 150, 100)),
        ]
        self.buttons["upgrade_boxes"] = {
            "sled": Button(120, 230, 420, 210, "Sled", (70, 110, 150)),
            "glider": Button(660, 230, 420, 210, "Glider", (70, 120, 165)),
            "booster": Button(120, 490, 420, 210, "Engine", (75, 115, 155)),
            "payload": Button(660, 490, 420, 210, "Payload", (95, 95, 130)),
        }
        self.buttons["catalog_close"] = Button(910, 190, 160, 36, "Close", (120, 90, 90))
        self.buttons["catalog_items"] = [
            Button(860, 255 + i * 92, 180, 38, "", (100, 150, 100)) for i in range(8)
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
        self.obstacle_contacts = set()
        self.low_speed_frames = 0
        self.was_ramp_locked = False
        self.ramp_detached_once = False
        self.impact_stopped = False
        self.pending_payload_explosion = None
        self.payload_explosion_delay_s = 1.0
        self.player_exploding = False
        self.player_explosion_anim_s = 0.0
        self.player_explosion_world = (0.0, 0.0)
        self.post_explosion_wait_s = 0.0

        # Reset flight visual state.
        self.player_trail = []
        self.boost_particles = []
        self.speed_lines = []
        self._trail_spawn_accum = 0.0
        self._speed_line_spawn_accum = 0.0
        
        self.player.equip_sled(self.game_data["equipped_sled"])
        self.player.equip_glider(self.game_data["equipped_glider"])
        self.player.equip_booster(self.game_data["equipped_booster"])
        self._apply_fuel_capacity_upgrade()
        self.player.equip_payload(self.game_data["equipped_payload"])
        
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
            if self.buttons["upgrade"][3].is_clicked(mouse_pos, True):
                self.try_purchase_fuel_capacity()

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
            elif self.buttons["upgrade_boxes"]["payload"].is_clicked(mouse_pos, True):
                self.shop_catalog_category = "payload"
        
        elif self.state == STATE_RESULTS:
            if self.buttons["results"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
    
    def try_purchase_gear(self, category, gear_name):
        """Try to purchase or equip categorized gear."""
        shop_helpers.try_purchase_gear(self, category, gear_name)

    def _apply_fuel_capacity_upgrade(self):
        """Apply current fuel upgrade multiplier to equipped booster capacity."""
        apply_fuel_capacity_upgrade(self.player, self.game_data, refill=True)

    def try_purchase_ramp_height(self):
        """Advance the launch ramp height upgrade."""
        shop_helpers.try_purchase_ramp_height(self)

    def try_purchase_ramp_drop(self):
        """Advance the downhill ramp depth upgrade."""
        shop_helpers.try_purchase_ramp_drop(self)

    def try_purchase_fuel_capacity(self):
        """Advance the fuel capacity upgrade."""
        shop_helpers.try_purchase_fuel_capacity(self)

    def get_catalog_entries(self, category):
        """Return ordered gear tuples for the selected shop catalog."""
        return shop_helpers.get_catalog_entries(category)

    def _get_terrain_slope_at_x(self, x):
        """Return terrain slope under a world x position."""
        return get_terrain_slope_at_x(self.environment.terrain.points, x)

    def _project_velocity_to_slope(self, slope, preserve_ratio=0.0):
        """Resolve ground contact by removing inward normal velocity and keeping tangent motion."""
        self.player.vx, self.player.vy = project_velocity_to_slope(
            self.player.vx,
            self.player.vy,
            slope,
            preserve_ratio=preserve_ratio,
        )

    def _resolve_obstacle_hits(self, controls, dt):
        """Handle impact-only obstacle hits: speed converts to damage and is fully consumed."""
        for obstacle in self.environment.hazards:
            if obstacle.destroyed or not obstacle.active:
                self.obstacle_contacts.discard(id(obstacle))
                continue

            obstacle_id = id(obstacle)
            colliding = obstacle.check_collision(self.player)
            if not colliding:
                self.obstacle_contacts.discard(obstacle_id)
                continue

            # Only apply damage on initial impact frame, not while overlapping through the hitbox.
            if obstacle_id in self.obstacle_contacts:
                continue
            self.obstacle_contacts.add(obstacle_id)

            speed_mps = math.hypot(self.player.vx, self.player.vy) * FPS / PIXELS_PER_METER
            payload_stats = PAYLOAD_TIERS.get(self.player.payload)
            if payload_stats:
                impact_damage = (speed_mps * float(payload_stats.get("impact_mult", 1.0))) + float(payload_stats.get("impact_flat", 0.0))
            else:
                impact_damage = speed_mps
            if not obstacle.destroyed:
                obstacle.hp -= impact_damage

            should_schedule_payload_blast = False
            if payload_stats and payload_stats.get("payload_type") == "explosive" and obstacle.hp > 0 and self.pending_payload_explosion is None:
                bonus_damage = float(payload_stats.get("explosion_damage", 0.0))
                if bonus_damage > 0.0:
                    should_schedule_payload_blast = True
                    self.pending_payload_explosion = {
                        "obstacle": obstacle,
                        "payload_name": payload_stats.get("name", "Payload"),
                        "bonus_damage": bonus_damage,
                    }
                    self.payload_explosion_delay_s = 1.0
                    self.set_toast(f"{payload_stats['name']} armed...", (255, 195, 135), duration=0.7)

            # Impact consumes all speed regardless of outcome.
            self.player.vx = 0.0
            self.player.vy = 0.0
            self.impact_stopped = True

            if obstacle.hp <= 0:
                obstacle.destroyed = True
                obstacle.active = False
                self.flight_destruction_points += obstacle.destruction_points
                self.set_toast(f"Destroyed: {obstacle.name}", (120, 220, 150), duration=1.6)
            else:
                # If not destroyed, the penguin remains stopped after the impact.
                if not should_schedule_payload_blast:
                    self.set_toast(f"Hit {obstacle.name}", (240, 180, 120), duration=0.9)

    def _trigger_player_explosion(self):
        """Start a short explosion animation centered on the player."""
        self.player_exploding = True
        self.player_explosion_anim_s = 0.35
        self.player_explosion_world = (self.player.x, self.player.y + self.player.size * 0.35)
        self.post_explosion_wait_s = 0.0

    def _process_payload_explosion_timers(self, dt):
        """Resolve delayed explosive payload behavior and end the day after animation."""
        if self.pending_payload_explosion is not None:
            self.payload_explosion_delay_s = max(0.0, self.payload_explosion_delay_s - dt)
            if self.payload_explosion_delay_s <= 0.0:
                payload_name = self.pending_payload_explosion.get("payload_name", "Payload")
                bonus_damage = float(self.pending_payload_explosion.get("bonus_damage", 0.0))
                obstacle = self.pending_payload_explosion.get("obstacle")

                if obstacle is not None and (not obstacle.destroyed) and obstacle.active:
                    obstacle.hp -= bonus_damage
                    if obstacle.hp <= 0:
                        obstacle.destroyed = True
                        obstacle.active = False
                        self.flight_destruction_points += obstacle.destruction_points
                        self.set_toast(f"{payload_name} exploded and destroyed {obstacle.name}", (120, 220, 150), duration=1.6)
                    else:
                        self.set_toast(f"{payload_name} detonated on {obstacle.name}", (255, 170, 120), duration=1.3)
                else:
                    self.set_toast(f"{payload_name} detonated", (255, 170, 120), duration=1.0)

                self.pending_payload_explosion = None
                self._trigger_player_explosion()

        if self.player_exploding:
            if self.player_explosion_anim_s > 0.0:
                self.player_explosion_anim_s = max(0.0, self.player_explosion_anim_s - dt)
            else:
                # Small cinematic hold after the blast before transitioning to results.
                self.post_explosion_wait_s += dt
                if self.post_explosion_wait_s >= self.post_explosion_end_delay_s:
                    self._finalize_day()
                    return True
        return False

    def _finalize_day(self):
        """Compute earnings from flight stats and transition to result screen."""
        self.flight_distance = self.player.distance_traveled
        earnings = compute_flight_earnings(
            distance=self.flight_distance,
            max_speed=self.flight_max_speed_mps,
            max_altitude=self.flight_max_altitude_m,
            duration=self.flight_duration_s,
            destruction=self.flight_destruction_points,
            k_distance=EARNING_K_DISTANCE,
            l_speed=EARNING_L_MAX_SPEED,
            m_altitude=EARNING_M_MAX_ALTITUDE,
            n_duration=EARNING_N_DURATION,
            o_destruction=EARNING_O_DESTRUCTION,
        )
        self.flight_coins_earned = earnings["total"]
        self.flight_breakdown = {
            "distance": self.flight_distance,
            "max_speed": self.flight_max_speed_mps,
            "max_altitude": self.flight_max_altitude_m,
            "duration": self.flight_duration_s,
            "destruction": self.flight_destruction_points,
            "distance_money": earnings["distance_money"],
            "speed_money": earnings["speed_money"],
            "altitude_money": earnings["altitude_money"],
            "duration_money": earnings["duration_money"],
            "destruction_money": earnings["destruction_money"],
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

            # Keep speed pinned to zero forever after the first obstacle impact.
            if self.impact_stopped:
                self.player.vx = 0.0
                self.player.vy = 0.0

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

            if self._process_payload_explosion_timers(dt):
                return

            self.environment.update()

            speed = (self.player.vx ** 2 + self.player.vy ** 2) ** 0.5
            speed_mps = speed * FPS / PIXELS_PER_METER
            self.flight_max_speed_mps = max(self.flight_max_speed_mps, speed_mps)
            self.render_time_s += dt

            terrain_y_now = self.environment.terrain.get_ground_y_at(self.player.x)
            altitude_m = max(0.0, (terrain_y_now - (self.player.y + self.player.size)) / PIXELS_PER_METER)
            self.flight_max_altitude_m = max(self.flight_max_altitude_m, altitude_m)

            flight_fx.update_flight_visuals(self, dt, speed_mps, controls)

            # End the day if the penguin has effectively stopped.
            explosion_sequence_active = (
                self.pending_payload_explosion is not None
                or self.player_exploding
                or self.post_explosion_wait_s > 0.0
            )
            if (not explosion_sequence_active) and (grounded or self.impact_stopped) and speed < 0.2:
                self.low_speed_frames += 1
            else:
                self.low_speed_frames = 0

            if (not explosion_sequence_active) and self.low_speed_frames >= 30:
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
            flight_fx.draw_flight_background(self, self.screen)
            
            # Draw game elements with camera offset applied
            draw_world_with_camera(self, self.screen)
            flight_fx.draw_motion_effects_with_camera(self, self.screen)
            if not self.player_exploding:
                draw_player_actor_with_camera(self, self.screen)
            self.draw_player_explosion_with_camera(self.screen)
            
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

    def draw_player_explosion_with_camera(self, surface):
        """Draw the delayed payload detonation blast around the player."""
        if not self.player_exploding:
            return

        offset = self.camera_x
        offset_y = self.camera_y
        ex = self.player_explosion_world[0] - offset
        ey = self.player_explosion_world[1] - offset_y
        progress = 1.0 - (self.player_explosion_anim_s / 0.55)
        progress = max(0.0, min(1.0, progress))

        base_radius = int(14 + 120 * progress)
        glow_radius = int(base_radius * 1.45)
        alpha = int(210 * (1.0 - progress))

        blast = pygame.Surface((glow_radius * 2 + 4, glow_radius * 2 + 4), pygame.SRCALPHA)
        cx = glow_radius + 2
        cy = glow_radius + 2
        pygame.draw.circle(blast, (255, 120, 60, alpha), (cx, cy), glow_radius)
        pygame.draw.circle(blast, (255, 195, 110, min(255, alpha + 25)), (cx, cy), base_radius)
        pygame.draw.circle(blast, (255, 240, 190, min(255, alpha + 40)), (cx, cy), max(3, int(base_radius * 0.45)))

        # Light shrapnel arcs to sell the blast motion.
        shard_count = 8
        for i in range(shard_count):
            ang = (i / float(shard_count)) * math.tau + progress * 2.2
            r1 = int(base_radius * 0.85)
            r2 = int(base_radius * 1.2)
            x1 = cx + int(math.cos(ang) * r1)
            y1 = cy + int(math.sin(ang) * r1)
            x2 = cx + int(math.cos(ang) * r2)
            y2 = cy + int(math.sin(ang) * r2)
            pygame.draw.line(blast, (255, 230, 170, max(80, alpha)), (x1, y1), (x2, y2), 2)

        # Expanding shock rings.
        ring_alpha = max(0, int(180 * (1.0 - progress)))
        for rk in (0.55, 0.9, 1.22):
            rr = max(4, int(base_radius * rk))
            pygame.draw.circle(blast, (255, 210, 150, ring_alpha // 2), (cx, cy), rr, 2)

        # Ember dots.
        ember_count = 12
        for i in range(ember_count):
            ang = (i / float(ember_count)) * math.tau + progress * 3.0
            er = int(base_radius * (0.65 + 0.55 * ((i % 3) / 2.0)))
            ex2 = cx + int(math.cos(ang) * er)
            ey2 = cy + int(math.sin(ang) * er)
            pygame.draw.circle(blast, (255, 170, 90, max(40, ring_alpha)), (ex2, ey2), 2)

        surface.blit(blast, (ex - cx, ey - cy))

