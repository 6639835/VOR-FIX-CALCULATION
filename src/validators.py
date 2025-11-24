"""
Input validation for the VOR-FIX Coordinate Calculator.
"""

from .constants import (
    AIRPORT_CODE_LENGTH,
    BEARING_MAX,
    BEARING_MIN,
    DECLINATION_MAX,
    DECLINATION_MIN,
    DISTANCE_MIN,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    RUNWAY_MAX,
    RUNWAY_MIN,
    VOR_IDENTIFIER_MAX_LENGTH,
    VOR_IDENTIFIER_MIN_LENGTH,
)
from .models import Coordinates


class ValidationError(Exception):
    """Custom exception for validation errors."""


class CoordinateValidator:
    """Validator for geographic coordinates."""

    @staticmethod
    def validate(latitude: float, longitude: float) -> None:
        """
        Validate latitude and longitude values.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Raises:
            ValidationError: If coordinates are invalid
        """
        if not (LAT_MIN <= latitude <= LAT_MAX):
            raise ValidationError(f"Latitude must be between {LAT_MIN} and {LAT_MAX} degrees")

        if not (LON_MIN <= longitude <= LON_MAX):
            raise ValidationError(f"Longitude must be between {LON_MIN} and {LON_MAX} degrees")

    @staticmethod
    def parse_coordinates(coord_str: str) -> Coordinates:
        """
        Parse coordinates from a string.

        Args:
            coord_str: String in format "latitude longitude"

        Returns:
            Coordinates object

        Raises:
            ValidationError: If parsing or validation fails
        """
        if not coord_str or not coord_str.strip():
            raise ValidationError("Coordinates cannot be empty")

        parts = coord_str.strip().split()
        if len(parts) != 2:
            raise ValidationError("Coordinates must be in format 'latitude longitude'")

        try:
            latitude = float(parts[0])
            longitude = float(parts[1])
        except ValueError as e:
            raise ValidationError(f"Invalid coordinate format: {e}") from e

        CoordinateValidator.validate(latitude, longitude)
        return Coordinates(latitude, longitude)


class BearingValidator:
    """Validator for bearing values."""

    @staticmethod
    def validate(bearing: float) -> None:
        """
        Validate magnetic bearing.

        Args:
            bearing: Bearing in degrees

        Raises:
            ValidationError: If bearing is invalid
        """
        if not (BEARING_MIN <= bearing <= BEARING_MAX):
            raise ValidationError(
                f"Bearing must be between {BEARING_MIN} and {BEARING_MAX} degrees"
            )

    @staticmethod
    def parse(bearing_str: str) -> float:
        """
        Parse bearing from string.

        Args:
            bearing_str: String representation of bearing

        Returns:
            Bearing in degrees (0-360, with 360 normalized to 0)

        Raises:
            ValidationError: If parsing or validation fails
        """
        if not bearing_str or not bearing_str.strip():
            raise ValidationError("Bearing cannot be empty")

        try:
            bearing = float(bearing_str.strip())
        except ValueError as e:
            raise ValidationError(f"Invalid bearing format: {e}") from e

        BearingValidator.validate(bearing)

        # Normalize 360 to 0
        if bearing == 360.0:
            bearing = 0.0

        return bearing


class DistanceValidator:
    """Validator for distance values."""

    @staticmethod
    def validate(distance: float) -> None:
        """
        Validate distance.

        Args:
            distance: Distance in nautical miles

        Raises:
            ValidationError: If distance is invalid
        """
        if distance <= DISTANCE_MIN:
            raise ValidationError(f"Distance must be greater than {DISTANCE_MIN} nautical miles")

    @staticmethod
    def parse(distance_str: str) -> float:
        """
        Parse distance from string.

        Args:
            distance_str: String representation of distance

        Returns:
            Distance in nautical miles

        Raises:
            ValidationError: If parsing or validation fails
        """
        if not distance_str or not distance_str.strip():
            raise ValidationError("Distance cannot be empty")

        try:
            distance = float(distance_str.strip())
        except ValueError as e:
            raise ValidationError(f"Invalid distance format: {e}") from e

        DistanceValidator.validate(distance)
        return distance


