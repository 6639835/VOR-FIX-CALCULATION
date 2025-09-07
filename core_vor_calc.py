#!/usr/bin/env python3
"""
Core VOR calculation components extracted for testing without tkinter dependencies.
"""

import math
import datetime
import importlib.util
from typing import Optional, Tuple, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
from geographiclib.geodesic import Geodesic

# Constants for the Earth's ellipsoid model with maximum precision settings
GEODESIC = Geodesic.WGS84

# Ultra high precision settings for intersection calculations
MAX_ITERATIONS = 200  # Increased max iterations for better convergence with tight tolerance
DISTANCE_TOLERANCE_NM = 0.00000054  # About 1 meter in nautical miles (1/1852)
DISTANCE_TOLERANCE_M = 1.0  # Tolerance in meters (1-meter precision)
ANGLE_TOLERANCE_DEG = 0.0001  # Extremely precise angular tolerance (about 0.36 arcseconds)

# Enhanced precision constants for improved accuracy
NEWTON_RAPHSON_TOLERANCE_M = 0.1  # Even tighter tolerance for Newton-Raphson
GRADIENT_STEP_SIZE = 0.001  # Small step size for numerical gradient calculation
MIN_SEARCH_RANGE_NM = 0.000001  # Minimum search range to prevent infinite loops

# Meters per nautical mile, defined exactly (constant should never be modified)
METERS_PER_NM = 1852.0

def _validate_constants():
    """Validate critical constants to prevent division by zero errors."""
    if METERS_PER_NM <= 0:
        raise ValueError("METERS_PER_NM constant must be positive")

# Validate constants on import
_validate_constants()

class FileType(Enum):
    NAV = "NAV"
    FIX = "FIX"

@dataclass
class Coordinates:
    """Represents geographic coordinates with validation."""
    lat: float
    lon: float
    
    def __post_init__(self):
        if not (-90 <= self.lat <= 90):
            raise ValueError(f"Latitude {self.lat} out of range (±90)")
        if not (-180 <= self.lon <= 180):
            raise ValueError(f"Longitude {self.lon} out of range [-180, 180]")
    
    def __str__(self) -> str:
        return f"{self.lat:.9f} {self.lon:.9f}"

