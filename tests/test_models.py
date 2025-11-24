"""
Test suite for the models module.
"""

import pytest

from src.models import Coordinates, FixInput, FixResult, NavAidEntry, WaypointInput, WaypointResult


class TestCoordinates:
    """Tests for the Coordinates class."""

    def test_coordinates_creation(self):
        """Test creating coordinates."""
        coords = Coordinates(latitude=37.6213, longitude=-122.3790)
        assert coords.latitude == 37.6213
        assert coords.longitude == -122.3790

    def test_coordinates_string_representation(self):
        """Test string representation of coordinates."""
        coords = Coordinates(latitude=37.6213, longitude=-122.3790)
        result = str(coords)
        assert "37.621300000" in result
        assert "-122.379000000" in result

    def test_coordinates_immutable(self):
        """Test that coordinates are immutable (frozen dataclass)."""
        coords = Coordinates(latitude=37.6213, longitude=-122.3790)
        with pytest.raises(AttributeError):
            coords.latitude = 40.0


class TestWaypointInput:
    """Tests for the WaypointInput class."""

    def test_waypoint_input_creation(self):
        """Test creating waypoint input."""
        coords = Coordinates(latitude=37.6213, longitude=-122.3790)
        waypoint = WaypointInput(
            coordinates=coords,
            identifier="WYPT1",
            magnetic_bearing=90.0,
            distance_nm=10.0,
            declination=15.0,
            airport_code="KSFO",
            vor_identifier="SFO",
        )
        assert waypoint.identifier == "WYPT1"
        assert waypoint.magnetic_bearing == 90.0
        assert waypoint.distance_nm == 10.0


class TestWaypointResult:
    """Tests for the WaypointResult class."""

    def test_waypoint_result_creation(self):
        """Test creating waypoint result."""
        coords = Coordinates(latitude=37.6213, longitude=-122.3790)
        result = WaypointResult(
            coordinates=coords,
            radius_letter="D",
            airport_code="KSFO",
            operation_code="A",
            vor_identifier="SFO",
            magnetic_bearing=90.0,
            distance_nm=10.0,
        )
        assert result.radius_letter == "D"
        assert result.airport_code == "KSFO"


class TestFixInput:
    """Tests for the FixInput class."""

    def test_fix_input_creation(self):
        """Test creating fix input."""
        coords = Coordinates(latitude=37.6213, longitude=-122.3790)
        fix_input = FixInput(
            coordinates=coords,
            identifier="FIX01",
            fix_type="VOR",
            fix_usage="BOTH",
            runway_code="RW28R",
            airport_code="KSFO",
        )
        assert fix_input.identifier == "FIX01"
        assert fix_input.fix_type == "VOR"


class TestFixResult:
    """Tests for the FixResult class."""

    def test_fix_result_creation(self):
        """Test creating fix result."""
        coords = Coordinates(latitude=37.6213, longitude=-122.3790)
        result = FixResult(
            coordinates=coords,
            fix_code="V",
            usage_code="B",
            runway_code="28R",
            airport_code="KSFO",
            operation_code="A",
        )
        assert result.fix_code == "V"
        assert result.usage_code == "B"


class TestNavAidEntry:
    """Tests for the NavAidEntry class."""

    def test_navaid_entry_creation(self):
        """Test creating navaid entry."""
        navaid = NavAidEntry(
            type_code="VOR",
            latitude=37.6213,
            longitude=-122.3790,
            identifier="SFO",
            name="San Francisco",
        )
        assert navaid.type_code == "VOR"
        assert navaid.identifier == "SFO"
        assert navaid.name == "San Francisco"

    def test_navaid_display_name_with_name(self):
        """Test display name when name is provided."""
        navaid = NavAidEntry(
            type_code="VOR",
            latitude=37.6213,
            longitude=-122.3790,
            identifier="SFO",
            name="San Francisco",
        )
        assert navaid.display_name == "SFO - San Francisco"

    def test_navaid_display_name_without_name(self):
        """Test display name when name is not provided."""
        navaid = NavAidEntry(
            type_code="VOR", latitude=37.6213, longitude=-122.3790, identifier="SFO"
        )
        assert navaid.display_name == "SFO"
