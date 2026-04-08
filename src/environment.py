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
        """Generate procedural terrain with hills, valleys, and ramps."""
        self.points = []
        self.ramps = []
        y = self.height - 250
        
        for x in range(0, self.width, 60):
            # Create varied terrain with occasional steep slopes (ramps)
            if random.random() < 0.3:  # 30% chance of ramp
                slope = random.choice([-40, -35, -30, 30, 35, 40])  # Steep slopes
                y += slope
            else:
                variation = random.randint(-15, 15)
                y += variation
            
            y = max(250, min(self.height - 50, y))
            self.points.append((x, y))
            
            # Record ramp segments (steep sections)
            if len(self.points) > 1:
                prev_x, prev_y = self.points[-2]
                curr_x, curr_y = self.points[-1]
                slope = abs(curr_y - prev_y)
                if slope > 25:  # Mark steep slopes as ramps
                    self.ramps.append({
                        'x1': prev_x, 'y1': prev_y,
                        'x2': curr_x, 'y2': curr_y,
                        'slope': (curr_y - prev_y) / (curr_x - prev_x) if curr_x != prev_x else 0
                    })
        
        # Add end point
        self.points.append((self.width, self.points[-1][1]))
    
    def apply_ramp_boost(self, player, terrain_y):
        """Apply acceleration boost when sliding down ramps."""
        for ramp in self.ramps:
            # Check if player is on this ramp
            if ramp['x1'] <= player.x <= ramp['x2']:
                # Sliding down a ramp gives acceleration
                if ramp['slope'] > 0.3:  # Downward slope (positive)
                    boost = min(abs(ramp['slope'] * 0.5), 2.0)  # Ramp acceleration
                    player.vx += boost * 0.5
                    # Reduce fuel cost slightly when sliding downhill
                    if player.fuel > 0:
                        player.fuel = max(0, player.fuel - 0.2)
                elif ramp['slope'] < -0.3:  # Upward slope (negative) - resistance
                    resistance = min(abs(ramp['slope'] * 0.3), 1.5)
                    player.vx = max(0, player.vx - resistance)
    
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
        """Draw terrain and background."""
        # Draw sky gradient effect
        surface.fill((135, 206, 235))
        
        # Draw clouds (simple circles)
        for i in range(5):
            cloud_y = 50 + (i * 100)
            pygame.draw.circle(surface, (255, 255, 255), (100 + i * 200, cloud_y), 30)
            pygame.draw.circle(surface, (255, 255, 255), (130 + i * 200, cloud_y), 35)
            pygame.draw.circle(surface, (255, 255, 255), (70 + i * 200, cloud_y), 25)
        
        # Draw wind particles (visual effect)
        for p in self.wind_particles:
            size = max(1, int(2 * (p["life"] / 30)))
            pygame.draw.circle(surface, (180, 180, 180), (int(p["x"]), int(p["y"])), size)
        
        # Draw terrain
        if len(self.points) > 1:
            terrain_points = list(self.points)
            terrain_points.append((self.width, self.height))
            terrain_points.append((0, self.height))
            
            pygame.draw.polygon(surface, (139, 69, 19), terrain_points)
        
        # Draw terrain outline (darker)
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            pygame.draw.line(surface, (100, 50, 0), (x1, y1), (x2, y2), 3)
        
        # Draw snow/highlight on top
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            pygame.draw.line(surface, (255, 255, 255), (x1, y1), (x2, y2), 1)
        
        # Draw ramp indicators (darker color for steep slopes)
        for ramp in self.ramps:
            color = (200, 100, 50) if ramp['slope'] > 0 else (100, 150, 200)  # Red/orange for downslope, blue for upslope
            pygame.draw.line(surface, color, (int(ramp['x1']), int(ramp['y1'])), 
                           (int(ramp['x2']), int(ramp['y2'])), 5)


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
        self.terrain = Terrain(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.hazards = []
        self.collectibles = []
        self.spawn_hazards()
    
    def spawn_hazards(self):
        """Spawn hazards throughout the level."""
        for i in range(10):
            x = random.randint(200, SCREEN_WIDTH - 100)
            terrain_y = self.terrain.get_ground_y_at(x)
            y = terrain_y - random.randint(50, 200)
            hazard_type = random.choice(["spike", "wall"])
            self.hazards.append(Hazard(x, y, hazard_type))
    
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