class CoordinateCalculator:
    """Service for performing coordinate calculations."""
    
    @staticmethod
    def meters_to_nm(meters: float) -> float:
        """Convert meters to nautical miles with high precision."""
        return meters / METERS_PER_NM

    @staticmethod
    def nm_to_meters(nm: float) -> float:
        """Convert nautical miles to meters with high precision."""
        return nm * METERS_PER_NM

    @staticmethod
    def calculate_target_coords_geodesic(
        start_coords: Coordinates, 
        azimuth: float, 
        distance_nm: float
    ) -> Coordinates:
        """Calculate target coordinates with ultra-high precision and adaptive refinement."""
        distance_m = CoordinateCalculator.nm_to_meters(distance_nm)
        
        # Use high-precision direct calculation
        result = GEODESIC.Direct(start_coords.lat, start_coords.lon, azimuth, distance_m)
        initial_coords = Coordinates(result['lat2'], result['lon2'])
        
        # Verify the calculation with inverse calculation
        verification = GEODESIC.Inverse(
            start_coords.lat, start_coords.lon, 
            result['lat2'], result['lon2']
        )
        actual_distance_m = verification['s12']
        distance_error_m = abs(actual_distance_m - distance_m)
        
        # If error is acceptable, return immediately
        if distance_error_m <= DISTANCE_TOLERANCE_M:
            return initial_coords
        
        # For distances with higher error, use adaptive multi-step approach
        optimal_coords = initial_coords
        min_error = distance_error_m
        
        # Try different step sizes to find optimal accuracy
        step_sizes = [100, 250, 500, 1000]  # Different step sizes in km
        
        for step_size_km in step_sizes:
            if distance_nm < step_size_km / 1.852:  # Convert km to nm
                continue  # Skip if distance is smaller than step size
                
            num_steps = max(2, int(distance_nm * 1.852 / step_size_km))
            step_coords = start_coords
            step_distance = distance_m / num_steps
            
            # Multi-step calculation with verification at each step
            for step in range(num_steps):
                step_result = GEODESIC.Direct(
                    step_coords.lat, step_coords.lon, azimuth, step_distance
                )
                step_coords = Coordinates(step_result['lat2'], step_result['lon2'])
            
            # Final verification for this approach
            final_verification = GEODESIC.Inverse(
                start_coords.lat, start_coords.lon,
                step_coords.lat, step_coords.lon
            )
            final_distance_error = abs(final_verification['s12'] - distance_m)
            
            # Keep the most accurate result
            if final_distance_error < min_error:
                min_error = final_distance_error
                optimal_coords = step_coords
                
                # If we achieved excellent accuracy, stop searching
                if min_error <= DISTANCE_TOLERANCE_M:
                    break
        
        return optimal_coords

    @staticmethod
    def validate_calculation_accuracy(
        start_coords: Coordinates,
        end_coords: Coordinates,
        expected_azimuth: float,
        expected_distance_nm: float
    ) -> Dict[str, float]:
        """Validate the accuracy of a coordinate calculation."""
        result = GEODESIC.Inverse(start_coords.lat, start_coords.lon, end_coords.lat, end_coords.lon)
        
        actual_distance_m = result['s12']
        actual_distance_nm = CoordinateCalculator.meters_to_nm(actual_distance_m)
        actual_azimuth = result['azi1']
        
        # Normalize azimuths to 0-360 range
        actual_azimuth = actual_azimuth % 360
        expected_azimuth = expected_azimuth % 360
        
        # Calculate azimuth difference (shortest angular distance)
        azimuth_diff = abs(actual_azimuth - expected_azimuth)
        azimuth_diff = min(azimuth_diff, 360 - azimuth_diff)
        
        distance_error_nm = abs(actual_distance_nm - expected_distance_nm)
        distance_error_m = abs(actual_distance_m - CoordinateCalculator.nm_to_meters(expected_distance_nm))
        
        return {
            'distance_error_nm': distance_error_nm,
            'distance_error_m': distance_error_m,
            'azimuth_error_deg': azimuth_diff,
            'actual_distance_nm': actual_distance_nm,
            'actual_azimuth_deg': actual_azimuth,
            'accuracy_rating': CoordinateCalculator._calculate_accuracy_rating(distance_error_m, azimuth_diff)
        }
    
    @staticmethod
    def _calculate_accuracy_rating(distance_error_m: float, azimuth_error_deg: float) -> str:
        """Calculate accuracy rating based on errors."""
        if distance_error_m <= 1.0 and azimuth_error_deg <= 0.001:
            return "EXCELLENT"
        elif distance_error_m <= 5.0 and azimuth_error_deg <= 0.01:
            return "VERY_GOOD"
        elif distance_error_m <= 10.0 and azimuth_error_deg <= 0.1:
            return "GOOD"
        elif distance_error_m <= 50.0 and azimuth_error_deg <= 1.0:
            return "ACCEPTABLE"
        else:
            return "POOR"

    @staticmethod
    def calculate_precision_metrics(
        calculations: List[Tuple[Coordinates, Coordinates, float, float]]
    ) -> Dict[str, float]:
        """Calculate overall precision metrics for multiple calculations."""
        if not calculations:
            return {
                'mean_distance_error_m': 0.0,
                'max_distance_error_m': 0.0,
                'min_distance_error_m': 0.0,
                'mean_azimuth_error_deg': 0.0,
                'max_azimuth_error_deg': 0.0,
                'min_azimuth_error_deg': 0.0,
                'total_calculations': 0
            }
        
        distance_errors = []
        azimuth_errors = []
        
        for start_coords, end_coords, expected_azimuth, expected_distance_nm in calculations:
            metrics = CoordinateCalculator.validate_calculation_accuracy(
                start_coords, end_coords, expected_azimuth, expected_distance_nm
            )
            distance_errors.append(metrics['distance_error_m'])
            azimuth_errors.append(metrics['azimuth_error_deg'])
        
        return {
            'mean_distance_error_m': sum(distance_errors) / len(distance_errors),
            'max_distance_error_m': max(distance_errors),
            'min_distance_error_m': min(distance_errors),
            'mean_azimuth_error_deg': sum(azimuth_errors) / len(azimuth_errors),
            'max_azimuth_error_deg': max(azimuth_errors),
            'min_azimuth_error_deg': min(azimuth_errors),
            'total_calculations': len(calculations)
        }

