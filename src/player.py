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
        self.current_gear = "base"
        self.fuel = 100
        self.max_fuel = 100
        self.distance_traveled = 0
        self.coins = 0
        self.is_flying = True
        self.is_landed = False
        
    def update(self, controls, terrain_slope=0.0, boosting=False, grounded=False, surface_friction=0.995):
        """Update player position and physics."""
        if self.is_landed:
            return
            
        # Get gear stats
        gear = GEAR_TYPES[self.current_gear]
        
        # Handle boost (thrust in facing direction)
        if boosting and self.fuel > 0:
            boost_force = BOOST_FORCE * gear["acceleration"]
            rad = math.radians(self.angle)
            self.vx += math.cos(rad) * boost_force
            self.vy -= math.sin(rad) * boost_force
            self.fuel = max(0, self.fuel - 1.0)
        
        # Handle rotation
        if controls.get("left"):
            self.angle = min(self.angle + ROTATION_SPEED, 45)
        elif controls.get("right"):
            self.angle = max(self.angle - ROTATION_SPEED, -45)
        else:
            # Smooth return to neutral
            self.angle *= 0.95
        
        if grounded:
            # Slide along the terrain tangent.
            self.vx += GRAVITY * terrain_slope * 2.2
            self.vx *= surface_friction
            self.vy = self.vx * terrain_slope
            
            # Kicker: convert speed into upward launch near sharp upturns.
            if terrain_slope < -0.45 and self.vx > 5.0:
                self.vy -= min(6.0, abs(terrain_slope) * self.vx * 0.22)
        else:
            # Airborne physics.
            gravity_effect = GRAVITY / gear["glide"]
            self.vy += gravity_effect
        
        # Cap velocity
        speed = math.sqrt(self.vx**2 + self.vy**2)
        max_speed = MAX_VELOCITY * gear["speed"]
        if speed > max_speed:
            scale = max_speed / speed
            self.vx *= scale
            self.vy *= scale
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Track distance (horizontal only)
        if self.vx > 0:
            self.distance_traveled += self.vx / PIXELS_PER_METER
    
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
    
    def equip_gear(self, gear_name):
        """Equip a different flight gear."""
        if gear_name in GEAR_TYPES:
            self.current_gear = gear_name
            self.max_fuel = GEAR_TYPES[gear_name]["fuel"]
            self.fuel = self.max_fuel
    
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

