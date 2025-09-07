"""
VOR Fix Calculation Tool - Input Validation

This module contains input validation logic for the application.
"""

from typing import Union
from .models import (
    Coordinates, ValidationResult, MIN_LATITUDE, MAX_LATITUDE,
    MIN_LONGITUDE, MAX_LONGITUDE, MIN_BEARING, MAX_BEARING, MIN_DISTANCE
)


class InputValidator:
    """Validates user input for the application."""

    @staticmethod
    def validate_coordinates(coords_str: str) -> Union[Coordinates, ValidationResult]:
        """Validate and parse coordinate string."""
        if not coords_str.strip():
            return ValidationResult(False, error_message="Coordinates cannot be empty")

        try:
            lat, lon = map(float, coords_str.split())
            coordinates = Coordinates(lat, lon)
            return ValidationResult(True, value=coordinates)
        except ValueError:
            return ValidationResult(
                False,
                error_message="Invalid coordinate format. Use 'latitude longitude'"
            )
        except Exception as e:
            return ValidationResult(
                False,
                error_message=f"Error parsing coordinates: {str(e)}"
            )

    @staticmethod
    def validate_bearing(bearing_str: str) -> ValidationResult:
        """Validate bearing input."""
        try:
            bearing = float(bearing_str)
            if not (MIN_BEARING <= bearing < MAX_BEARING):
                return ValidationResult(
                    False,
                    error_message=f"Bearing should be within {MIN_BEARING}-{MAX_BEARING-1} degrees"
                )
            return ValidationResult(True, value=bearing)
        except ValueError as e:
            if "could not convert" in str(e):
                return ValidationResult(False, error_message="Bearing must be a number")
            return ValidationResult(False, error_message=f"Bearing validation error: {str(e)}")

    @staticmethod
    def validate_distance(distance_str: str) -> ValidationResult:
        """Validate distance input."""
        try:
            distance = float(distance_str)
            if distance <= MIN_DISTANCE:
                return ValidationResult(
                    False,
                    error_message=f"Distance should be greater than {MIN_DISTANCE} nautical miles"
                )
            return ValidationResult(True, value=distance)
        except ValueError as e:
            if "could not convert" in str(e):
                return ValidationResult(False, error_message="Distance must be a number")
            return ValidationResult(False, error_message=f"Distance validation error: {str(e)}")

    @staticmethod
    def validate_airport_code(airport_code: str) -> ValidationResult:
        """Validate airport code."""
        code = airport_code.strip().upper()
        if len(code) != 4:
            return ValidationResult(False, error_message="Airport code must be 4 letters")
        if not code.isalpha():
            return ValidationResult(False, error_message="Airport code must contain only letters")
        return ValidationResult(True, value=code)

    @staticmethod
    def validate_vor_identifier(vor_id: str) -> ValidationResult:
        """Validate VOR identifier."""
        if not vor_id:
            return ValidationResult(True, value=vor_id)

        code = vor_id.strip().upper()
        if not (1 <= len(code) <= 3 and code.isalpha()):
            return ValidationResult(
                False,
                error_message="VOR identifier should be 1-3 letters and alphabetic"
            )
        return ValidationResult(True, value=code)

    @staticmethod
    def validate_runway_code(runway_str: str) -> ValidationResult:
        """Validate runway code."""
        try:
            runway = int(runway_str)
            if not (0 <= runway <= 99):
                return ValidationResult(
                    False,
                    error_message="Runway code should be between 0 and 99"
                )
            return ValidationResult(True, value=runway)
        except ValueError as e:
            if "invalid literal" in str(e):
                return ValidationResult(False, error_message="Runway code must be a number")
            return ValidationResult(False, error_message=f"Runway code validation error: {str(e)}")

    @staticmethod
    def validate_identifier(identifier: str) -> ValidationResult:
        """Validate general navigation identifier."""
        if not identifier or not identifier.strip():
            return ValidationResult(False, error_message="Identifier cannot be empty")

        code = identifier.strip().upper()
        if not code:
            return ValidationResult(False, error_message="Identifier cannot be empty")

        return ValidationResult(True, value=code)