class InputValidator:
    """Validates user input for the application."""
    
    @staticmethod
    def validate_coordinates(coords_str: str) -> Coordinates:
        """Validate and parse coordinate string."""
        if not coords_str.strip():
            raise ValueError("Coordinates cannot be empty")
        
        parts = coords_str.strip().split()
        if len(parts) != 2:
            raise ValueError("Coordinates must contain exactly two numbers: latitude and longitude")
        
        try:
            lat, lon = map(float, parts)
            return Coordinates(lat, lon)
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError("Coordinates must be valid numbers")
            raise ValueError(f"Invalid coordinate format: {str(e)}")
    
    @staticmethod
    def validate_bearing(bearing_str: str) -> float:
        """Validate bearing input."""
        try:
            bearing = float(bearing_str)
            if not (0 <= bearing < 360):
                raise ValueError("Bearing should be within 0-359 degrees")
            return bearing
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError("Bearing must be a number")
            raise e

class NavigationDataService:
    """Service for reading and searching navigation data files."""
    
    def __init__(self):
        self.nav_file_path = ""
        self.fix_file_path = ""
    
    def set_file_path(self, file_type: FileType, path: str) -> None:
        """Set the file path for the specified file type."""
        if file_type == FileType.NAV:
            self.nav_file_path = path
        else:
            self.fix_file_path = path
    
    def search_identifier(
        self, 
        identifier: str, 
        file_type: FileType
    ) -> List[List[str]]:
        """Search for an identifier in the specified file type."""
        file_path = (self.nav_file_path if file_type == FileType.NAV 
                    else self.fix_file_path)
        
        if not file_path:
            raise FileNotFoundError(f"No {file_type.value} file selected")
        
        try:
            with open(file_path, 'r') as file:
                matching_lines = []
                for line in file:
                    parts = line.strip().split()
                    relevant_index = 7 if file_type == FileType.NAV else 2
                    
                    if (len(parts) > relevant_index and 
                        parts[relevant_index] == identifier.upper()):
                        matching_lines.append(parts)
                
                return matching_lines
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
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
                except Exception:
                    try:
                        # Fall back to standard resolution
                        self.geo_mag = GeoMag(high_resolution=False)
                        self.geomag_initialized = True
                    except Exception:
                        self.geomag_initialized = False
            else:
                self.pygeomag_available = False
                self.geomag_initialized = False
        except ImportError:
            self.pygeomag_available = False
            self.geomag_initialized = False
    
    def get_declination(self, coordinates: Coordinates, altitude_m: float = 0.0, date: Optional[datetime.datetime] = None) -> float:
        """Calculate magnetic declination at the given coordinates with enhanced precision."""
        if not (self.pygeomag_available and self.geomag_initialized):
            return 0.0
        
        try:
            # Use provided date or current date
            target_date = date or datetime.datetime.today()
            
            # Calculate decimal year with high precision
            year_start = datetime.datetime(target_date.year, 1, 1)
            year_end = datetime.datetime(target_date.year + 1, 1, 1)
            year_duration = (year_end - year_start).total_seconds()
            elapsed_seconds = (target_date - year_start).total_seconds()
            decimal_year = target_date.year + (elapsed_seconds / year_duration)
            
            # Convert altitude to kilometers for geomag calculation
            altitude_km = altitude_m / 1000.0
            
            result = self.geo_mag.calculate(
                glat=coordinates.lat, 
                glon=coordinates.lon, 
                alt=altitude_km, 
                time=decimal_year
            )
            
            # Return declination with proper rounding to avoid floating point precision issues
            return round(result.d, 4)  # Round to 0.0001 degree precision
            
        except Exception:
            return 0.0