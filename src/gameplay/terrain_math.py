import math


def get_terrain_slope_at_x(points, x):
    """Return terrain slope for world x using piecewise linear terrain points."""
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        if x1 <= x <= x2:
            dx = x2 - x1
            return ((y2 - y1) / dx) if dx != 0 else 0.0
    return 0.0


def project_velocity_to_slope(vx, vy, slope, preserve_ratio=0.0):
    """Resolve inward normal velocity and keep tangent-aligned motion on a slope."""
    norm = math.sqrt(1.0 + slope * slope)
    tx = 1.0 / norm
    ty = slope / norm

    nx = -slope / norm
    ny = 1.0 / norm
    vn_inward = (vx * nx) + (vy * ny)
    if vn_inward > 0.0:
        vx -= vn_inward * nx
        vy -= vn_inward * ny

    tangential_speed = (vx * tx) + (vy * ty)

    if preserve_ratio > 0.0:
        preserve_speed = math.hypot(vx, vy) * preserve_ratio
        if abs(tangential_speed) < preserve_speed:
            if tangential_speed > 1e-6:
                tangential_speed = preserve_speed
            elif tangential_speed < -1e-6:
                tangential_speed = -preserve_speed

    return tx * tangential_speed, ty * tangential_speed

