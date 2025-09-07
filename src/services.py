"""
VOR Fix Calculation Tool - Services

This module contains service classes for navigation data handling and magnetic declination calculations.
"""

import datetime
import importlib.util
import logging
from typing import List, Optional

from .models import Coordinates, FileType, NavigationEntry, NAV_TYPE_DESCRIPTIONS

logger = logging.getLogger(__name__)


class NavigationDataService:
    """Service for reading and searching navigation data files."""

    def __init__(self):
        self.nav_file_path = ""
        self.fix_file_path = ""

    def set_file_path(self, file_type: FileType, path: str) -> None:
        """Set the file path for the specified file type."""
        if file_type == FileType.NAV:
            self.nav_file_path = path
            logger.info(f"Set NAV file path: {path}")
        else:
            self.fix_file_path = path
            logger.info(f"Set FIX file path: {path}")

    def search_identifier(
        self,
        identifier: str,
        file_type: FileType
    ) -> List[NavigationEntry]:
        """Search for an identifier in the specified file type."""
        file_path = (self.nav_file_path if file_type == FileType.NAV
                    else self.fix_file_path)

        if not file_path:
            raise FileNotFoundError(f"No {file_type.value} file selected")

        try:
            matching_lines = []
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split()
                    relevant_index = 7 if file_type == FileType.NAV else 2

                    if (len(parts) > relevant_index and
                        parts[relevant_index] == identifier.upper()):

                        # Parse coordinates
                        try:
                            if file_type == FileType.NAV:
                                lat, lon = float(parts[1]), float(parts[2])
                            else:
                                lat, lon = float(parts[0]), float(parts[1])

                            coordinates = Coordinates(lat, lon)

                            # Get description
                            nav_type = parts[0] if file_type == FileType.NAV else "FIX"
                            type_desc = NAV_TYPE_DESCRIPTIONS.get(nav_type, "Unknown")

                            entry = NavigationEntry(
                                identifier=identifier,
                                coordinates=coordinates,
                                nav_type=nav_type,
                                description=type_desc,
                                additional_info={"raw_data": parts}
                            )
                            matching_lines.append(entry)

                        except (ValueError, IndexError) as e:
                            logger.warning(f"Error parsing line: {line.strip()}. Error: {e}")
                            continue

            return matching_lines

        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error reading {file_type.value} file: {e}")
            raise Exception(f"Error reading {file_type.value} file: {e}")


class MagneticDeclinationService:
    """Service for calculating magnetic declination."""

    def __init__(self):
        self._initialize_geomag()

    def _initialize_geomag(self) -> None:
        """Initialize the GeoMag library if available."""
        try:
            spec = importlib.util.find_spec("pygeomag")
            if spec is not None:
                from pygeomag import GeoMag
                self.pygeomag_available = True
                # Try with high resolution first
                try:
                    self.geo_mag = GeoMag(high_resolution=True)
                    self.geomag_initialized = True
                    logger.info("GeoMag initialized with high resolution")
                except Exception as e:
                    logger.warning(f"High resolution GeoMag failed: {e}")
                    try:
                        # Fall back to standard resolution
                        self.geo_mag = GeoMag(high_resolution=False)
                        self.geomag_initialized = True
                        logger.info("GeoMag initialized with standard resolution")
                    except Exception as e2:
                        logger.warning(f"Standard resolution GeoMag failed: {e2}")
                        self.geomag_initialized = False
            else:
                self.pygeomag_available = False
                self.geomag_initialized = False
                logger.info("pygeomag not available")
        except ImportError as e:
            logger.warning(f"Import error for pygeomag: {e}")
            self.pygeomag_available = False
            self.geomag_initialized = False

    def get_declination(self, coordinates: Coordinates) -> float:
        """Calculate magnetic declination at the given coordinates."""
        if not (self.pygeomag_available and self.geomag_initialized):
            logger.debug("GeoMag not available, returning 0.0 declination")
            return 0.0

        try:
            today = datetime.datetime.today()
            year = today.year
            day_of_year = today.timetuple().tm_yday
            time = year + (day_of_year - 1) / 365

            result = self.geo_mag.calculate(
                glat=coordinates.lat,
                glon=coordinates.lon,
                alt=0,
                time=time
            )
            declination = result.d
            logger.debug(f"Calculated declination: {declination:.1f}° at {coordinates}")
            return declination
        except Exception as e:
            logger.warning(f"Error calculating declination: {e}")
            return 0.0

    def is_available(self) -> bool:
        """Check if magnetic declination calculation is available."""
        return self.pygeomag_available and self.geomag_initialized
