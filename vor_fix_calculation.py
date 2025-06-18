import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from geographiclib.geodesic import Geodesic
import math
import os
import datetime
import importlib.util
from typing import Optional, Tuple, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

# Constants for the Earth's ellipsoid model with maximum precision settings
GEODESIC = Geodesic.WGS84

# Ultra high precision settings for intersection calculations
MAX_ITERATIONS = 200  # Increased max iterations for better convergence with tight tolerance
DISTANCE_TOLERANCE_NM = 0.00000054  # About 1 meter in nautical miles (1/1852)
DISTANCE_TOLERANCE_M = 1.0  # Tolerance in meters (1-meter precision)
ANGLE_TOLERANCE_DEG = 0.0001  # Extremely precise angular tolerance (about 0.36 arcseconds)

# Meters per nautical mile, defined exactly (constant should never be modified)
METERS_PER_NM = 1852.0

def _validate_constants():
    """Validate critical constants to prevent division by zero errors."""
    if METERS_PER_NM <= 0:
        raise ValueError("METERS_PER_NM constant must be positive")

# Validate constants on import
_validate_constants()

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
    WAYPOINT = "WAYPOINT"
    FIX = "FIX"

class FileType(Enum):
    NAV = "NAV"
    FIX = "FIX"

class BearingMode(Enum):
    MAGNETIC = "Magnetic"
    TRUE = "True"

class DeclinationMode(Enum):
    AUTO = "Auto"
    MANUAL = "Manual"

@dataclass
class Coordinates:
    """Represents geographic coordinates with validation."""
    lat: float
    lon: float
    
    def __post_init__(self):
        if not (-90 <= self.lat <= 90):
            raise ValueError(f"Latitude {self.lat} out of range (±90)")
        if not (-180 < self.lon <= 180):
            raise ValueError(f"Longitude {self.lon} out of range (-180, 180]")
    
    def __str__(self) -> str:
        return f"{self.lat:.9f} {self.lon:.9f}"

