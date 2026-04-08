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
        self.generate_clouds()
        self.wind_speed = 0
        self.wind_direction = 1
        self.wind_timer = 0
        self.wind_particles = []
    
    def generate_terrain(self):
        """Generate terrain with start ramp, long air section, then flat ground."""
        self.points = []
        self.ramps = []
        start_y = self.height - 520

        # Launch section only at the beginning.
        # Profile: almost-flat top -> steep down -> short flat -> ~30deg launch up -> cliff.
        launch_points = [
            (0, start_y),
            (170, start_y + 6),
            (350, start_y + 170),
            (430, start_y + 175),
            (560, start_y + 100),
            (620, start_y + 70),
        ]

        lowest_ramp_y = max(y for _, y in launch_points)
        launch_off_y = launch_points[-1][1]  # launch lip height

        # Make snow start much lower than launch-off (approx 10m drop).
        snow_drop_from_launch_m = 1
        snow_y = launch_off_y + (snow_drop_from_launch_m * PIXELS_PER_METER)
        # Keep snow safely below the whole ramp assembly as well.
        snow_y = max(snow_y, lowest_ramp_y + (0.4 * PIXELS_PER_METER))
        self.points.extend(launch_points)

        # Tiny snow shelf right after the launch lip, then a near-vertical drop to snow.
        shelf_end_x = 632
        shelf_y = launch_off_y + 6
        self.points.append((shelf_end_x, shelf_y))

        # Snow starts immediately after the drop (no horizontal air gap).
        snow_step_x = shelf_end_x + 2
        flat_y = snow_y
        self.points.append((snow_step_x, flat_y))
        self.points.append((self.width, flat_y))

        # Surface zones for physics + rendering.
        self.ice_end_x = 620
        self.shelf_snow_end_x = shelf_end_x
        self.snow_start_x = snow_step_x

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

    def generate_clouds(self):
        """Generate world-anchored clouds that drift gently with wind."""
        self.clouds = []
        cloud_y_choices = [55, 85, 120, 155, 190, 235]
        cloud_count = 9
        spacing = max(600, self.width // cloud_count)
        for i in range(cloud_count):
            self.clouds.append({
                "x": 120 + i * spacing + random.randint(-140, 140),
                "y": random.choice(cloud_y_choices) + random.randint(-12, 18),
                "s": random.randint(26, 44),
                "drift": random.uniform(0.15, 0.45),
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
        """Return surface type at x: ice or snow."""
        if x <= self.ice_end_x:
            return "ice"
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

        # Update cloud positions (slow wind drift, wrapped through world bounds).
        for c in self.clouds:
            c["x"] += self.wind_speed * c["drift"]
            if c["x"] < -200:
                c["x"] = self.width + 200
            elif c["x"] > self.width + 200:
                c["x"] = -200
    
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
        self.terrain = Terrain(PIXELS_PER_METER * WORLD_LENGTH_M, SCREEN_HEIGHT)
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

