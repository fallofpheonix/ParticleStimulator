from __future__ import annotations

import math

from core.constants import SPEED_OF_LIGHT_M_S


def gamma_from_speed(speed_m_s: float) -> float:
    limited_speed = min(abs(speed_m_s), 0.999_999_999 * SPEED_OF_LIGHT_M_S)
    beta = limited_speed / SPEED_OF_LIGHT_M_S
    return 1.0 / math.sqrt(1.0 - (beta * beta))


def beta_from_speed(speed_m_s: float) -> float:
    return min(abs(speed_m_s), SPEED_OF_LIGHT_M_S) / SPEED_OF_LIGHT_M_S
