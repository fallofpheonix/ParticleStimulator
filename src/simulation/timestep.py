from __future__ import annotations


def choose_time_step(max_speed_m_s: float, base_dt_s: float, min_dt_s: float = 1.0e-12) -> float:
    if max_speed_m_s <= 0.0:
        return base_dt_s
    scale = max(1.0, max_speed_m_s / 1.0e7)
    return max(min_dt_s, base_dt_s / scale)
