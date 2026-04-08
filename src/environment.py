import pygame
import random
import math
from src.constants import *


class Terrain:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.points = []
        self.ramps = []  # List of ramp segments
        self.generate_terrain()
        self.wind_speed = 0
        self.wind_direction = 1
        self.wind_timer = 0
        self.wind_particles = []
    
    def generate_terrain(self):
        """Generate terrain with start ramp, long air section, then flat ground."""
        self.points = []
        self.ramps = []
        start_y = self.height - 380
        snow_y = self.height - 90

        # Launch section only at the beginning.
        launch_points = [
            (0, start_y),
            (120, start_y + 8),
            (250, start_y + 45),
            (390, start_y + 95),
            (520, start_y + 145),
            # Launch lip (upward kick)
            (610, start_y + 105),
            (690, start_y + 72),
            (740, start_y + 95),
            (820, start_y + 145),
        ]

        # Keep the whole ramp assembly above snow.
        launch_points = [(x, min(y, snow_y - 70)) for x, y in launch_points]
        self.points.extend(launch_points)

        # Air section: terrain goes below screen so player is airborne.
        air_start_x = 900
        air_end_x = 2600
        self.points.append((air_start_x, self.height + 220))
        self.points.append((air_end_x, self.height + 220))

        # Flat ground only after the air gap.
        flat_y = snow_y
        self.points.append((air_end_x + 200, flat_y))
        self.points.append((self.width, flat_y))

        # Surface zones for physics + rendering.
        self.ice_end_x = air_start_x
        self.air_end_x = air_end_x
        self.snow_start_x = air_end_x + 200

        # Record steep segments as ramps.
        for i in range(len(self.points) - 1):
            prev_x, prev_y = self.points[i]
            curr_x, curr_y = self.points[i + 1]
            slope = (curr_y - prev_y) / (curr_x - prev_x) if curr_x != prev_x else 0
            if abs(curr_y - prev_y) > 20:
                self.ramps.append({
                    'x1': prev_x,
                    'y1': prev_y,
                    'x2': curr_x,
                    'y2': curr_y,
                    'slope': slope,
                })
    
    def apply_ramp_boost(self, player, terrain_y):
        """Calculate slope at player position."""
        # Find the slope under the player
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            if x1 <= player.x <= x2:
                slope = (y2 - y1) / (x2 - x1) if x2 != x1 else 0
                return slope
        return 0

    def get_surface_type_at(self, x):
        """Return surface type at x: ice, air, or snow."""
        if x <= self.ice_end_x:
            return "ice"
        if x < self.snow_start_x:
            return "air"
        return "snow"
    
    def update(self):
        """Update wind and environmental effects."""
        self.wind_timer += 1
        if self.wind_timer > 120:  # Change wind every 2 seconds
            self.wind_timer = 0
            self.wind_direction = random.choice([-1, 1])
            self.wind_speed = random.uniform(0.1, 0.5) * self.wind_direction
        
        # Update wind particles
        self.wind_particles = [p for p in self.wind_particles if p["life"] > 0]
        for p in self.wind_particles:
            p["x"] += p["vx"]
            p["life"] -= 1
        
        # Spawn new wind particles occasionally
        if random.random() < 0.3:
            self.wind_particles.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "vx": self.wind_speed * 2,
                "life": 30,
            })
    
    def get_ground_y_at(self, x):
        """Get terrain height at a specific x coordinate (linear interpolation)."""
        if x < 0 or x > self.width:
            return self.height
        
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            
            if x1 <= x <= x2:
                # Linear interpolation
                t = (x - x1) / (x2 - x1) if x2 != x1 else 0
                return y1 + (y2 - y1) * t
        
        return self.height
    
    def draw(self, surface):
        """Deprecated: Use game.draw_terrain_with_camera() instead."""
        pass


class Hazard:
    def __init__(self, x, y, hazard_type="spike"):
        self.x = x
        self.y = y
        self.type = hazard_type  # "spike", "wall", "ice"
        self.size = 15
        self.active = True
    
    def draw(self, surface):
        """Draw hazard."""
        if not self.active:
            return
        
        if self.type == "spike":
            # Draw spike
            pygame.draw.polygon(surface, (255, 0, 0), [
                (self.x, self.y - self.size),
                (self.x - self.size, self.y + self.size),
                (self.x + self.size, self.y + self.size),
            ])
        elif self.type == "wall":
            # Draw wall
            pygame.draw.rect(surface, (128, 128, 128), (self.x - self.size, self.y - self.size * 2, self.size * 2, self.size * 4))
    
    def check_collision(self, player):
        """Check collision with player using proper circle collision."""
        # More accurate circular collision detection
        dist_x = abs(player.x - self.x)
        dist_y = abs(player.y - self.y)
        
        # Quick check for obvious misses
        if dist_x > (self.size + player.size) or dist_y > (self.size + player.size):
            return False
        
        # Detailed distance check
        dist = math.sqrt(dist_x**2 + dist_y**2)
        return dist < (self.size + player.size)


class Environment:
    def __init__(self):
        self.terrain = Terrain(SCREEN_WIDTH * 8, SCREEN_HEIGHT)
        self.hazards = []
        self.collectibles = []
        self.spawn_hazards()
    
    def spawn_hazards(self):
        """No hazards in MVP flight mechanics phase."""
        self.hazards = []
    
    def update(self):
        """Update environment."""
        self.terrain.update()
    
    def draw(self, surface):
        """Draw entire environment."""
        self.terrain.draw(surface)
        for hazard in self.hazards:
            hazard.draw(surface)
    
    def check_hazard_collision(self, player):
        """Check if player collides with any hazard."""
        for hazard in self.hazards:
            if hazard.check_collision(player):
                return True
        return False

