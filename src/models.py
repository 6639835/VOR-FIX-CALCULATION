"""
VOR Fix Calculation Tool - Core Data Models and Constants

This module contains the core data models, constants, and enumerations
used throughout the VOR Fix Calculation application.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, Dict, List, Any, Union
import datetime

# Constants for the Earth's ellipsoid model with maximum precision settings
GEODESIC = None  # Will be initialized in calculator module

# Ultra high precision settings for intersection calculations
MAX_ITERATIONS = 200  # Increased max iterations for better convergence with tight tolerance
DISTANCE_TOLERANCE_NM = 0.00000054  # About 1 meter in nautical miles (1/1852)
DISTANCE_TOLERANCE_M = 1.0  # Tolerance in meters (1-meter precision)
ANGLE_TOLERANCE_DEG = 0.0001  # Extremely precise angular tolerance (about 0.36 arcseconds)

# Meters per nautical mile, defined exactly
METERS_PER_NM = 1852.0

# Coordinate validation constants
MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0

# Distance and bearing validation constants
MIN_BEARING = 0.0
MAX_BEARING = 360.0
MIN_DISTANCE = 0.0001  # Minimum distance in nautical miles

# Operation codes
OPERATION_CODES = {
    "Departure": "4464713",
    "Arrival": "4530249",
    "Approach": "4595785"
}

# FIX type codes
FIX_TYPE_CODES = {
    "VORDME": "D",
    "VOR": "V",
    "NDBDME": "Q",
    "NDB": "N",
    "ILS": "I",
    "RNP": "R"
}

# FIX usage codes
FIX_USAGE_CODES = {
    "Final approach fix": "F",
    "Initial approach fix": "A",
    "Intermediate approach fix": "I",
    "Final approach course fix": "C",
    "Missed approach point fix": "M"
}

# NAV type descriptions
NAV_TYPE_DESCRIPTIONS = {
    '3': "VOR",
    '12': "DME (VOR)",
    '2': "NDB",
    '13': 'DME',
    '7': 'OUTER MARKER',
    '8': 'MIDDLE MARKER',
    '9': 'INNER MARKER'
}


class AppMode(Enum):
    """Application operating modes."""
    WAYPOINT = "WAYPOINT"
    FIX = "FIX"


class FileType(Enum):
    """Types of navigation data files."""
    NAV = "NAV"
    FIX = "FIX"


class BearingMode(Enum):
    """Bearing calculation modes."""
    MAGNETIC = "Magnetic"
    TRUE = "True"


class DeclinationMode(Enum):
    """Magnetic declination calculation modes."""
    AUTO = "Auto"
    MANUAL = "Manual"


@dataclass
class Coordinates:
    """Represents geographic coordinates with validation."""
    lat: float
    lon: float

    def __post_init__(self) -> None:
        """Validate coordinates after initialization."""
        self._validate_latitude()
        self._validate_longitude()

    def _validate_latitude(self) -> None:
        """Validate latitude is within acceptable range."""
        if not (MIN_LATITUDE <= self.lat <= MAX_LATITUDE):
            raise ValueError(f"Latitude {self.lat} out of range ({MIN_LATITUDE} to {MAX_LATITUDE})")

    def _validate_longitude(self) -> None:
        """Validate longitude is within acceptable range."""
        if not (MIN_LONGITUDE <= self.lon <= MAX_LONGITUDE):
            raise ValueError(f"Longitude {self.lon} out of range ({MIN_LONGITUDE} to {MAX_LONGITUDE})")

    def __str__(self) -> str:
        """Return string representation with high precision."""
        return f"{self.lat:.9f} {self.lon:.9f}"

    def to_tuple(self) -> Tuple[float, float]:
        """Return coordinates as a tuple."""
        return (self.lat, self.lon)

    def distance_to(self, other: 'Coordinates') -> float:
        """Calculate distance to another coordinate in meters."""
        from geographiclib.geodesic import Geodesic
        result = Geodesic.WGS84.Inverse(self.lat, self.lon, other.lat, other.lon)
        return result['s12']


@dataclass
class CalculationResult:
    """Represents the result of a coordinate calculation."""
    coordinates: Coordinates
    output_string: str
    timestamp: str
    mode: AppMode


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    value: Any = None
    error_message: str = ""


@dataclass
class NavigationEntry:
    """Represents a navigation data entry from file."""
    identifier: str
    coordinates: Coordinates
    nav_type: str
    description: str = ""
    additional_info: Dict[str, Any] = field(default_factory=dict)
