import pygame
import random
import math
from src.constants import *


class Terrain:
    def __init__(self, width, height, ramp_height_level=0, ramp_drop_level=0):
        self.width = width
        self.height = height
        self.ramp_height_level = max(0, min(int(ramp_height_level), len(RAMP_HEIGHT_TIERS) - 1))
        self.ramp_drop_level = max(0, min(int(ramp_drop_level), len(RAMP_DROP_TIERS) - 1))
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
        launch_gap_m = RAMP_HEIGHT_TIERS[self.ramp_height_level]["launch_gap_m"]
        extra_drop_px = RAMP_DROP_TIERS[self.ramp_drop_level]["extra_drop_m"] * PIXELS_PER_METER

        # Launch section only at the beginning.
        # Ramp-drop upgrade raises only the start section; launch piece/lip anchors remain fixed.
        launch_anchors = [
            (0, start_y - extra_drop_px),
            (200, start_y + 8 - extra_drop_px),      # Shorter top near-flat entry
            (520, start_y + 360),                     # Steeper main downhill acceleration section
            (980, start_y + 365),                     # Short center settle section
            # Recovery climb is reduced in height (Y), not shortened in X.
            (1260, start_y + 262),
        ]

        launch_points = self._build_smooth_ramp_points(launch_anchors, samples_per_segment=24)

        bottom_flat_y = launch_anchors[3][1]

        # Ramp height is measured from the bottom flat section to the snow surface.
        snow_y = bottom_flat_y + (launch_gap_m * PIXELS_PER_METER)
        self.points.extend(launch_points)

        # Immediate near-vertical drop right from the launch lip.
        lip_x = launch_anchors[-1][0]

        # Snow starts immediately after the drop (no horizontal air gap).
        snow_step_x = lip_x + 2
        flat_y = snow_y
        self.points.append((snow_step_x, flat_y))
        self.points.append((self.width, flat_y))

        # Surface zones for physics + rendering.
        self.ice_end_x = lip_x
        self.shelf_snow_end_x = lip_x
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

    def _build_smooth_ramp_points(self, anchors, samples_per_segment=20):
        """Generate a smooth shape-preserving polyline from monotonic-x anchor points."""
        if len(anchors) < 2:
            return anchors[:]

        n = len(anchors)
        x_vals = [p[0] for p in anchors]
        y_vals = [p[1] for p in anchors]

        # Segment secants (dy/dx).
        secants = []
        for i in range(n - 1):
            dx = x_vals[i + 1] - x_vals[i]
            secants.append((y_vals[i + 1] - y_vals[i]) / dx if dx != 0 else 0.0)

        # PCHIP-style tangents: smooth but no overshoot-induced local hills/valleys.
        slopes = [0.0] * n
        slopes[0] = secants[0]
        slopes[-1] = secants[-1]
        for i in range(1, n - 1):
            d0 = secants[i - 1]
            d1 = secants[i]
            if d0 == 0.0 or d1 == 0.0 or (d0 > 0.0) != (d1 > 0.0):
                slopes[i] = 0.0
            else:
                slopes[i] = 0.5 * (d0 + d1)

        # Hyman monotonicity limiter.
        for i in range(n - 1):
            d = secants[i]
            if d == 0.0:
                slopes[i] = 0.0
                slopes[i + 1] = 0.0
                continue
            a = slopes[i] / d
            b = slopes[i + 1] / d
            if a < 0.0:
                slopes[i] = 0.0
                a = 0.0
            if b < 0.0:
                slopes[i + 1] = 0.0
                b = 0.0
            mag = a * a + b * b
            if mag > 9.0:
                tau = 3.0 / math.sqrt(mag)
                slopes[i] = tau * a * d
                slopes[i + 1] = tau * b * d

        points = []
        for i in range(n - 1):
            x0, y0 = x_vals[i], y_vals[i]
            x1, y1 = x_vals[i + 1], y_vals[i + 1]
            dx = x1 - x0
            if dx <= 0:
                continue

            m0 = slopes[i]
            m1 = slopes[i + 1]

            step_count = max(4, int(samples_per_segment))
            for s in range(step_count):
                u = s / float(step_count)
                h00 = (2 * u ** 3) - (3 * u ** 2) + 1
                h10 = (u ** 3) - (2 * u ** 2) + u
                h01 = (-2 * u ** 3) + (3 * u ** 2)
                h11 = (u ** 3) - (u ** 2)

                x = x0 + (dx * u)
                y = h00 * y0 + h10 * m0 * dx + h01 * y1 + h11 * m1 * dx
                points.append((x, y))

        points.append(anchors[-1])
        return points

    def generate_clouds(self):
        """Generate world-anchored clouds across the full map width."""
        self.clouds = []
        cloud_clearance_choices = [180, 210, 240, 270, 300, 335, 370, 405]

        # Scale cloud count with map width so long runs still show strong motion cues.
        bucket_spacing = 950
        cloud_count = max(35, int(self.width / bucket_spacing))
        spacing = self.width / float(cloud_count)

        for i in range(cloud_count):
            base_x = (i + 0.5) * spacing
            self.clouds.append({
                "x": base_x + random.uniform(-spacing * 0.42, spacing * 0.42),
                # Fixed distance above local terrain for this cloud.
                "terrain_gap": random.choice(cloud_clearance_choices) + random.randint(-18, 22),
                "s": random.randint(24, 50),
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
            wrap_margin = 280
            if c["x"] < -wrap_margin:
                c["x"] = self.width + wrap_margin
            elif c["x"] > self.width + wrap_margin:
                c["x"] = -wrap_margin
    
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
    def __init__(self, x, y, hazard_type="spike", name=None, hp=1, destruction_points=0):
        self.x = x
        self.y = y
        self.type = hazard_type  # "spike", "wall", "ice"
        self.name = name or hazard_type
        self.size = 15
        self.width = self.size * 2
        self.height = self.size * 2
        if self.type == "snowman":
            self.width, self.height = 72, 140
        elif self.type == "snowmound":
            self.width, self.height = 78, 44
        elif self.type == "rocky_hill":
            self.width, self.height = 120, 68
        elif self.type == "iceberg":
            self.width, self.height = 145, 108
        elif self.type == "glacier_wall":
            self.width, self.height = 170, 230
        self.max_hp = max(1.0, float(hp))
        self.hp = self.max_hp
        self.destruction_points = int(destruction_points)
        self.destroyed = False
        self.last_hit_ms = -10000
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
        """Check collision against obstacle bounds (circle vs expanded AABB)."""
        if self.destroyed or not self.active:
            return False
        left = self.x - self.width * 0.5 - player.size
        right = self.x + self.width * 0.5 + player.size
        top = self.y - self.height - player.size
        bottom = self.y + player.size * 0.35
        return left <= player.x <= right and top <= player.y <= bottom


class Environment:
    def __init__(self, ramp_height_level=0, ramp_drop_level=0):
        self.terrain = Terrain(
            PIXELS_PER_METER * WORLD_LENGTH_M,
            SCREEN_HEIGHT,
            ramp_height_level=ramp_height_level,
            ramp_drop_level=ramp_drop_level,
        )
        self.hazards = []
        self.collectibles = []
        self.spawn_hazards()
    
    def spawn_hazards(self):
        """Spawn fixed milestone obstacles along the course."""
        self.hazards = []
        for entry in OBSTACLE_LAYOUT:
            world_x = entry["distance_m"] * PIXELS_PER_METER
            ground_y = self.terrain.get_ground_y_at(world_x)
            self.hazards.append(
                Hazard(
                    world_x,
                    ground_y,
                    hazard_type=entry["kind"],
                    name=entry["name"],
                    hp=entry["hp"],
                    destruction_points=entry["destruction_points"],
                )
            )
    
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

