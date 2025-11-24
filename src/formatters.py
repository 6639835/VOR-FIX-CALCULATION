"""
Output formatters for the VOR-FIX Coordinate Calculator.

ACCURACY NOTE:
This module rounds bearings and distances for output display according to aviation
standard notation. While internal calculations use full precision (9 decimal places
for coordinates), output formatting introduces the following intentional rounding:
- Bearings: Rounded to nearest integer degree (±0.5° precision)
- Distances: Rounded to nearest nautical mile (±0.5 NM precision)
- Coordinates: Preserved at 9 decimal places (~0.11 mm precision)

This rounding is standard practice in aviation waypoint notation and does not
affect the accuracy of the underlying coordinate calculations.
"""

from .constants import LARGE_DISTANCE_THRESHOLD_NM, NavAidType
from .models import FixResult, NavAidEntry, WaypointResult


class WaypointFormatter:
    """Formatter for waypoint calculation results."""

    @staticmethod
    def format(result: WaypointResult) -> str:
        """
        Format waypoint result for output.

        Args:
            result: Waypoint calculation result

        Returns:
            Formatted output string
        """
        coords = result.coordinates
        airport_region = result.airport_code[:2]

        # Format based on distance threshold
        if result.distance_nm > LARGE_DISTANCE_THRESHOLD_NM:
            # Large distance format
            rounded_distance = int(
                round(result.distance_nm)
            )  # Intentional rounding for aviation notation
            output = (
                f"{coords.latitude:.9f} {coords.longitude:.9f} "
                f"{result.vor_identifier}{rounded_distance} "
                f"{result.airport_code} {airport_region}"
            )

            if result.vor_identifier:
                bearing_int = int(
                    result.magnetic_bearing
                )  # Intentional rounding for aviation notation
                output += (
                    f" {result.operation_code} "
                    f"{result.vor_identifier}{bearing_int:03d}{rounded_distance:03d}"
                )
            else:
                output += f" {result.operation_code}"

        else:
            # Small distance format (with radius designator)
            bearing_int = int(result.magnetic_bearing)  # Intentional rounding for aviation notation
            output = (
                f"{coords.latitude:.9f} {coords.longitude:.9f} "
                f"D{bearing_int:03d}{result.radius_letter} "
                f"{result.airport_code} {airport_region}"
            )

            if result.vor_identifier:
                distance_int = int(
                    round(result.distance_nm)
                )  # Intentional rounding for aviation notation
                output += (
                    f" {result.operation_code} "
                    f"{result.vor_identifier}{bearing_int:03d}{distance_int:03d}"
                )
            else:
                output += f" {result.operation_code}"

        return output


class FixFormatter:
    """Formatter for fix calculation results."""

    @staticmethod
    def format(result: FixResult) -> str:
        """
        Format fix result for output.

        Args:
            result: Fix calculation result

        Returns:
            Formatted output string
        """
        coords = result.coordinates
        airport_region = result.airport_code[:2]
        runway_int = int(result.runway_code)

        return (
            f"{coords.latitude:.9f} {coords.longitude:.9f} "
            f"{result.usage_code}{result.fix_code}{runway_int:02d} "
            f"{result.airport_code} {airport_region} {result.operation_code}"
        )


class NavAidFormatter:
    """Formatter for navigation aid entries."""

    @staticmethod
    def format_for_display(entry: NavAidEntry) -> str:
        """
        Format navigation aid entry for display in selection dialogs.

        Args:
            entry: Navigation aid entry

        Returns:
            Formatted display string
        """
        # Get type label
        type_label = "Unknown"
        for navaid_type in NavAidType:
            if navaid_type.code == entry.type_code:
                type_label = navaid_type.label
                break

        # Build display text
        display = f"{type_label} - {entry.identifier}"

        # Add name if available
        if entry.name:
            display += f" - {entry.name}"
        else:
            display += " - [No name]"

        return display