class DeclinationValidator:
    """Validator for magnetic declination."""

    @staticmethod
    def validate(declination: float) -> None:
        """
        Validate magnetic declination.

        Args:
            declination: Magnetic declination in degrees

        Raises:
            ValidationError: If declination is invalid
        """
        if not (DECLINATION_MIN <= declination <= DECLINATION_MAX):
            raise ValidationError(
                f"Declination must be between {DECLINATION_MIN} and {DECLINATION_MAX} degrees"
            )

    @staticmethod
    def parse(declination_str: str) -> float:
        """
        Parse declination from string.

        Args:
            declination_str: String representation of declination

        Returns:
            Declination in degrees

        Raises:
            ValidationError: If parsing or validation fails
        """
        if not declination_str or not declination_str.strip():
            raise ValidationError("Declination cannot be empty")

        try:
            declination = float(declination_str.strip())
        except ValueError as e:
            raise ValidationError(f"Invalid declination format: {e}") from e

        DeclinationValidator.validate(declination)
        return declination


class AirportCodeValidator:
    """Validator for airport codes."""

    @staticmethod
    def validate(code: str) -> None:
        """
        Validate airport code.

        Args:
            code: Airport ICAO code

        Raises:
            ValidationError: If code is invalid
        """
        if not code:
            raise ValidationError("Airport code cannot be empty")

        if len(code) != AIRPORT_CODE_LENGTH:
            raise ValidationError(f"Airport code must be exactly {AIRPORT_CODE_LENGTH} characters")

        if not code.isalpha():
            raise ValidationError("Airport code must contain only letters")

    @staticmethod
    def parse(code_str: str) -> str:
        """
        Parse and validate airport code.

        Args:
            code_str: Airport code string

        Returns:
            Uppercase airport code

        Raises:
            ValidationError: If validation fails
        """
        code = code_str.strip().upper()
        AirportCodeValidator.validate(code)
        return code


class VORIdentifierValidator:
    """Validator for VOR identifiers."""

    @staticmethod
    def validate(identifier: str, allow_empty: bool = True) -> None:
        """
        Validate VOR identifier.

        Args:
            identifier: VOR identifier
            allow_empty: Whether empty identifier is allowed

        Raises:
            ValidationError: If identifier is invalid
        """
        if not identifier:
            if not allow_empty:
                raise ValidationError("VOR identifier cannot be empty")
            return

        if not (VOR_IDENTIFIER_MIN_LENGTH <= len(identifier) <= VOR_IDENTIFIER_MAX_LENGTH):
            raise ValidationError(
                f"VOR identifier must be {VOR_IDENTIFIER_MIN_LENGTH}-"
                f"{VOR_IDENTIFIER_MAX_LENGTH} characters"
            )

        if not identifier.isalpha():
            raise ValidationError("VOR identifier must contain only letters")

    @staticmethod
    def parse(identifier_str: str, allow_empty: bool = True) -> str:
        """
        Parse and validate VOR identifier.

        Args:
            identifier_str: VOR identifier string
            allow_empty: Whether empty identifier is allowed

        Returns:
            Uppercase VOR identifier

        Raises:
            ValidationError: If validation fails
        """
        identifier = identifier_str.strip().upper()
        VORIdentifierValidator.validate(identifier, allow_empty)
        return identifier


class RunwayCodeValidator:
    """Validator for runway codes."""

    @staticmethod
    def validate(code: int) -> None:
        """
        Validate runway code.

        Args:
            code: Runway code number

        Raises:
            ValidationError: If code is invalid
        """
        if not (RUNWAY_MIN <= code <= RUNWAY_MAX):
            raise ValidationError(f"Runway code must be between {RUNWAY_MIN} and {RUNWAY_MAX}")

    @staticmethod
    def parse(code_str: str) -> int:
        """
        Parse and validate runway code.

        Args:
            code_str: Runway code string

        Returns:
            Runway code as integer

        Raises:
            ValidationError: If parsing or validation fails
        """
        if not code_str or not code_str.strip():
            raise ValidationError("Runway code cannot be empty")

        try:
            code = int(code_str.strip())
        except ValueError as e:
            raise ValidationError(f"Invalid runway code format: {e}") from e

        RunwayCodeValidator.validate(code)
        return code
