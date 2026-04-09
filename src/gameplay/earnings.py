def compute_flight_earnings(
    distance,
    max_speed,
    max_altitude,
    duration,
    destruction,
    k_distance,
    l_speed,
    m_altitude,
    n_duration,
    o_destruction,
):
    """Compute money breakdown for a completed flight."""
    distance_money = distance * k_distance
    speed_money = max_speed * l_speed
    altitude_money = max_altitude * m_altitude
    duration_money = duration * n_duration
    destruction_money = destruction * o_destruction

    total = int(distance_money + speed_money + altitude_money + duration_money + destruction_money)
    return {
        "total": max(0, total),
        "distance_money": int(distance_money),
        "speed_money": int(speed_money),
        "altitude_money": int(altitude_money),
        "duration_money": int(duration_money),
        "destruction_money": int(destruction_money),
    }

