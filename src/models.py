"""
Data models for the VOR-FIX Coordinate Calculator.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Coordinates:
    """Geographic coordinates."""

    latitude: float
    longitude: float

    def __str__(self) -> str:
        return f"{self.latitude:.9f} {self.longitude:.9f}"


@dataclass
class WaypointInput:
    """Input data for waypoint calculation."""

    coordinates: Optional[Coordinates]
    identifier: str
    magnetic_bearing: float
    distance_nm: float
    declination: float
    airport_code: str
    vor_identifier: str


@dataclass
class WaypointResult:
    """Result of waypoint calculation."""

    coordinates: Coordinates
    radius_letter: str
    airport_code: str
    operation_code: str
    vor_identifier: str
    magnetic_bearing: float
    distance_nm: float


@dataclass
class FixInput:
    """Input data for fix calculation."""

    coordinates: Coordinates
    identifier: str
    fix_type: str
    fix_usage: str
    runway_code: str
    airport_code: str


@dataclass
class FixResult:
    """Result of fix calculation."""

    coordinates: Coordinates
    fix_code: str
    usage_code: str
    runway_code: str
    airport_code: str
    operation_code: str


@dataclass
class NavAidEntry:
    """Navigation aid entry from data file."""

    type_code: str
    latitude: float
    longitude: float
    identifier: str
    name: Optional[str] = None
    raw_parts: Optional[list[str]] = None

    @property
    def display_name(self) -> str:
        """Get display name for the navaid."""
        if self.name:
            return f"{self.identifier} - {self.name}"
        return self.identifier