@dataclass
class CalculationResult:
    """Represents the result of a coordinate calculation."""
    coordinates: Coordinates
    output_string: str
    timestamp: str
    mode: AppMode

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
    
    def get_declination(self, coordinates: Coordinates) -> float:
        """Calculate magnetic declination at the given coordinates."""
        if not (self.pygeomag_available and self.geomag_initialized):
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
            return result.d
        except Exception:
            return 0.0

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
        """Calculate target coordinates with ultra-high precision."""
        distance_m = CoordinateCalculator.nm_to_meters(distance_nm)
        
        result = GEODESIC.Direct(start_coords.lat, start_coords.lon, azimuth, distance_m)
        
        # Verify the calculation
        verification = GEODESIC.Inverse(
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
                    step_result = GEODESIC.Direct(
                        step_coords.lat, step_coords.lon, azimuth, step_distance
                    )
                    step_coords = Coordinates(step_result['lat2'], step_result['lon2'])
                return step_coords
        
        return Coordinates(result['lat2'], result['lon2'])

    @staticmethod
    def get_radius_letter(distance_nm: float) -> str:
        """Get the single-letter radius designator."""
        ranges = [
            (0.1, 1.5, 'A'), (1.5, 2.5, 'B'), (2.5, 3.5, 'C'), (3.5, 4.5, 'D'),
            (4.5, 5.5, 'E'), (5.5, 6.5, 'F'), (6.5, 7.5, 'G'), (7.5, 8.5, 'H'),
            (8.5, 9.5, 'I'), (9.5, 10.5, 'J'), (10.5, 11.5, 'K'), (11.5, 12.5, 'L'),
            (12.5, 13.5, 'M'), (13.5, 14.5, 'N'), (14.5, 15.5, 'O'), (15.5, 16.5, 'P'),
            (16.5, 17.5, 'Q'), (17.5, 18.5, 'R'), (18.5, 19.5, 'S'), (19.5, 20.5, 'T'),
            (20.5, 21.5, 'U'), (21.5, 22.5, 'V'), (22.5, 23.5, 'W'), (23.5, 24.5, 'X'),
            (24.5, 25.5, 'Y'), (25.5, 26.5, 'Z')
        ]
        for low, high, letter in ranges:
            if low <= distance_nm < high:
                return letter
        # Handle edge cases
        if distance_nm < 0.1:
            return 'A'
        return 'Z'

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
    
    @staticmethod
    def validate_distance(distance_str: str) -> float:
        """Validate distance input."""
        try:
            distance = float(distance_str)
            if distance <= 0:
                raise ValueError("Distance should be greater than 0 nautical miles")
            return distance
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError("Distance must be a number")
            raise e
    
    @staticmethod
    def validate_airport_code(airport_code: str) -> str:
        """Validate airport code."""
        code = airport_code.strip().upper()
        if len(code) != 4:
            raise ValueError("Airport code must be 4 letters")
        if not code.isalpha():
            raise ValueError("Airport code must contain only letters")
        return code
    
    @staticmethod
    def validate_vor_identifier(vor_id: str) -> str:
        """Validate VOR identifier."""
        if not vor_id:
            return vor_id
        
        code = vor_id.strip().upper()
        if not (1 <= len(code) <= 3 and code.isalpha()):
            raise ValueError("VOR identifier should be 1-3 letters and alphabetic")
        return code
    
    @staticmethod
    def validate_runway_code(runway_str: str) -> int:
        """Validate runway code."""
        try:
            runway = int(runway_str)
            if not (0 <= runway <= 99):
                raise ValueError("Runway code should be between 0 and 99")
            return runway
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Runway code must be a number")
            raise e

class FileSelectionFrame:
    """Frame for file selection UI."""
    
    def __init__(self, parent, nav_data_service: NavigationDataService):
        self.nav_data_service = nav_data_service
        self.frame = tk.LabelFrame(
            parent, 
            text="File Selection", 
            padx=10, 
            pady=5, 
            borderwidth=2, 
            relief=tk.GROOVE
        )
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the file selection widgets."""
        # Configure grid columns
        self.frame.columnconfigure(1, weight=1)
        
        # FIX File Selection
        tk.Label(self.frame, text="FIX File:", width=8, anchor="w").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.entry_fix_file = tk.Entry(self.frame, width=40)
        self.entry_fix_file.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        btn_browse_fix = tk.Button(
            self.frame, 
            text="Browse", 
            command=lambda: self._browse_file(FileType.FIX)
        )
        btn_browse_fix.grid(row=0, column=2, padx=5, pady=2)

        # NAV File Selection
        tk.Label(self.frame, text="NAV File:", width=8, anchor="w").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.entry_nav_file = tk.Entry(self.frame, width=40)
        self.entry_nav_file.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        btn_browse_nav = tk.Button(
            self.frame, 
            text="Browse", 
            command=lambda: self._browse_file(FileType.NAV)
        )
        btn_browse_nav.grid(row=1, column=2, padx=5, pady=2)
    
    def _browse_file(self, file_type: FileType):
        """Browse for a file of the specified type."""
        filepath = filedialog.askopenfilename(
            title=f"Select {file_type.value} File",
            filetypes=[(f"{file_type.value} files", "*.dat"), ("All files", "*.*")]
        )
        
        if filepath:
            self.nav_data_service.set_file_path(file_type, filepath)
            
            if file_type == FileType.FIX:
                self.entry_fix_file.delete(0, tk.END)
                self.entry_fix_file.insert(0, filepath)
            else:
                self.entry_nav_file.delete(0, tk.END)
                self.entry_nav_file.insert(0, filepath)
    
    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)

class BaseCalculationFrame:
    """Base class for calculation frames with common functionality."""
    
    def __init__(
        self, 
        parent, 
        nav_data_service: NavigationDataService,
        declination_service: MagneticDeclinationService
    ):
        self.nav_data_service = nav_data_service
        self.declination_service = declination_service
        self.frame = tk.Frame(parent)
        self.search_file_type = tk.StringVar()
        self.bearing_mode = tk.StringVar(value=BearingMode.MAGNETIC.value)
        self.declination_mode = tk.StringVar(value=DeclinationMode.MANUAL.value)
        self.auto_declination_value = 0.0
    
    def _create_bearing_mode_widgets(self, row: int):
        """Create bearing mode selection widgets."""
        tk.Label(self.frame, text="Bearing Mode:", anchor="e").grid(
            row=row, column=0, padx=5, pady=5, sticky="e"
        )
        
        bearing_frame = tk.Frame(self.frame)
        bearing_frame.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Radiobutton(
            bearing_frame, 
            text="Magnetic", 
            variable=self.bearing_mode,
            value=BearingMode.MAGNETIC.value, 
            command=self._update_bearing_label
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            bearing_frame, 
            text="True", 
            variable=self.bearing_mode,
            value=BearingMode.TRUE.value, 
            command=self._update_bearing_label
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_declination_widgets(self, row: int):
        """Create declination mode widgets."""
        self.declination_frame = tk.Frame(self.frame)
        self.declination_frame.grid(
            row=row, column=0, columnspan=2, pady=5, sticky="w"
        )
        
        tk.Label(self.declination_frame, text="Declination Mode:").pack(
            side=tk.LEFT, padx=5
        )
        
        tk.Radiobutton(
            self.declination_frame, 
            text="Auto", 
            variable=self.declination_mode,
            value=DeclinationMode.AUTO.value, 
            command=self._update_bearing_label
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            self.declination_frame, 
            text="Manual", 
            variable=self.declination_mode,
            value=DeclinationMode.MANUAL.value, 
            command=self._update_bearing_label
        ).pack(side=tk.LEFT, padx=5)
        
        self.auto_declination_label = tk.Label(
            self.declination_frame, text="Auto: 0.0°"
        )
        self.auto_declination_label.pack(side=tk.LEFT, padx=5)
    
    def _update_bearing_label(self):
        """Update bearing label based on selected mode - to be implemented by subclasses."""
        pass
    
    def _get_effective_declination(self, coordinates: Optional[Coordinates] = None) -> float:
        """Get the effective declination based on mode and coordinates."""
        if self.bearing_mode.get() != BearingMode.MAGNETIC.value:
            return 0.0
        
        if self.declination_mode.get() == DeclinationMode.AUTO.value:
            if coordinates:
                declination = self.declination_service.get_declination(coordinates)
                self.auto_declination_value = declination
                self.auto_declination_label.config(text=f"Auto: {declination:.1f}°")
                return declination
            return self.auto_declination_value
        else:
            try:
                return float(self.entry_declination.get())
            except ValueError:
                return 0.0
    
    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)
    
    def pack_forget(self):
        """Hide the frame."""
        self.frame.pack_forget()

class WaypointCalculationFrame(BaseCalculationFrame):
    """Frame for waypoint calculations."""
    
    def __init__(
        self, 
        parent, 
        nav_data_service: NavigationDataService,
        declination_service: MagneticDeclinationService,
        calculator: CoordinateCalculator,
        on_calculate_callback
    ):
        super().__init__(parent, nav_data_service, declination_service)
        self.calculator = calculator
        self.on_calculate_callback = on_calculate_callback
        self.search_file_type.set(FileType.NAV.value)
        self._create_widgets()
    
    def _create_widgets(self):
        """Create waypoint calculation widgets."""
        self.frame.columnconfigure(1, weight=1)
        
        # File type selection
        tk.Label(self.frame, text="Search in File Type:", anchor="e").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        combo_search_file = ttk.Combobox(
            self.frame, 
            textvariable=self.search_file_type,
            values=[FileType.NAV.value, FileType.FIX.value], 
            state="readonly"
        )
        combo_search_file.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Identifier entry
        tk.Label(self.frame, text="VOR/DME/NDB Identifier:", anchor="e").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_identifier = tk.Entry(self.frame, width=30)
        self.entry_identifier.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Coordinates entry
        tk.Label(self.frame, text="Coordinates (Lat Lon):", anchor="e").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_coords = tk.Entry(self.frame, width=30)
        self.entry_coords.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Bearing mode widgets
        self._create_bearing_mode_widgets(3)
        
        # Bearing entry
        self.bearing_label = tk.StringVar(value="Magnetic Bearing (°):")
        tk.Label(self.frame, textvariable=self.bearing_label, anchor="e").grid(
            row=4, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_bearing = tk.Entry(self.frame, width=30)
        self.entry_bearing.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        # Distance entry
        tk.Label(self.frame, text="Distance (NM):", anchor="e").grid(
            row=5, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_distance = tk.Entry(self.frame, width=30)
        self.entry_distance.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        
        # Declination widgets
        self._create_declination_widgets(6)
        
        # Manual declination entry
        self.declination_label = tk.Label(
            self.frame, text="Manual Declination (°):", anchor="e"
        )
        self.declination_label.grid(row=7, column=0, padx=5, pady=5, sticky="e")
        self.entry_declination = tk.Entry(self.frame, width=30)
        self.entry_declination.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
        self.entry_declination.insert(0, "0.0")
        
        # Airport code entry
        tk.Label(self.frame, text="Airport Code:", anchor="e").grid(
            row=8, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_airport_code = tk.Entry(self.frame, width=30)
        self.entry_airport_code.grid(row=8, column=1, padx=5, pady=5, sticky="ew")
        
        # VOR identifier entry
        tk.Label(self.frame, text="VOR Identifier:", anchor="e").grid(
            row=9, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_vor_identifier = tk.Entry(self.frame, width=30)
        self.entry_vor_identifier.grid(row=9, column=1, padx=5, pady=5, sticky="ew")
        
        # Operation type
        tk.Label(self.frame, text="Operation Type:", anchor="e").grid(
            row=10, column=0, padx=5, pady=5, sticky="e"
        )
        self.combo_operation_type = ttk.Combobox(
            self.frame,
            values=list(OPERATION_CODES.keys()),
            state="readonly"
        )
        self.combo_operation_type.current(0)
        self.combo_operation_type.grid(row=10, column=1, padx=5, pady=5, sticky="ew")
        
        # Buttons
        btn_calc = tk.Button(
            self.frame, 
            text="Calculate Waypoint", 
            command=self.calculate
        )
        btn_calc.grid(row=11, column=0, columnspan=2, pady=5)
        
        btn_search = tk.Button(
            self.frame, 
            text="Search Coordinates", 
            command=self.search_coordinates
        )
        btn_search.grid(row=1, column=2, padx=5, pady=5)
        
        btn_update_decl = tk.Button(
            self.frame, 
            text="Update Declination", 
            command=self.update_declination
        )
        btn_update_decl.grid(row=2, column=2, padx=5, pady=5)
        
        self._update_bearing_label()
    
    def _update_bearing_label(self):
        """Update bearing label based on selected mode."""
        bearing_mode = BearingMode(self.bearing_mode.get())
        declination_mode = DeclinationMode(self.declination_mode.get())
        
        if bearing_mode == BearingMode.MAGNETIC:
            self.bearing_label.set("Magnetic Bearing (°):")
            self.declination_frame.grid()
            
            if declination_mode == DeclinationMode.MANUAL:
                self.declination_label.grid()
                self.entry_declination.grid()
            else:
                self.declination_label.grid_remove()
                self.entry_declination.grid_remove()
        else:
            self.bearing_label.set("True Bearing (°):")
            self.declination_frame.grid_remove()
            self.declination_label.grid_remove()
            self.entry_declination.grid_remove()
    
    def search_coordinates(self):
        """Search for coordinates based on identifier."""
        identifier = self.entry_identifier.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter an identifier.")
            return
        
        try:
            file_type = FileType(self.search_file_type.get())
            matching_lines = self.nav_data_service.search_identifier(identifier, file_type)
            
            if not matching_lines:
                messagebox.showinfo(
                    "Not Found", 
                    f"{file_type.value} identifier '{identifier}' not found."
                )
                return
            
            if len(matching_lines) > 1:
                self._handle_duplicate_entries(matching_lines)
            else:
                self._set_coordinates(matching_lines[0])
                
        except Exception as e:
            messagebox.showerror("Search Error", str(e))
    
    def _handle_duplicate_entries(self, matching_lines: List[List[str]]):
        """Handle multiple entries with the same identifier."""
        choice_window = tk.Toplevel(self.frame)
        choice_window.title("Choose Entry")
        tk.Label(choice_window, text="Multiple entries found. Please choose one:").pack()
        
        selected_line = tk.StringVar()
        file_type = FileType(self.search_file_type.get())
        
        for line_parts in matching_lines:
            first_part = line_parts[0]
            type_str = NAV_TYPE_DESCRIPTIONS.get(first_part, "Unknown")
            relevant_index = 7 if file_type == FileType.NAV else 2
            display_text = f"{type_str} - {line_parts[relevant_index]}"
            
            if len(line_parts) > 9:
                display_text += f" - {line_parts[9]}"
            else:
                display_text += " - [Location missing]"
            
            rb = tk.Radiobutton(
                choice_window,
                text=display_text,
                variable=selected_line,
                value=",".join(line_parts)
            )
            rb.pack()
        
        def confirm_choice():
            chosen_line = selected_line.get()
            if chosen_line:
                self._set_coordinates(chosen_line.split(","))
                choice_window.destroy()
            else:
                messagebox.showwarning("Selection Required", "Please select an entry.")
        
        btn_confirm = tk.Button(choice_window, text="Confirm", command=confirm_choice)
        btn_confirm.pack()
        choice_window.wait_window()
    
    def _set_coordinates(self, line_parts: List[str]):
        """Set coordinates from search results."""
        try:
            file_type = FileType(self.search_file_type.get())
            lat_index = 1 if file_type == FileType.NAV else 0
            lon_index = 2 if file_type == FileType.NAV else 1
            
            # Check if we have enough data
            if len(line_parts) <= max(lat_index, lon_index):
                raise IndexError("Insufficient coordinate data in file entry")
            
            coordinates = Coordinates(float(line_parts[lat_index]), float(line_parts[lon_index]))
            self.entry_coords.delete(0, tk.END)
            self.entry_coords.insert(0, str(coordinates))
            
        except (ValueError, IndexError) as e:
            messagebox.showerror("Data Error", f"Invalid coordinate data in the selected file: {str(e)}")
    
    def update_declination(self):
        """Update auto declination from coordinates."""
        try:
            coords_str = self.entry_coords.get().strip()
            if not coords_str:
                messagebox.showwarning(
                    "Auto Declination", 
                    "Please enter or search for coordinates first."
                )
                return
            
            coordinates = InputValidator.validate_coordinates(coords_str)
            declination = self.declination_service.get_declination(coordinates)
            
            self.auto_declination_value = declination
            self.auto_declination_label.config(text=f"Auto: {declination:.1f}°")
            
            if self.declination_mode.get() == DeclinationMode.AUTO.value:
                messagebox.showinfo(
                    "Auto Declination",
                    f"Magnetic declination at {coordinates.lat:.4f}, {coordinates.lon:.4f} "
                    f"is {declination:.1f}°"
                )
                
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Declination Error", f"Error calculating declination: {e}")
    
    def calculate(self):
        """Perform waypoint calculation."""
        try:
            # Validate all inputs
            coords_str = self.entry_coords.get().strip()
            coordinates = None
            
            if coords_str:
                coordinates = InputValidator.validate_coordinates(coords_str)
            elif self.entry_identifier.get().strip():
                # Try to search for coordinates first
                self.search_coordinates()
                coords_str = self.entry_coords.get().strip()
                if coords_str:
                    coordinates = InputValidator.validate_coordinates(coords_str)
                else:
                    messagebox.showerror("Input Error", "Could not find coordinates for identifier.")
                    return
            else:
                messagebox.showerror("Input Error", "Please enter identifier or coordinates.")
                return
            
            bearing = InputValidator.validate_bearing(self.entry_bearing.get())
            distance_nm = InputValidator.validate_distance(self.entry_distance.get())
            airport_code = InputValidator.validate_airport_code(self.entry_airport_code.get())
            vor_identifier = InputValidator.validate_vor_identifier(self.entry_vor_identifier.get())
            
            # Calculate effective declination
            declination = self._get_effective_declination(coordinates)
            
            # Convert to true bearing if needed
            bearing_mode = BearingMode(self.bearing_mode.get())
            if bearing_mode == BearingMode.MAGNETIC:
                true_bearing = (bearing + declination) % 360
            else:
                true_bearing = bearing % 360
            
            # Calculate target coordinates
            target_coords = self.calculator.calculate_target_coords_geodesic(
                coordinates, true_bearing, distance_nm
            )
            
            # Generate output
            radius_letter = self.calculator.get_radius_letter(distance_nm)
            operation_code = OPERATION_CODES[self.combo_operation_type.get()]
            
            if distance_nm > 26.5:
                rounded_distance_nm_int = int(round(distance_nm))
                output = (f"{target_coords} "
                         f"{vor_identifier}{rounded_distance_nm_int} "
                         f"{airport_code} {airport_code[:2]}")
                if vor_identifier:
                    bearing_int = int(bearing)
                    output += f" {operation_code} {vor_identifier}{bearing_int:03d}{rounded_distance_nm_int:03d}"
                else:
                    output += f" {operation_code}"
            else:
                output = (f"{target_coords} "
                         f"D{int(bearing):03d}{radius_letter} "
                         f"{airport_code} {airport_code[:2]}")
                if vor_identifier:
                    bearing_int = int(bearing)
                    output += f" {operation_code} {vor_identifier}{bearing_int:03d}{int(round(distance_nm)):03d}"
                else:
                    output += f" {operation_code}"
            
            # Create result
            result = CalculationResult(
                coordinates=target_coords,
                output_string=output,
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                mode=AppMode.WAYPOINT
            )
            
            self.on_calculate_callback(result)
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {e}")
    
    def clear_fields(self):
        """Clear all input fields."""
        self.entry_identifier.delete(0, tk.END)
        self.entry_coords.delete(0, tk.END)
        self.entry_bearing.delete(0, tk.END)
        self.entry_distance.delete(0, tk.END)
        self.entry_declination.delete(0, tk.END)
        self.entry_airport_code.delete(0, tk.END)
        self.entry_vor_identifier.delete(0, tk.END)

class FixCalculationFrame(BaseCalculationFrame):
    """Frame for FIX calculations."""
    
    def __init__(
        self, 
        parent, 
        nav_data_service: NavigationDataService,
        declination_service: MagneticDeclinationService,
        calculator: CoordinateCalculator,
        on_calculate_callback
    ):
        super().__init__(parent, nav_data_service, declination_service)
        self.calculator = calculator
        self.on_calculate_callback = on_calculate_callback
        self.search_file_type.set(FileType.FIX.value)
        self._create_widgets()
    
    def _create_widgets(self):
        """Create FIX calculation widgets."""
        self.frame.columnconfigure(1, weight=1)
        
        # File type selection
        tk.Label(self.frame, text="Search in File Type:", anchor="e").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        combo_search_file = ttk.Combobox(
            self.frame,
            textvariable=self.search_file_type,
            values=[FileType.FIX.value, FileType.NAV.value],
            state="readonly"
        )
        combo_search_file.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # FIX identifier entry
        tk.Label(self.frame, text="FIX Identifier:", anchor="e").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_fix_identifier = tk.Entry(self.frame, width=30)
        self.entry_fix_identifier.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # FIX coordinates entry
        tk.Label(self.frame, text="FIX Coordinates (Lat Lon):", anchor="e").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_fix_coords = tk.Entry(self.frame, width=30)
        self.entry_fix_coords.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Separator for DME section
        separator = ttk.Separator(self.frame, orient='horizontal')
        separator.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
        
        tk.Label(self.frame, text="DME Calculation", font=('Helvetica', 10, 'bold')).grid(
            row=4, column=0, columnspan=2, pady=5, sticky="w"
        )
        
        # Distance reference selector
        tk.Label(self.frame, text="Distance Reference:", anchor="e").grid(
            row=5, column=0, padx=5, pady=5, sticky="e"
        )
        self.distance_reference = tk.StringVar(value="DME")
        distance_frame = tk.Frame(self.frame)
        distance_frame.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        tk.Radiobutton(
            distance_frame, text="DME", variable=self.distance_reference, value="DME"
        ).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(
            distance_frame, text="FIX", variable=self.distance_reference, value="FIX"
        ).pack(side=tk.LEFT, padx=5)
        
        # DME identifier and coordinates
        tk.Label(self.frame, text="DME Identifier:", anchor="e").grid(
            row=6, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_dme_identifier = tk.Entry(self.frame, width=30)
        self.entry_dme_identifier.grid(row=6, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(self.frame, text="DME Coordinates (Lat Lon):", anchor="e").grid(
            row=7, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_dme_coords = tk.Entry(self.frame, width=30)
        self.entry_dme_coords.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
        
        # DME bearing mode
        self._create_bearing_mode_widgets(8)
        
        # DME bearing and distance
        self.dme_bearing_label = tk.StringVar(value="Magnetic Bearing (°):")
        tk.Label(self.frame, textvariable=self.dme_bearing_label, anchor="e").grid(
            row=9, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_dme_bearing = tk.Entry(self.frame, width=30)
        self.entry_dme_bearing.grid(row=9, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(self.frame, text="Distance (NM):", anchor="e").grid(
            row=10, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_dme_distance = tk.Entry(self.frame, width=30)
        self.entry_dme_distance.grid(row=10, column=1, padx=5, pady=5, sticky="ew")
        
        # DME declination widgets
        self._create_declination_widgets(11)
        
        # Manual declination entry
        self.dme_declination_label = tk.Label(
            self.frame, text="Manual Declination (°):", anchor="e"
        )
        self.dme_declination_label.grid(row=12, column=0, padx=5, pady=5, sticky="e")
        self.entry_dme_declination = tk.Entry(self.frame, width=30)
        self.entry_dme_declination.grid(row=12, column=1, padx=5, pady=5, sticky="ew")
        self.entry_dme_declination.insert(0, "0.0")
        
        # Buttons for DME section
        btn_search_dme = tk.Button(
            self.frame, text="Search DME", command=self.search_dme_coords
        )
        btn_search_dme.grid(row=6, column=2, padx=5, pady=5)
        
        btn_update_dme_decl = tk.Button(
            self.frame, text="Update Declination", command=self.update_dme_declination
        )
        btn_update_dme_decl.grid(row=7, column=2, padx=5, pady=5)
        
        btn_calc_from_dme = tk.Button(
            self.frame, text="Calculate Intersection", command=self.calculate_from_dme
        )
        btn_calc_from_dme.grid(row=13, column=0, columnspan=2, pady=5)
        
        # Second separator
        separator2 = ttk.Separator(self.frame, orient='horizontal')
        separator2.grid(row=14, column=0, columnspan=3, sticky="ew", pady=10)
        
        # FIX details
        tk.Label(self.frame, text="FIX Type:", anchor="e").grid(
            row=15, column=0, padx=5, pady=5, sticky="e"
        )
        self.combo_fix_type = ttk.Combobox(
            self.frame,
            values=list(FIX_TYPE_CODES.keys()),
            state="readonly"
        )
        self.combo_fix_type.current(0)
        self.combo_fix_type.grid(row=15, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(self.frame, text="FIX Usage:", anchor="e").grid(
            row=16, column=0, padx=5, pady=5, sticky="e"
        )
        self.combo_fix_usage = ttk.Combobox(
            self.frame,
            values=list(FIX_USAGE_CODES.keys()),
            state="readonly"
        )
        self.combo_fix_usage.current(0)
        self.combo_fix_usage.grid(row=16, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(self.frame, text="Runway Code:", anchor="e").grid(
            row=17, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_runway_code = tk.Entry(self.frame, width=30)
        self.entry_runway_code.grid(row=17, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(self.frame, text="Airport Code:", anchor="e").grid(
            row=18, column=0, padx=5, pady=5, sticky="e"
        )
        self.entry_fix_airport_code = tk.Entry(self.frame, width=30)
        self.entry_fix_airport_code.grid(row=18, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(self.frame, text="Operation Type:", anchor="e").grid(
            row=19, column=0, padx=5, pady=5, sticky="e"
        )
        self.combo_fix_operation_type = ttk.Combobox(
            self.frame,
            values=list(OPERATION_CODES.keys()),
            state="readonly"
        )
        self.combo_fix_operation_type.current(0)
        self.combo_fix_operation_type.grid(row=19, column=1, padx=5, pady=5, sticky="ew")
        
        # Main calculation button
        btn_calc = tk.Button(
            self.frame, text="Calculate FIX", command=self.calculate_fix
        )
        btn_calc.grid(row=20, column=0, columnspan=2, pady=5)
        
        # Search button for FIX coordinates
        btn_search_fix = tk.Button(
            self.frame, text="Search Coordinates", command=self.search_fix_coords
        )
        btn_search_fix.grid(row=1, column=2, padx=5, pady=5)
        
        self._update_bearing_label()
    
    def _update_bearing_label(self):
        """Update DME bearing label based on selected mode."""
        bearing_mode = BearingMode(self.bearing_mode.get())
        declination_mode = DeclinationMode(self.declination_mode.get())
        
        if bearing_mode == BearingMode.MAGNETIC:
            self.dme_bearing_label.set("Magnetic Bearing (°):")
            self.declination_frame.grid()
            
            if declination_mode == DeclinationMode.MANUAL:
                self.dme_declination_label.grid()
                self.entry_dme_declination.grid()
            else:  # Auto
                self.dme_declination_label.grid_remove()
                self.entry_dme_declination.grid_remove()
        else:  # True
            self.dme_bearing_label.set("True Bearing (°):")
            self.declination_frame.grid_remove()
            self.dme_declination_label.grid_remove()
            self.entry_dme_declination.grid_remove()
    
    def search_fix_coords(self):
        """Search for FIX coordinates."""
        identifier = self.entry_fix_identifier.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter a FIX identifier.")
            return
        
        try:
            file_type = FileType(self.search_file_type.get())
            matching_lines = self.nav_data_service.search_identifier(identifier, file_type)
            
            if not matching_lines:
                messagebox.showinfo(
                    "Not Found",
                    f"{file_type.value} identifier '{identifier}' not found."
                )
                return
            
            if len(matching_lines) > 1:
                self._handle_duplicate_entries(matching_lines, self._set_fix_coords)
            else:
                self._set_fix_coords(matching_lines[0])
                
        except Exception as e:
            messagebox.showerror("Search Error", str(e))
    
    def search_dme_coords(self):
        """Search for DME coordinates."""
        identifier = self.entry_dme_identifier.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter a DME identifier.")
            return
        
        try:
            matching_lines = self.nav_data_service.search_identifier(identifier, FileType.NAV)
            
            # Filter for DME types
            dme_lines = [
                line for line in matching_lines 
                if len(line) > 0 and line[0] in ['12', '13']
            ]
            
            if not dme_lines:
                messagebox.showinfo("Not Found", f"DME identifier '{identifier}' not found.")
                return
            
            if len(dme_lines) > 1:
                self._handle_duplicate_entries(dme_lines, self._set_dme_coords)
            else:
                self._set_dme_coords(dme_lines[0])
                
        except Exception as e:
            messagebox.showerror("Search Error", str(e))
    
    def _handle_duplicate_entries(self, matching_lines: List[List[str]], callback):
        """Handle multiple entries with same identifier."""
        choice_window = tk.Toplevel(self.frame)
        choice_window.title("Choose Entry")
        tk.Label(choice_window, text="Multiple entries found. Please choose one:").pack()
        
        selected_line = tk.StringVar()
        
        for line_parts in matching_lines:
            first_part = line_parts[0]
            type_str = NAV_TYPE_DESCRIPTIONS.get(first_part, "Unknown")
            relevant_index = 7
            display_text = f"{type_str} - {line_parts[relevant_index]}"
            
            if len(line_parts) > 9:
                display_text += f" - {line_parts[9]}"
            else:
                display_text += " - [Location missing]"
            
            rb = tk.Radiobutton(
                choice_window,
                text=display_text,
                variable=selected_line,
                value=",".join(line_parts)
            )
            rb.pack()
        
        def confirm_choice():
            chosen_line = selected_line.get()
            if chosen_line:
                callback(chosen_line.split(","))
                choice_window.destroy()
            else:
                messagebox.showwarning("Selection Required", "Please select an entry.")
        
        btn_confirm = tk.Button(choice_window, text="Confirm", command=confirm_choice)
        btn_confirm.pack()
        choice_window.wait_window()
    
    def _set_fix_coords(self, line_parts: List[str]):
        """Set FIX coordinates from search results."""
        try:
            file_type = FileType(self.search_file_type.get())
            lat_index = 0 if file_type == FileType.FIX else 1
            lon_index = 1 if file_type == FileType.FIX else 2
            
            # Check if we have enough data
            if len(line_parts) <= max(lat_index, lon_index):
                raise IndexError("Insufficient coordinate data in file entry")
            
            coordinates = Coordinates(float(line_parts[lat_index]), float(line_parts[lon_index]))
            self.entry_fix_coords.delete(0, tk.END)
            self.entry_fix_coords.insert(0, str(coordinates))
            
        except (ValueError, IndexError) as e:
            messagebox.showerror("Data Error", f"Invalid coordinate data in the selected file: {str(e)}")
    
    def _set_dme_coords(self, line_parts: List[str]):
        """Set DME coordinates from search results."""
        try:
            # Check if we have enough data (need at least 3 elements for indices 1 and 2)
            if len(line_parts) < 3:
                raise IndexError("Insufficient coordinate data in DME entry")
            
            coordinates = Coordinates(float(line_parts[1]), float(line_parts[2]))
            self.entry_dme_coords.delete(0, tk.END)
            self.entry_dme_coords.insert(0, str(coordinates))
        except (ValueError, IndexError) as e:
            messagebox.showerror("Data Error", f"Invalid coordinate data in the selected DME: {str(e)}")
    
    def update_dme_declination(self):
        """Update auto declination from DME coordinates."""
        try:
            coords_str = self.entry_dme_coords.get().strip()
            if not coords_str:
                messagebox.showwarning(
                    "Auto Declination",
                    "Please enter or search for DME coordinates first."
                )
                return
            
            coordinates = InputValidator.validate_coordinates(coords_str)
            declination = self.declination_service.get_declination(coordinates)
            
            self.auto_declination_value = declination
            self.auto_declination_label.config(text=f"Auto: {declination:.1f}°")
            
            if self.declination_mode.get() == DeclinationMode.AUTO.value:
                messagebox.showinfo(
                    "Auto Declination",
                    f"Magnetic declination at {coordinates.lat:.4f}, {coordinates.lon:.4f} "
                    f"is {declination:.1f}°"
                )
                
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Declination Error", f"Error calculating declination: {e}")
    
    def calculate_from_dme(self):
        """Calculate intersection from DME data."""
        try:
            # Get and validate FIX coordinates
            fix_coords = InputValidator.validate_coordinates(self.entry_fix_coords.get())
            
            # Get and validate DME coordinates
            dme_coords = InputValidator.validate_coordinates(self.entry_dme_coords.get())
            
            # Get and validate bearing and distance
            bearing = InputValidator.validate_bearing(self.entry_dme_bearing.get())
            distance_nm = InputValidator.validate_distance(self.entry_dme_distance.get())
            
            # Calculate effective declination
            declination = self._get_effective_declination(dme_coords)
            
            # Convert to true bearing
            bearing_mode = BearingMode(self.bearing_mode.get())
            if bearing_mode == BearingMode.MAGNETIC:
                true_bearing = (bearing + declination) % 360
            else:
                true_bearing = bearing % 360
            
            distance_reference = self.distance_reference.get()
            start_time = datetime.datetime.now()
            
            if distance_reference == "DME":
                # Find intersection of radial from FIX with circle around DME
                intersection_point = self._find_radial_distance_intersection(
                    fix_coords, true_bearing, dme_coords, distance_nm
                )
                
                # Verify accuracy
                verification = GEODESIC.Inverse(
                    intersection_point.lat, intersection_point.lon,
                    dme_coords.lat, dme_coords.lon
                )
                actual_distance_nm = verification['s12'] / 1852
                accuracy_error_nm = abs(actual_distance_nm - distance_nm)
            else:
                # Calculate directly from FIX
                try:
                    intersection_point = self.calculator.calculate_target_coords_geodesic(
                        fix_coords, true_bearing, distance_nm
                    )
                    accuracy_error_nm = 0
                except Exception as e:
                    raise Exception(f"Error calculating coordinates from FIX: {str(e)}")
            
            end_time = datetime.datetime.now()
            elapsed_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update FIX coordinates with intersection point
            self.entry_fix_coords.delete(0, tk.END)
            self.entry_fix_coords.insert(0, str(intersection_point))
            
            bearing_type = "magnetic" if bearing_mode == BearingMode.MAGNETIC else "true"
            declination_info = f" (declination: {declination:.1f}°)" if bearing_mode == BearingMode.MAGNETIC else ""
            
            if distance_reference == "DME":
                message = (f"Intersection found: FIX {bearing_type} radial {bearing:.2f}°{declination_info} "
                          f"intersects with {distance_nm:.3f} NM from DME.\n"
                          f"Precision: Distance error {accuracy_error_nm:.6f} NM")
            else:
                message = f"Point calculated at {bearing_type} bearing {bearing:.2f}°{declination_info} and {distance_nm:.3f} NM from FIX."
            
            messagebox.showinfo(
                "Calculation Complete",
                f"{message}\n"
                f"Coordinates have been set in the FIX field.\n"
                f"Calculation time: {elapsed_ms:.2f} ms"
            )
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {e}")
    
    def _find_radial_distance_intersection(
        self, 
        fix_coords: Coordinates, 
        true_bearing: float, 
        dme_coords: Coordinates, 
        distance_nm: float
    ) -> Coordinates:
        """Find intersection of radial from FIX with distance circle from DME."""
        distance_m = self.calculator.nm_to_meters(distance_nm)
        
        # Calculate distance between FIX and DME
        fix_dme_result = GEODESIC.Inverse(fix_coords.lat, fix_coords.lon, dme_coords.lat, dme_coords.lon)
        fix_dme_distance_nm = self.calculator.meters_to_nm(fix_dme_result['s12'])
        
        # Determine search range
        if distance_nm < 0.05:
            min_dist, max_dist = 0.0, 0.2
        elif distance_nm < 0.5:
            min_dist, max_dist = 0.0, max(1.0, distance_nm * 2)
        else:
            min_dist = max(0.0, fix_dme_distance_nm - distance_nm - 1)
            max_dist = fix_dme_distance_nm + distance_nm + 1
        
        # Validate search range
        if min_dist >= max_dist:
            # If search range is invalid, use a default range
            min_dist = 0.0
            max_dist = max(1.0, distance_nm * 2)
        
        # Binary search for intersection
        best_approx_distance = float('inf')
        # Initialize with a reasonable starting point based on fix coordinates
        try:
            best_approx_point = Coordinates(fix_coords.lat, fix_coords.lon)
        except ValueError:
            # Fallback to center coordinates if fix_coords is invalid
            best_approx_point = Coordinates(0, 0)
        
        for iteration in range(MAX_ITERATIONS):
            test_dist = (min_dist + max_dist) / 2.0
            test_point_result = GEODESIC.Direct(
                fix_coords.lat, fix_coords.lon, true_bearing, 
                self.calculator.nm_to_meters(test_dist)
            )
            test_point = Coordinates(test_point_result['lat2'], test_point_result['lon2'])
            
            # Calculate distance from test point to DME
            test_to_dme = GEODESIC.Inverse(test_point.lat, test_point.lon, dme_coords.lat, dme_coords.lon)
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
    
    def calculate_fix(self):
        """Calculate FIX output."""
        try:
            coordinates = InputValidator.validate_coordinates(self.entry_fix_coords.get())
            runway_code = InputValidator.validate_runway_code(self.entry_runway_code.get())
            airport_code = InputValidator.validate_airport_code(self.entry_fix_airport_code.get())
            
            fix_type = self.combo_fix_type.get()
            fix_usage = self.combo_fix_usage.get()
            
            fix_code = FIX_TYPE_CODES[fix_type]
            usage_code = FIX_USAGE_CODES[fix_usage]
            operation_code = OPERATION_CODES[self.combo_fix_operation_type.get()]
            
            output = (f"{coordinates} {usage_code}{fix_code}{runway_code:02d} "
                     f"{airport_code} {airport_code[:2]} {operation_code}")
            
            result = CalculationResult(
                coordinates=coordinates,
                output_string=output,
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                mode=AppMode.FIX
            )
            
            self.on_calculate_callback(result)
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {e}")
    
    def clear_fields(self):
        """Clear all input fields."""
        self.entry_fix_identifier.delete(0, tk.END)
        self.entry_fix_coords.delete(0, tk.END)
        self.entry_dme_identifier.delete(0, tk.END)
        self.entry_dme_coords.delete(0, tk.END)
        self.entry_dme_bearing.delete(0, tk.END)
        self.entry_dme_distance.delete(0, tk.END)
        self.entry_dme_declination.delete(0, tk.END)
        self.entry_runway_code.delete(0, tk.END)
        self.entry_fix_airport_code.delete(0, tk.END)

class CoordinateCalculatorApp:
    """Main application class for the coordinate calculator."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("VOR FIX Coordinate Calculator")
        self.root.geometry("800x700")
        
        # Initialize services
        self.nav_data_service = NavigationDataService()
        self.declination_service = MagneticDeclinationService()
        self.calculator = CoordinateCalculator()
        
        # Initialize state
        self.mode_var = tk.StringVar(value=AppMode.WAYPOINT.value)
        self.history: List[CalculationResult] = []
        
        # Create UI components
        self._create_ui()
        
    def _create_ui(self):
        """Create the main user interface."""
        # Mode selection
        self._create_mode_selection()
        
        # File selection
        self.file_selection_frame = FileSelectionFrame(
            self.root, self.nav_data_service
        )
        self.file_selection_frame.pack(padx=10, pady=5, fill="x")
        
        # Input frame container
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=5, fill="x")
        
        # Calculation frames
        self.waypoint_frame = WaypointCalculationFrame(
            self.input_frame, 
            self.nav_data_service,
            self.declination_service,
            self.calculator,
            self._on_calculation_complete
        )
        
        self.fix_frame = FixCalculationFrame(
            self.input_frame,
            self.nav_data_service, 
            self.declination_service,
            self.calculator,
            self._on_calculation_complete
        )
        
        # Output area
        self._create_output_area()
        
        # Bottom buttons
        self._create_bottom_buttons()
        
        # Initial mode setup
        self._on_mode_change()
        
    def _create_mode_selection(self):
        """Create the mode selection frame."""
        frm_mode = tk.LabelFrame(self.root, text="Mode Selection", padx=10, pady=5)
        frm_mode.pack(padx=10, pady=5, fill="x")
        
        tk.Label(frm_mode, text="Select Mode:").pack(side=tk.LEFT, padx=5)
        combo_mode = ttk.Combobox(
            frm_mode, 
            textvariable=self.mode_var,
            values=[mode.value for mode in AppMode], 
            state="readonly"
        )
        combo_mode.pack(side=tk.LEFT, padx=5)
        self.mode_var.trace_add('write', self._on_mode_change)
        
    def _create_output_area(self):
        """Create the output text area."""
        frm_output = tk.LabelFrame(self.root, text="Output Result", padx=10, pady=5)
        frm_output.pack(padx=10, pady=5, fill="both", expand=True)
        
        self.output_entry = tk.Text(frm_output, width=80, height=8, state="disabled")
        self.output_entry.pack(padx=5, pady=5, fill="both", expand=True)
        
    def _create_bottom_buttons(self):
        """Create the bottom button frame."""
        frm_btn = tk.Frame(self.root)
        frm_btn.pack(padx=10, pady=5, fill="x")
        
        # Left side buttons
        btn_clear = tk.Button(frm_btn, text="Clear Input", command=self._clear_fields)
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        btn_copy = tk.Button(frm_btn, text="Copy Result", command=self._copy_output)
        btn_copy.pack(side=tk.LEFT, padx=5)
        
        btn_history = tk.Button(frm_btn, text="View History", command=self._show_history)
        btn_history.pack(side=tk.LEFT, padx=5)
        
        # Right side button
        btn_exit = tk.Button(frm_btn, text="Exit", command=self.root.quit)
        btn_exit.pack(side=tk.RIGHT, padx=5)
        
    def _on_mode_change(self, *args):
        """Handle mode change events."""
        current_mode = AppMode(self.mode_var.get())
        
        # Hide all frames first
        self.waypoint_frame.pack_forget()
        self.fix_frame.pack_forget()
        
        # Show the appropriate frame
        if current_mode == AppMode.WAYPOINT:
            self.waypoint_frame.pack(side=tk.TOP, fill="x", pady=5)
        elif current_mode == AppMode.FIX:
            self.fix_frame.pack(side=tk.TOP, fill="x", pady=5)
            
    def _on_calculation_complete(self, result: CalculationResult):
        """Handle completion of a calculation."""
        # Add to history
        self.history.append(result)
        
        # Update output display
        self.output_entry.config(state=tk.NORMAL)
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.insert(tk.END, result.output_string)
        self.output_entry.config(state=tk.DISABLED)
        
    def _clear_fields(self):
        """Clear input fields in the current mode."""
        current_mode = AppMode(self.mode_var.get())
        
        if current_mode == AppMode.WAYPOINT:
            self.waypoint_frame.clear_fields()
        elif current_mode == AppMode.FIX:
            self.fix_frame.clear_fields()
            
        # Clear output
        self.output_entry.config(state=tk.NORMAL)
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.config(state=tk.DISABLED)
        
    def _copy_output(self):
        """Copy the output to clipboard."""
        output_text = self.output_entry.get(1.0, tk.END).strip()
        if output_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(output_text)
            messagebox.showinfo("Copy Result", "Result copied to clipboard!")
        else:
            messagebox.showwarning("Copy Result", "No text to copy!")
            
    def _show_history(self):
        """Show the calculation history window."""
        if not self.history:
            messagebox.showinfo("History", "No calculation history available.")
            return
            
        self._create_history_window()
        
    def _create_history_window(self):
        """Create and display the history window."""
        history_window = tk.Toplevel(self.root)
        history_window.title("Calculation History")
        history_window.geometry("800x500")
        
        # Create frame with scrollbar
        frame = tk.Frame(history_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create treeview for history display
        columns = ("Time", "Mode", "Output")
        history_tree = ttk.Treeview(
            frame, 
            columns=columns, 
            show="headings", 
            yscrollcommand=scrollbar.set
        )
        
        # Configure columns
        history_tree.column("Time", width=150, anchor="w")
        history_tree.column("Mode", width=80, anchor="center")
        history_tree.column("Output", width=550, anchor="w")
        
        history_tree.heading("Time", text="Time")
        history_tree.heading("Mode", text="Mode")
        history_tree.heading("Output", text="Output")
        
        # Populate with history items (newest first)
        for item in reversed(self.history):
            history_tree.insert(
                "", "end", 
                values=(item.timestamp, item.mode.value, item.output_string)
            )
        
        history_tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=history_tree.yview)
        
        # Buttons frame
        btn_frame = tk.Frame(history_window)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        def use_selected_item():
            """Use the selected history item."""
            selected_items = history_tree.selection()
            if not selected_items:
                messagebox.showinfo("Selection", "Please select a history item.")
                return
                
            item_id = selected_items[0]
            values = history_tree.item(item_id, "values")
            if not values or len(values) < 3:
                return
                
            # Update output with selected item
            self.output_entry.config(state=tk.NORMAL)
            self.output_entry.delete(1.0, tk.END)
            self.output_entry.insert(tk.END, values[2])  # Output is the third column
            self.output_entry.config(state=tk.DISABLED)
            history_window.destroy()
        
        def copy_selected_item():
            """Copy the selected history item to clipboard."""
            selected_items = history_tree.selection()
            if not selected_items:
                messagebox.showinfo("Selection", "Please select a history item.")
                return
                
            item_id = selected_items[0]
            values = history_tree.item(item_id, "values")
            if not values or len(values) < 3:
                return
                
            self.root.clipboard_clear()
            self.root.clipboard_append(values[2])  # Output is the third column
            messagebox.showinfo("Copy", "Result copied to clipboard!")
        
        def clear_history():
            """Clear all history items."""
            if messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
                self.history.clear()
                history_window.destroy()
                messagebox.showinfo("History", "History cleared successfully!")
        
        # Create buttons
        btn_use = tk.Button(btn_frame, text="Use Selected", command=use_selected_item)
        btn_use.pack(side=tk.LEFT, padx=5)
        
        btn_copy = tk.Button(btn_frame, text="Copy Selected", command=copy_selected_item)
        btn_copy.pack(side=tk.LEFT, padx=5)
        
        btn_clear_history = tk.Button(btn_frame, text="Clear History", command=clear_history)
        btn_clear_history.pack(side=tk.LEFT, padx=5)
        
        btn_close = tk.Button(btn_frame, text="Close", command=history_window.destroy)
        btn_close.pack(side=tk.RIGHT, padx=5)

def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = CoordinateCalculatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()