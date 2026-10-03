import numpy as np
import math

from collections.abc import Sequence


EARTH_RADIUS_M = 6371000.0      # rad of earth in meters


def haversine_distance(p1: Sequence[float], p2: Sequence[float]) -> float:
    """
    Get distance between 2 world coordinates.
    Requires points to be in (lon, lat)
    """
    lon1, lat1 = p1
    lon2, lat2 = p2

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2 
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = EARTH_RADIUS_M * c
    return distance
