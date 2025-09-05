"""
Contains utility functions for the application.
"""
import math
from typing import Any


def safe_int(x: Any, default: int) -> int:
    """
    Safely converts a value to an integer.

    This function attempts to convert the given value `x` to an integer. If the
    conversion is successful, the integer value is returned. If the conversion
    fails due to a `ValueError` (e.g., `int("abc")`) or a `TypeError` (e.g.,
    `int(None)`), the `default` value is returned instead.

    Args:
        x: The value to convert to an integer.
        default: The default integer value to return if conversion fails.

    Returns:
        The integer representation of `x` or the `default` value.
    """
    try:
        return int(x)
    except (ValueError, TypeError):
        return default


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth.

    This implementation uses the Haversine formula to calculate the distance
    between two points specified in decimal degrees.

    Args:
        lat1: Latitude of the first point in decimal degrees.
        lon1: Longitude of the first point in decimal degrees.
        lat2: Latitude of the second point in decimal degrees.
        lon2: Longitude of the second point in decimal degrees.

    Returns:
        The distance between the two points in meters.
    """
    radius_of_earth = 6371000.0  # in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius_of_earth * c
