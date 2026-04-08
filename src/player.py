import pygame
import math
from src.constants import *


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0  # velocity x
        self.vy = 0  # velocity y
        self.size = 13
        self.angle = 0  # rotation angle
        
        # Flight stats
        self.sled = None
        self.glider = None
        self.booster = None
        self.fuel = 0
        self.max_fuel = 0
        self.distance_traveled = 0
        self.coins = 0
        self.is_flying = True
        self.is_landed = False
        self.sled_attached = True
        
    def update(self, controls, terrain_slope=0.0, boosting=False, grounded=False, surface_friction=0.995, can_rotate=True, dt=1.0 / FPS):
        """Update player position and physics."""
        if self.is_landed:
            return
            
        glider_stats = GLIDER_TIERS.get(self.glider, {"glide_mult": 1.0})
        booster_stats = BOOSTER_TIERS.get(self.booster, {"boost_mult": 0.0})
        
        # Handle boost (thrust in facing direction)
        thrust_n = 0.0
        if boosting and self.fuel > 0:
            thrust_n = BOOST_THRUST_N * float(booster_stats["boost_mult"])
            burn = BOOST_FUEL_BURN_PER_SEC * (0.85 + 0.15 * float(booster_stats["boost_mult"]))
            self.fuel = max(0.0, self.fuel - burn * dt)
        
        # Handle pitch: manual in air, automatic on ramp when locked.
        if can_rotate:
            if controls.get("left"):
                self.angle = min(self.angle + ROTATION_SPEED, 45)
            elif controls.get("right"):
                self.angle = max(self.angle - ROTATION_SPEED, -45)
        else:
            # Align to slope when on ramp (y grows downward on screen).
            slope_angle = -math.degrees(math.atan(terrain_slope))
            self.angle = max(-45, min(45, slope_angle))
        
        dt = max(1e-4, dt)
        if grounded:
            # Grounded ramp slide physics (pixel-domain), keeps penguin glued to slope.
            self.vx += GRAVITY * terrain_slope * 1.5
            # Small thrust contribution while on ground.
            if thrust_n > 0:
                thrust_px = (thrust_n / PLAYER_MASS_KG) * (PIXELS_PER_METER / FPS) * dt * FPS
                self.vx += max(0.0, math.cos(math.radians(self.angle))) * thrust_px
            self.vx *= surface_friction
            self.vy = self.vx * terrain_slope

            # Launch assist at sharp ramp upturns.
            if terrain_slope < -0.45 and self.vx > 5.0:
                self.vy -= min(4.5, abs(terrain_slope) * self.vx * 0.16)
        else:
            # Airborne physics in SI units using lift/drag/thrust/gravity.
            pitch = math.radians(self.angle)

            vx_ms = self.vx * FPS / PIXELS_PER_METER
            vy_up_ms = -self.vy * FPS / PIXELS_PER_METER
            speed_ms = max(0.1, math.hypot(vx_ms, vy_up_ms))

            vel_dir_x = vx_ms / speed_ms
            vel_dir_y = vy_up_ms / speed_ms
            flight_path_angle = math.atan2(vy_up_ms, vx_ms)

            alpha = max(math.radians(-25), min(math.radians(25), pitch - flight_path_angle))
            cl = LIFT_COEFF_0 + LIFT_COEFF_ALPHA * alpha
            cl = max(LIFT_COEFF_MIN, min(LIFT_COEFF_MAX, cl))
            cd = DRAG_COEFF_0 + DRAG_INDUCED_K * (cl ** 2)

            wing_area = BASE_WING_AREA_M2 * (float(glider_stats["glide_mult"]) ** 1.35)
            q = 0.5 * AIR_DENSITY * (speed_ms ** 2)
            lift_n = q * wing_area * cl
            drag_n = q * wing_area * cd

            lift_dir_x = -vel_dir_y
            lift_dir_y = vel_dir_x
            drag_dir_x = -vel_dir_x
            drag_dir_y = -vel_dir_y

            thrust_x = thrust_n * math.cos(pitch)
            thrust_y = thrust_n * math.sin(pitch)

            fx = lift_n * lift_dir_x + drag_n * drag_dir_x + thrust_x
            fy = lift_n * lift_dir_y + drag_n * drag_dir_y + thrust_y - PLAYER_MASS_KG * GRAVITY_MPS2

            ax = fx / PLAYER_MASS_KG
            ay = fy / PLAYER_MASS_KG

            dvx_ms = ax * dt
            dvy_up_ms = ay * dt

            self.vx += dvx_ms * PIXELS_PER_METER / FPS
            self.vy += (-dvy_up_ms) * PIXELS_PER_METER / FPS
        

        # Update position
        step_scale = dt * FPS
        self.x += self.vx * step_scale
        self.y += self.vy * step_scale
        
        # Track distance (horizontal only)
        if self.vx > 0:
            self.distance_traveled += (self.vx * step_scale) / PIXELS_PER_METER
    
    def check_landing(self, terrain_y):
        """Check if player lands on ground."""
        if self.y + self.size >= terrain_y:
            self.is_landed = True
            self.is_flying = False
            self.y = terrain_y - self.size
            return True
        return False
    
    def reset(self):
        """Reset player for new attempt."""
        self.x = 100
        self.y = 200
        self.vx = 0
        self.vy = 0
        self.fuel = self.max_fuel
        self.distance_traveled = 0
        self.is_flying = True
        self.is_landed = False
        self.angle = 0
        self.sled_attached = self.sled in SLED_TIERS
    
    def equip_sled(self, sled_name):
        if sled_name in SLED_TIERS or sled_name is None:
            self.sled = sled_name
            self.sled_attached = self.sled in SLED_TIERS

    def equip_glider(self, glider_name):
        if glider_name in GLIDER_TIERS or glider_name is None:
            self.glider = glider_name

    def equip_booster(self, booster_name):
        if booster_name in BOOSTER_TIERS:
            self.booster = booster_name
            self.max_fuel = BOOSTER_TIERS[booster_name]["fuel"]
            self.fuel = min(self.fuel, self.max_fuel) if self.fuel > 0 else self.max_fuel
        elif booster_name is None:
            self.booster = None
            self.max_fuel = 0
            self.fuel = 0
    
    def draw(self, surface):
        """Draw player as a penguin sprite."""
        size = self.size
        
        # Draw penguin body (white belly, black back)
        # Body (black back)
        body_points = [
            (self.x - size * 0.6, self.y - size * 0.3),  # top left
            (self.x + size * 0.6, self.y - size * 0.3),  # top right
            (self.x + size * 0.5, self.y + size * 0.8),  # bottom right
            (self.x - size * 0.5, self.y + size * 0.8),  # bottom left
        ]
        pygame.draw.polygon(surface, (20, 20, 20), body_points)
        
        # Belly (white)
        belly_points = [
            (self.x - size * 0.4, self.y - size * 0.1),
            (self.x + size * 0.4, self.y - size * 0.1),
            (self.x + size * 0.3, self.y + size * 0.6),
            (self.x - size * 0.3, self.y + size * 0.6),
        ]
        pygame.draw.polygon(surface, (220, 220, 220), belly_points)
        
        # Head (black)
        pygame.draw.circle(surface, (20, 20, 20), (int(self.x), int(self.y - size * 0.5)), int(size * 0.45))
        
        # Eyes
        eye_offset = size * 0.2
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x - eye_offset), int(self.y - size * 0.6)), int(size * 0.12))
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x + eye_offset), int(self.y - size * 0.6)), int(size * 0.12))
        
        # Pupils (look in direction of flight)
        pupil_offset = int(self.vx * 0.02)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x - eye_offset + pupil_offset), int(self.y - size * 0.6)), int(size * 0.06))
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x + eye_offset + pupil_offset), int(self.y - size * 0.6)), int(size * 0.06))
        
        # Beak
        beak_points = [
            (self.x - size * 0.1, self.y - size * 0.25),
            (self.x + size * 0.1, self.y - size * 0.25),
            (self.x, self.y - size * 0.05),
        ]
        pygame.draw.polygon(surface, (255, 150, 0), beak_points)
        
        # Wings (small sides)
        pygame.draw.polygon(surface, (20, 20, 20), [
            (self.x - size * 0.65, self.y - size * 0.1),
            (self.x - size * 0.85, self.y + size * 0.2),
            (self.x - size * 0.7, self.y + size * 0.4),
        ])
        pygame.draw.polygon(surface, (20, 20, 20), [
            (self.x + size * 0.65, self.y - size * 0.1),
            (self.x + size * 0.85, self.y + size * 0.2),
            (self.x + size * 0.7, self.y + size * 0.4),
        ])
        
        # Feet
        pygame.draw.polygon(surface, (255, 150, 0), [
            (self.x - size * 0.25, self.y + size * 0.9),
            (self.x - size * 0.1, self.y + size * 0.95),
            (self.x - size * 0.15, self.y + size * 1.05),
            (self.x - size * 0.3, self.y + size * 1.0),
        ])
        pygame.draw.polygon(surface, (255, 150, 0), [
            (self.x + size * 0.25, self.y + size * 0.9),
            (self.x + size * 0.1, self.y + size * 0.95),
            (self.x + size * 0.15, self.y + size * 1.05),
            (self.x + size * 0.3, self.y + size * 1.0),
        ])
        
        # Draw fuel bar
        if self.fuel > 0:
            bar_width = 25
            bar_height = 5
            bar_x = self.x - bar_width // 2
            bar_y = self.y - size - 15
            
            # Background
            pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            
            # Fuel level (green to red gradient)
            fuel_width = int(bar_width * (self.fuel / self.max_fuel))
            fuel_color = (int(255 * (1 - self.fuel / self.max_fuel)), int(255 * (self.fuel / self.max_fuel)), 0)
            pygame.draw.rect(surface, fuel_color, (bar_x, bar_y, fuel_width, bar_height))
            
            # Border
            pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)

