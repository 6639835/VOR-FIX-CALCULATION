"""
Constants and configuration for the VOR-FIX Coordinate Calculator.
"""

from enum import Enum

# Geodesic constants
METERS_PER_NAUTICAL_MILE = 1852.0
LARGE_DISTANCE_THRESHOLD_NM = 26.5

# Coordinate validation ranges
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0
BEARING_MIN, BEARING_MAX = 0.0, 360.0
DISTANCE_MIN = 0.0
DECLINATION_MIN, DECLINATION_MAX = -180.0, 180.0
RUNWAY_MIN, RUNWAY_MAX = 0, 99

# Identifier validation
AIRPORT_CODE_LENGTH = 4
VOR_IDENTIFIER_MIN_LENGTH = 3
VOR_IDENTIFIER_MAX_LENGTH = 4


class OperationType(Enum):
    """Flight operation types."""

    DEPARTURE = ("Departure", "4464713")
    ARRIVAL = ("Arrival", "4530249")
    APPROACH = ("Approach", "4595785")

    def __init__(self, label: str, code: str):
        self.label = label
        self.code = code


class FixType(Enum):
    """Navigation fix types."""

    VORDME = ("VORDME", "D")
    VOR = ("VOR", "V")
    NDBDME = ("NDBDME", "Q")
    NDB = ("NDB", "N")
    ILS = ("ILS", "I")
    RNP = ("RNP", "R")

    def __init__(self, label: str, code: str):
        self.label = label
        self.code = code


class FixUsage(Enum):
    """Fix usage types in approach procedures."""

    FINAL_APPROACH = ("Final approach fix", "F")
    INITIAL_APPROACH = ("Initial approach fix", "A")
    INTERMEDIATE_APPROACH = ("Intermediate approach fix", "I")
    FINAL_APPROACH_COURSE = ("Final approach course fix", "C")
    MISSED_APPROACH_POINT = ("Missed approach point fix", "M")

    def __init__(self, label: str, code: str):
        self.label = label
        self.code = code


class NavAidType(Enum):
    """Navigation aid types as found in data files."""

    VOR = ("3", "VOR")
    DME_VOR = ("12", "DME (VOR)")
    NDB = ("2", "NDB")
    DME = ("13", "DME")
    OUTER_MARKER = ("7", "OUTER MARKER")
    MIDDLE_MARKER = ("8", "MIDDLE MARKER")
    INNER_MARKER = ("9", "INNER MARKER")

    def __init__(self, code: str, label: str):
        self.code = code
        self.label = label


# Radius designator ranges (distance in NM to letter code)
RADIUS_RANGES = [
    (0.1, 1.4, "A"),
    (1.5, 2.4, "B"),
    (2.5, 3.4, "C"),
    (3.5, 4.4, "D"),
    (4.5, 5.4, "E"),
    (5.5, 6.4, "F"),
    (6.5, 7.4, "G"),
    (7.5, 8.4, "H"),
    (8.5, 9.4, "I"),
    (9.5, 10.4, "J"),
    (10.5, 11.4, "K"),
    (11.5, 12.4, "L"),
    (12.5, 13.4, "M"),
    (13.5, 14.4, "N"),
    (14.5, 15.4, "O"),
    (15.5, 16.4, "P"),
    (16.5, 17.4, "Q"),
    (17.5, 18.4, "R"),
    (18.5, 19.4, "S"),
    (19.5, 20.4, "T"),
    (20.5, 21.4, "U"),
    (21.5, 22.4, "V"),
    (22.5, 23.4, "W"),
    (23.5, 24.4, "X"),
    (24.5, 25.4, "Y"),
    (25.5, 26.4, "Z"),
]


# File type constants
class FileType(Enum):
    """Data file types."""

    NAV = "NAV"
    FIX = "FIX"


# File format indices
NAV_FILE_LAT_INDEX = 1
NAV_FILE_LON_INDEX = 2
NAV_FILE_IDENTIFIER_INDEX = 7
NAV_FILE_TENTH_PART_INDEX = 9

FIX_FILE_LAT_INDEX = 0
FIX_FILE_LON_INDEX = 1
FIX_FILE_IDENTIFIER_INDEX = 2
