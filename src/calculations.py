"""
Geodesic calculations for the VOR-FIX Coordinate Calculator.
"""

from geographiclib.geodesic import Geodesic

from .constants import METERS_PER_NAUTICAL_MILE, RADIUS_RANGES
from .models import Coordinates

# Initialize the WGS84 ellipsoid model
GEODESIC = Geodesic.WGS84


def calculate_destination_point(
    origin: Coordinates, azimuth: float, distance_nm: float
) -> Coordinates:
    """
    Calculate the destination point given origin, azimuth, and distance.

    Args:
        origin: Starting coordinates
        azimuth: True bearing in degrees (0-360)
        distance_nm: Distance in nautical miles

    Returns:
        Coordinates of the destination point
    """
    distance_meters = distance_nm * METERS_PER_NAUTICAL_MILE
    result = GEODESIC.Direct(origin.latitude, origin.longitude, azimuth, distance_meters)
    return Coordinates(latitude=result["lat2"], longitude=result["lon2"])


def magnetic_to_true_bearing(magnetic_bearing: float, declination: float) -> float:
    """
    Convert magnetic bearing to true bearing.

    Args:
        magnetic_bearing: Magnetic bearing in degrees
        declination: Magnetic declination in degrees

    Returns:
        True bearing in degrees (0-360)
    """
    return (magnetic_bearing + declination) % 360.0


def get_radius_designator(distance_nm: float) -> str:
    """
    Get the single-letter radius designator based on distance.

    Args:
        distance_nm: Distance in nautical miles

    Returns:
        Single-letter radius designator (A-Z)
    """
    for low, high, letter in RADIUS_RANGES:
        if low <= distance_nm <= high:
            return letter
    return "Z"


def calculate_waypoint(
    origin: Coordinates, magnetic_bearing: float, distance_nm: float, declination: float
) -> Coordinates:
    """
    Calculate waypoint coordinates from origin, magnetic bearing, distance, and declination.

    Args:
        origin: Starting coordinates (VOR/DME/NDB position)
        magnetic_bearing: Magnetic bearing in degrees
        distance_nm: Distance in nautical miles
        declination: Magnetic declination in degrees

    Returns:
        Calculated waypoint coordinates
    """
    true_bearing = magnetic_to_true_bearing(magnetic_bearing, declination)
    return calculate_destination_point(origin, true_bearing, distance_nm)
