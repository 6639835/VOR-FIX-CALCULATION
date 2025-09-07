"""
VOR Fix Calculation Tool - Coordinate Calculator

This module contains the core coordinate calculation logic using geodesic mathematics.
"""

import math
from typing import Optional
from geographiclib.geodesic import Geodesic

from .models import Coordinates, METERS_PER_NM, MAX_ITERATIONS, DISTANCE_TOLERANCE_M


class CoordinateCalculator:
    """Service for performing coordinate calculations."""

    def __init__(self):
        """Initialize the calculator with WGS84 ellipsoid."""
        self.geodesic = Geodesic.WGS84

    @staticmethod
    def meters_to_nm(meters: float) -> float:
        """Convert meters to nautical miles with high precision."""
        return meters / METERS_PER_NM

    @staticmethod
    def nm_to_meters(nm: float) -> float:
        """Convert nautical miles to meters with high precision."""
        return nm * METERS_PER_NM

    def calculate_target_coords_geodesic(
        self,
        start_coords: Coordinates,
        azimuth: float,
        distance_nm: float
    ) -> Coordinates:
        """Calculate target coordinates with ultra-high precision."""
        distance_m = self.nm_to_meters(distance_nm)

        result = self.geodesic.Direct(start_coords.lat, start_coords.lon, azimuth, distance_m)

        # Verify the calculation
        verification = self.geodesic.Inverse(
            start_coords.lat, start_coords.lon,
            result['lat2'], result['lon2']
        )
        actual_distance_m = verification['s12']
        distance_error_m = abs(actual_distance_m - distance_m)

        # For very long distances, use multi-step approach
        if distance_error_m > 0.1:
            num_steps = max(1, int(distance_nm / 500))
            if num_steps > 1:
                step_coords = start_coords
                step_distance = distance_m / num_steps
                for _ in range(num_steps):
                    step_result = self.geodesic.Direct(
                        step_coords.lat, step_coords.lon, azimuth, step_distance
                    )
                    step_coords = Coordinates(step_result['lat2'], step_result['lon2'])
                return step_coords

        return Coordinates(result['lat2'], result['lon2'])

    @staticmethod
    def get_radius_letter(distance_nm: float) -> str:
        """Get the single-letter radius designator."""
        ranges = [
            (0.1, 1.4, 'A'), (1.5, 2.4, 'B'), (2.5, 3.4, 'C'), (3.5, 4.4, 'D'),
            (4.5, 5.4, 'E'), (5.5, 6.4, 'F'), (6.5, 7.4, 'G'), (7.5, 8.4, 'H'),
            (8.5, 9.4, 'I'), (9.5, 10.4, 'J'), (10.5, 11.4, 'K'), (11.5, 12.4, 'L'),
            (12.5, 13.4, 'M'), (13.5, 14.4, 'N'), (14.5, 15.4, 'O'), (15.5, 16.4, 'P'),
            (16.5, 17.4, 'Q'), (17.5, 18.4, 'R'), (18.5, 19.4, 'S'), (19.5, 20.4, 'T'),
            (20.5, 21.4, 'U'), (21.5, 22.4, 'V'), (22.5, 23.4, 'W'), (23.5, 24.4, 'X'),
            (24.5, 25.4, 'Y'), (25.5, 26.4, 'Z')
        ]
        for low, high, letter in ranges:
            if low <= distance_nm <= high:
                return letter
        return 'Z'

    def find_radial_distance_intersection(
        self,
        fix_coords: Coordinates,
        true_bearing: float,
        dme_coords: Coordinates,
        distance_nm: float
    ) -> Coordinates:
        """Find intersection of radial from FIX with distance circle from DME."""
        distance_m = self.nm_to_meters(distance_nm)

        # Calculate distance between FIX and DME
        fix_dme_result = self.geodesic.Inverse(
            fix_coords.lat, fix_coords.lon,
            dme_coords.lat, dme_coords.lon
        )
        fix_dme_distance_nm = self.meters_to_nm(fix_dme_result['s12'])

        # Determine search range
        if distance_nm < 0.05:
            min_dist, max_dist = 0.0, 0.2
        elif distance_nm < 0.5:
            min_dist, max_dist = 0.0, max(1.0, distance_nm * 2)
        else:
            min_dist = max(0.0, fix_dme_distance_nm - distance_nm - 1)
            max_dist = fix_dme_distance_nm + distance_nm + 1

        # Binary search for intersection
        best_approx_distance = float('inf')
        best_approx_point = Coordinates(0, 0)

        for iteration in range(MAX_ITERATIONS):
            test_dist = (min_dist + max_dist) / 2.0
            test_point_result = self.geodesic.Direct(
                fix_coords.lat, fix_coords.lon, true_bearing,
                self.nm_to_meters(test_dist)
            )
            test_point = Coordinates(test_point_result['lat2'], test_point_result['lon2'])

            # Calculate distance from test point to DME
            test_to_dme = self.geodesic.Inverse(
                test_point.lat, test_point.lon,
                dme_coords.lat, dme_coords.lon
            )
            test_to_dme_m = test_to_dme['s12']

            error_m = abs(test_to_dme_m - distance_m)

            if error_m < best_approx_distance:
                best_approx_distance = error_m
                best_approx_point = test_point

            if error_m < DISTANCE_TOLERANCE_M:
                break

            # Adjust search range
            if test_to_dme_m > distance_m:
                max_dist = test_dist
            else:
                min_dist = test_dist

            if (max_dist - min_dist) < 0.000001:
                break

        return best_approx_point
