import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from geographiclib.geodesic import Geodesic
import math
import os

# Constants
GEODESIC = Geodesic.WGS84
MAX_DISTANCE_NM = 26.5
MAX_LATITUDE = 90
MAX_LONGITUDE = 180

# Operation type codes
OPERATION_CODES = {
    "Departure": "4464713",
    "Arrival": "4530249",
    "Approach": "4595785"
}

# Fix type codes
FIX_TYPE_CODES = {
    "VORDME": "D",
    "VOR": "V",
    "NDBDME": "Q",
    "NDB": "N",
    "ILS": "I",
    "RNP": "R"
}

# Fix usage codes
FIX_USAGE_CODES = {
    "Final approach fix": "F",
    "Initial approach fix": "A",
    "Intermediate approach fix": "I",
    "Final approach course fix": "C",
    "Missed approach point fix": "M"
}

# Navigation type mapping
NAV_TYPE_MAPPING = {
    '3': "VOR",
    '12': "DME (VOR)",
    '2': "NDB",
    '13': 'DME',
    '7': 'OUTER MARKER',
    '8': 'MIDDLE MARKER',
    '9': 'INNER MARKER'
}

@dataclass
class Coordinates:
    latitude: float
    longitude: float

    def __str__(self) -> str:
        return f"{self.latitude:.9f} {self.longitude:.9f}"

    @classmethod
    def from_string(cls, coords_str: str) -> 'Coordinates':
        lat, lon = map(float, coords_str.split())
        return cls(lat, lon)

    def validate(self) -> bool:
        return -MAX_LATITUDE <= self.latitude <= MAX_LATITUDE and -MAX_LONGITUDE <= self.longitude <= MAX_LONGITUDE

def calculate_target_coords_geodesic(lat1: float, lon1: float, azimuth: float, distance_nm: float) -> Tuple[float, float]:
    """Calculate target coordinates using geodesic calculations.
    
    Args:
        lat1: Starting latitude in degrees
        lon1: Starting longitude in degrees
        azimuth: Bearing in degrees
        distance_nm: Distance in nautical miles
        
    Returns:
        Tuple of (target_latitude, target_longitude) in degrees
    """
    distance = distance_nm * 1852  # Convert nautical miles to meters
    result = GEODESIC.Direct(lat1, lon1, azimuth, distance)
    return result['lat2'], result['lon2']

def get_radius_letter(distance_nm: float) -> str:
    """Get the single-letter radius designator based on distance.
    
    Args:
        distance_nm: Distance in nautical miles
        
    Returns:
        Single letter radius designator (A-Z)
    """
    ranges = [
        (0.1, 1.4, 'A'), (1.5, 2.4, 'B'), (2.5, 3.4, 'C'), (3.5, 4.4, 'D'),
        (4.5, 5.4, 'E'), (5.5, 6.4, 'F'), (6.5, 7.4, 'G'), (7.5, 8.4, 'H'),
        (8.5, 9.4, 'I'), (9.5, 10.4, 'J'), (10.5, 11.4, 'K'), (11.5, 12.4, 'L'),
        (12.5, 13.4, 'M'), (13.5, 14.4, 'N'), (14.5, 15.4, 'O'), (15.5, 16.4, 'P'),
        (16.5, 17.4, 'Q'), (17.5, 18.4, 'R'), (18.5, 19.4, 'S'), (19.5, 20.4, 'T'),
        (20.5, 21.4, 'U'), (21.5, 22.4, 'V'), (22.5, 23.4, 'W'), (23.5, 24.4, 'X'),
        (24.5, 25.4, 'Y'), (25.5, 26.4, 'Z')
    ]
    
    for low, high, letter in ranges:
        if low <= distance_nm <= high:
            return letter
    return 'Z'

def validate_airport_code(code: str) -> bool:
    """Validate airport code format.
    
    Args:
        code: Airport code to validate
        
    Returns:
        True if valid, False otherwise
    """
    return len(code) == 4 and code.isalpha()

def validate_vor_identifier(identifier: str) -> bool:
    """Validate VOR identifier format.
    
    Args:
        identifier: VOR identifier to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 3 <= len(identifier) <= 4 and identifier.isalpha()

def validate_runway_code(code: str) -> bool:
    """Validate runway code format.
    
    Args:
        code: Runway code to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        code_int = int(code)
        return 0 <= code_int <= 99
    except ValueError:
        return False

class CoordinateCalculatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Coordinate Calculator")
        self.root.geometry("750x650")
        
        # Initialize variables
        self.mode_var = tk.StringVar(value="WAYPOINT")
        self.fix_file_path = ""
        self.nav_file_path = ""
        self.search_file_type = tk.StringVar(value="NAV")
        self.pending_calculation_params = None
        
        # Create UI components
        self._create_ui()
        self._setup_bindings()
        
    def _create_ui(self) -> None:
        """Create all UI components."""
        self.create_mode_selection()
        self.create_file_selection()
        
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=5, fill="x")
        
        self.waypoint_frame = tk.Frame(self.input_frame)
        self.fix_frame = tk.Frame(self.input_frame)
        
        self.create_waypoint_ui()
        self.create_fix_ui()
        
        self.output_area = self.create_output_ui()
        self.on_mode_change()
        self.create_bottom_buttons()
        
    def _setup_bindings(self) -> None:
        """Setup event bindings."""
        self.mode_var.trace_add('write', self.on_mode_change)
        
    def create_mode_selection(self) -> None:
        """Create mode selection UI."""
        frm_mode = tk.LabelFrame(self.root, text="Mode Selection", padx=10, pady=5)
        frm_mode.pack(padx=10, pady=5, fill="x")
        
        tk.Label(frm_mode, text="Select Mode:").pack(side=tk.LEFT, padx=5)
        combo_mode = ttk.Combobox(
            frm_mode, 
            textvariable=self.mode_var, 
            values=('WAYPOINT', 'FIX'), 
            state="readonly"
        )
        combo_mode.pack(side=tk.LEFT, padx=5)
        
    def create_file_selection(self) -> None:
        """Create file selection UI."""
        frm_file = tk.LabelFrame(
            self.root, 
            text="File Selection", 
            padx=10, 
            pady=5, 
            borderwidth=2, 
            relief=tk.GROOVE
        )
        frm_file.pack(padx=10, pady=5, fill="x")
        
        # Initialize entry widgets
        self.entry_fix_file = tk.Entry(frm_file, width=40)
        self.entry_nav_file = tk.Entry(frm_file, width=40)
        
        # FIX File Selection
        self._create_file_entry(
            frm_file, 
            "FIX File:", 
            "FIX", 
            self.entry_fix_file
        )
        
        # NAV File Selection
        self._create_file_entry(
            frm_file, 
            "NAV File:", 
            "NAV", 
            self.entry_nav_file
        )
        
    def _create_file_entry(
        self, 
        parent: tk.Frame, 
        label_text: str, 
        file_type: str, 
        entry_widget: tk.Entry
    ) -> None:
        """Create a file entry with browse button.
        
        Args:
            parent: Parent frame
            label_text: Label text
            file_type: Type of file (FIX/NAV)
            entry_widget: Entry widget to use
        """
        tk.Label(parent, text=label_text, width=8, anchor="w").pack(side=tk.LEFT, padx=5)
        entry_widget.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        btn_browse = tk.Button(
            parent, 
            text="Browse", 
            command=lambda: self.browse_file(file_type)
        )
        btn_browse.pack(side=tk.LEFT, padx=5)
        
    def browse_file(self, file_type: str) -> None:
        """Open file browser dialog.
        
        Args:
            file_type: Type of file to browse for
        """
        filepath = filedialog.askopenfilename(
            title=f"Select {file_type} File",
            filetypes=[(f"{file_type} files", "*.dat"), ("All files", "*.*")]
        )
        
        if filepath:
            if file_type == "FIX":
                self.fix_file_path = filepath
                self.entry_fix_file.delete(0, tk.END)
                self.entry_fix_file.insert(0, filepath)
            elif file_type == "NAV":
                self.nav_file_path = filepath
                self.entry_nav_file.delete(0, tk.END)
                self.entry_nav_file.insert(0, filepath)

    def on_mode_change(self, *args):
        current_mode = self.mode_var.get()
        self.waypoint_frame.pack_forget()
        self.fix_frame.pack_forget()

        if current_mode == "WAYPOINT":
            self.waypoint_frame.pack(side=tk.TOP, fill="x", pady=5)
            self.search_file_type.set("NAV") # WAYPOINT searches NAV by default
        elif current_mode == "FIX":
            self.fix_frame.pack(side=tk.TOP, fill="x", pady=5)
            self.search_file_type.set("FIX") # FIX searches FIX by default

    def create_waypoint_ui(self) -> None:
        """Create waypoint calculation UI."""
        frm = self.waypoint_frame
        frm.columnconfigure(1, weight=1)
        
        # File Type Selection
        self._create_search_file_selection(frm)
        
        # Identifier Entry with Search
        self._create_identifier_entry(frm, "VOR/DME/NDB Identifier:", "waypoint")
        
        # Coordinate Entry
        self._create_coordinate_entry(frm, "Coordinates (Lat Lon):", "waypoint")
        
        # Bearing Entry
        self._create_numeric_entry(frm, "Magnetic Bearing (°):", "bearing")
        
        # Distance Entry
        self._create_numeric_entry(frm, "Distance (NM):", "distance")
        
        # Declination Entry
        self._create_numeric_entry(frm, "Magnetic Declination (°):", "declination")
        
        # Airport Code Entry
        self._create_airport_entry(frm)
        
        # VOR Identifier Entry
        self._create_vor_entry(frm)
        
        # Operation Type Selection
        self._create_operation_type_selection(frm)
        
        # Calculate Button
        self._create_calculate_button(frm, "Calculate Waypoint", self.on_calculate_waypoint)
        
    def _create_search_file_selection(self, parent: tk.Frame) -> None:
        """Create file type selection for search."""
        tk.Label(parent, text="Search in File Type:", anchor="e").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        combo_search_file = ttk.Combobox(
            parent, 
            textvariable=self.search_file_type, 
            values=("NAV", "FIX"), 
            state="readonly"
        )
        combo_search_file.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
    def _create_identifier_entry(self, parent: tk.Frame, label: str, mode: str) -> None:
        """Create identifier entry with search button."""
        tk.Label(parent, text=label, anchor="e").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        entry = tk.Entry(parent, width=30)
        entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        search_cmd = self.search_waypoint_coords if mode == "waypoint" else self.search_fix_coords
        btn_search = tk.Button(
            parent, 
            text="Search Coordinates", 
            command=search_cmd
        )
        btn_search.grid(row=1, column=2, padx=5, pady=5)
        
        if mode == "waypoint":
            self.entry_waypoint_identifier = entry
        else:
            self.entry_fix_identifier = entry
            
    def _create_coordinate_entry(self, parent: tk.Frame, label: str, mode: str) -> None:
        """Create coordinate entry field."""
        tk.Label(parent, text=label, anchor="e").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        entry = tk.Entry(parent, width=30)
        entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        if mode == "waypoint":
            self.entry_waypoint_coords = entry
        else:
            self.entry_fix_coords = entry
            
    def _create_numeric_entry(self, parent: tk.Frame, label: str, name: str) -> None:
        """Create numeric entry field."""
        tk.Label(parent, text=label, anchor="e").grid(
            row=self._get_next_row(parent), 
            column=0, 
            padx=5, 
            pady=5, 
            sticky="e"
        )
        entry = tk.Entry(parent, width=30)
        entry.grid(
            row=self._get_next_row(parent)-1, 
            column=1, 
            padx=5, 
            pady=5, 
            sticky="ew"
        )
        
        setattr(self, f"entry_{name}", entry)
        
    def _get_next_row(self, parent: tk.Frame) -> int:
        """Get the next available row in the grid."""
        return len(parent.winfo_children()) // 2 + 1
        
    def _create_airport_entry(self, parent: tk.Frame) -> None:
        """Create airport code entry field."""
        tk.Label(parent, text="Airport Code:", anchor="e").grid(
            row=self._get_next_row(parent), 
            column=0, 
            padx=5, 
            pady=5, 
            sticky="e"
        )
        self.entry_airport_code = tk.Entry(parent, width=30)
        self.entry_airport_code.grid(
            row=self._get_next_row(parent)-1, 
            column=1, 
            padx=5, 
            pady=5, 
            sticky="ew"
        )
        
    def _create_vor_entry(self, parent: tk.Frame) -> None:
        """Create VOR identifier entry field."""
        tk.Label(parent, text="VOR Identifier:", anchor="e").grid(
            row=self._get_next_row(parent), 
            column=0, 
            padx=5, 
            pady=5, 
            sticky="e"
        )
        self.entry_vor_identifier = tk.Entry(parent, width=30)
        self.entry_vor_identifier.grid(
            row=self._get_next_row(parent)-1, 
            column=1, 
            padx=5, 
            pady=5, 
            sticky="ew"
        )
        
    def _create_operation_type_selection(self, parent: tk.Frame) -> None:
        """Create operation type selection."""
        tk.Label(parent, text="Operation Type:", anchor="e").grid(
            row=self._get_next_row(parent), 
            column=0, 
            padx=5, 
            pady=5, 
            sticky="e"
        )
        self.combo_operation_type = ttk.Combobox(
            parent, 
            values=list(OPERATION_CODES.keys()), 
            state="readonly"
        )
        self.combo_operation_type.current(0)
        self.combo_operation_type.grid(
            row=self._get_next_row(parent)-1, 
            column=1, 
            padx=5, 
            pady=5, 
            sticky="ew"
        )
        
    def _create_calculate_button(self, parent: tk.Frame, text: str, command: callable) -> None:
        """Create calculate button."""
        btn_calc = tk.Button(parent, text=text, command=command)
        btn_calc.grid(
            row=self._get_next_row(parent), 
            column=0, 
            columnspan=2, 
            pady=5
        )

    def create_fix_ui(self) -> None:
        """Create FIX calculation UI."""
        frm = self.fix_frame
        frm.columnconfigure(1, weight=1)
        
        # File Type Selection
        self._create_search_file_selection(frm)
        
        # Identifier Entry with Search
        self._create_identifier_entry(frm, "FIX Identifier:", "fix")
        
        # Coordinate Entry
        self._create_coordinate_entry(frm, "FIX Coordinates (Lat Lon):", "fix")
        
        # FIX Type Selection
        self._create_fix_type_selection(frm)
        
        # FIX Usage Selection
        self._create_fix_usage_selection(frm)
        
        # Runway Code Entry
        self._create_numeric_entry(frm, "Runway Code:", "runway_code")
        
        # Airport Code Entry
        self._create_airport_entry(frm)
        
        # Operation Type Selection
        self._create_operation_type_selection(frm)
        
        # Calculate Button
        self._create_calculate_button(frm, "Calculate FIX", self.on_calculate_fix)
        
    def _create_fix_type_selection(self, parent: tk.Frame) -> None:
        """Create FIX type selection."""
        tk.Label(parent, text="FIX Type:", anchor="e").grid(
            row=self._get_next_row(parent), 
            column=0, 
            padx=5, 
            pady=5, 
            sticky="e"
        )
        self.combo_fix_type = ttk.Combobox(
            parent, 
            values=list(FIX_TYPE_CODES.keys()), 
            state="readonly"
        )
        self.combo_fix_type.current(0)
        self.combo_fix_type.grid(
            row=self._get_next_row(parent)-1, 
            column=1, 
            padx=5, 
            pady=5, 
            sticky="ew"
        )
        
    def _create_fix_usage_selection(self, parent: tk.Frame) -> None:
        """Create FIX usage selection."""
        tk.Label(parent, text="FIX Usage:", anchor="e").grid(
            row=self._get_next_row(parent), 
            column=0, 
            padx=5, 
            pady=5, 
            sticky="e"
        )
        self.combo_fix_usage = ttk.Combobox(
            parent, 
            values=list(FIX_USAGE_CODES.keys()), 
            state="readonly"
        )
        self.combo_fix_usage.current(0)
        self.combo_fix_usage.grid(
            row=self._get_next_row(parent)-1, 
            column=1, 
            padx=5, 
            pady=5, 
            sticky="ew"
        )
        
    def create_output_ui(self) -> tk.LabelFrame:
        """Create output display UI."""
        frm_output = tk.LabelFrame(self.root, text="Output Result", padx=10, pady=5)
        frm_output.pack(padx=10, pady=5, fill="both", expand=True)
        
        self.output_entry = tk.Text(
            frm_output, 
            width=80, 
            height=8, 
            state="disabled"
        )
        self.output_entry.pack(padx=5, pady=5, fill="both", expand=True)
        
        return frm_output
        
    def create_bottom_buttons(self) -> None:
        """Create bottom action buttons."""
        frm_btn = tk.Frame(self.root)
        frm_btn.pack(padx=10, pady=5, fill="x")
        
        btn_clear = tk.Button(
            frm_btn, 
            text="Clear Input", 
            command=self.clear_fields
        )
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        btn_copy = tk.Button(
            frm_btn, 
            text="Copy Result", 
            command=self.copy_output
        )
        btn_copy.pack(side=tk.LEFT, padx=5)
        
        btn_exit = tk.Button(
            frm_btn, 
            text="Exit", 
            command=self.root.quit
        )
        btn_exit.pack(side=tk.RIGHT, padx=5)
        
    def clear_fields(self) -> None:
        """Clear all input fields and output."""
        if self.mode_var.get() == "WAYPOINT":
            self._clear_waypoint_fields()
        elif self.mode_var.get() == "FIX":
            self._clear_fix_fields()
            
        self._clear_output()
        
    def _clear_waypoint_fields(self) -> None:
        """Clear waypoint input fields."""
        self.entry_waypoint_identifier.delete(0, tk.END)
        self.entry_waypoint_coords.delete(0, tk.END)
        self.entry_bearing.delete(0, tk.END)
        self.entry_distance.delete(0, tk.END)
        self.entry_declination.delete(0, tk.END)
        self.entry_airport_code.delete(0, tk.END)
        self.entry_vor_identifier.delete(0, tk.END)
        
    def _clear_fix_fields(self) -> None:
        """Clear FIX input fields."""
        self.entry_fix_identifier.delete(0, tk.END)
        self.entry_fix_coords.delete(0, tk.END)
        self.entry_runway_code.delete(0, tk.END)
        self.entry_fix_airport_code.delete(0, tk.END)
        
    def _clear_output(self) -> None:
        """Clear output display."""
        self.output_entry.config(state=tk.NORMAL)
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.config(state=tk.DISABLED)
        
    def copy_output(self) -> None:
        """Copy output text to clipboard."""
        output_text = self.output_entry.get(1.0, tk.END).strip()
        if output_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(output_text)
            messagebox.showinfo("Copy Result", "Result copied to clipboard!")
        else:
            messagebox.showwarning("Copy Result", "No text to copy!")

    def calculate_target_coords_vincenty(self, lat_vor, lon_vor, magnetic_bearing, distance_nm, declination):
        true_bearing = (magnetic_bearing + declination) % 360
        return calculate_target_coords_geodesic(lat_vor, lon_vor, true_bearing, distance_nm)

    def validate_input(self, mode: str) -> Optional[Tuple[Any, ...]]:
        """Validate input based on mode.
        
        Args:
            mode: Calculation mode ("WAYPOINT" or "FIX")
            
        Returns:
            Tuple of validated parameters if valid, None otherwise
        """
        if mode == "WAYPOINT":
            return self._validate_waypoint_input()
        elif mode == "FIX":
            return self._validate_fix_input()
        return None
        
    def _validate_waypoint_input(self) -> Optional[Tuple[Any, ...]]:
        """Validate waypoint input parameters.
        
        Returns:
            Tuple of (lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier)
            if valid, None otherwise
        """
        try:
            # Validate coordinates if entered manually
            coords_str = self.entry_waypoint_coords.get().strip()
            lat_vor, lon_vor = None, None
            
            if coords_str:
                coords = Coordinates.from_string(coords_str)
                if not coords.validate():
                    raise ValueError("Latitude/Longitude out of range (±90 / ±180)")
                lat_vor, lon_vor = coords.latitude, coords.longitude
            elif not self.entry_waypoint_identifier.get().strip():
                raise ValueError("Coordinates or Identifier must be provided")
                
            # Validate numeric inputs
            magnetic_bearing = float(self.entry_bearing.get())
            if not (0 <= magnetic_bearing < 360):
                raise ValueError("Magnetic bearing should be within 0-359 degrees")
                
            distance_nm = float(self.entry_distance.get())
            if distance_nm <= 0:
                raise ValueError("Distance should be greater than 0 nautical miles")
                
            declination = float(self.entry_declination.get())
            
            # Validate text inputs
            airport_code = self.entry_airport_code.get().strip().upper()
            if not validate_airport_code(airport_code):
                raise ValueError("Airport code must be 4 letters")
                
            vor_identifier = self.entry_vor_identifier.get().strip().upper()
            if vor_identifier and not validate_vor_identifier(vor_identifier):
                raise ValueError("VOR identifier should be 3-4 letters and alphabetic")
                
            return lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"WAYPOINT mode input error: {e}")
            return None
            
    def _validate_fix_input(self) -> Optional[Tuple[Any, ...]]:
        """Validate FIX input parameters.
        
        Returns:
            Tuple of (lat, lon, fix_type, fix_usage, runway_code, airport_code, operation_code)
            if valid, None otherwise
        """
        try:
            # Validate coordinates
            coords_str = self.entry_fix_coords.get().strip()
            if not coords_str:
                raise ValueError("Please search for and select coordinates first or enter manually")
                
            coords = Coordinates.from_string(coords_str)
            if not coords.validate():
                raise ValueError("Latitude/Longitude out of range (±90 / ±180)")
                
            # Validate runway code
            runway_code = self.entry_runway_code.get().strip()
            if not validate_runway_code(runway_code):
                raise ValueError("Runway code should be a two-digit number between 0 and 99")
                
            # Validate airport code
            airport_code = self.entry_fix_airport_code.get().strip().upper()
            if not validate_airport_code(airport_code):
                raise ValueError("Airport code must be 4 letters")
                
            # Get and validate fix type and usage
            fix_type = self.combo_fix_type.get()
            fix_usage = self.combo_fix_usage.get()
            
            if fix_type not in FIX_TYPE_CODES or fix_usage not in FIX_USAGE_CODES:
                raise ValueError("Invalid FIX type or usage")
                
            return (
                coords.latitude,
                coords.longitude,
                FIX_TYPE_CODES[fix_type],
                FIX_USAGE_CODES[fix_usage],
                runway_code,
                airport_code,
                OPERATION_CODES[self.combo_fix_operation_type.get()]
            )
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"FIX mode input error: {e}")
            return None
            
    def on_calculate_waypoint(self) -> None:
        """Handle waypoint calculation."""
        params = self.validate_input("WAYPOINT")
        if params is None:
            return
            
        lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier = params
        
        if lat_vor is None or lon_vor is None:
            identifier = self.entry_waypoint_identifier.get().strip().upper()
            if not identifier:
                messagebox.showerror("Input Error", "Please enter identifier or coordinates.")
                return
            self.search_waypoint_coords_and_calculate(
                identifier, 
                magnetic_bearing, 
                distance_nm, 
                declination, 
                airport_code, 
                vor_identifier
            )
            return
            
        try:
            lat_target, lon_target = self.calculate_target_coords_vincenty(
                lat_vor, 
                lon_vor, 
                magnetic_bearing, 
                distance_nm, 
                declination
            )
            radius_letter = get_radius_letter(distance_nm)
            operation_code = OPERATION_CODES[self.combo_operation_type.get()]
            
            result = (
                round(lat_target, 9),
                round(lon_target, 9),
                radius_letter,
                airport_code,
                operation_code
            )
            
            self.process_output(result, "WAYPOINT", vor_identifier, magnetic_bearing, distance_nm)
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {str(e)}")
            
    def on_calculate_fix(self) -> None:
        """Handle FIX calculation."""
        params = self.validate_input("FIX")
        if params is None:
            return
            
        try:
            result = params
            self.process_output(result, "FIX")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {str(e)}")

    def search_waypoint_coords(self) -> None:
        """Search for waypoint coordinates in selected file."""
        identifier = self.entry_waypoint_identifier.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter an identifier.")
            return
            
        file_type = self.search_file_type.get()
        file_path = self._get_file_path(file_type)
        if not file_path:
            return
            
        try:
            matching_lines = self._search_file(file_path, identifier, file_type)
            if not matching_lines:
                messagebox.showinfo("Not Found", f"{file_type} identifier '{identifier}' not found.")
                return
                
            if len(matching_lines) > 1:
                self.handle_duplicate_entries(matching_lines, "WAYPOINT")
            else:
                self.set_waypoint_coords(matching_lines[0])
                
        except Exception as e:
            messagebox.showerror("File Error", f"Error reading {file_type} file: {e}")
            
    def search_fix_coords(self) -> None:
        """Search for FIX coordinates in selected file."""
        identifier = self.entry_fix_identifier.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter a FIX identifier.")
            return
            
        file_type = self.search_file_type.get()
        file_path = self._get_file_path(file_type)
        if not file_path:
            return
            
        try:
            matching_lines = self._search_file(file_path, identifier, file_type)
            if not matching_lines:
                messagebox.showinfo("Not Found", f"{file_type} identifier '{identifier}' not found.")
                return
                
            if len(matching_lines) > 1:
                self.handle_duplicate_entries(matching_lines, "FIX")
            else:
                self.set_fix_coords(matching_lines[0])
                
        except Exception as e:
            messagebox.showerror("File Error", f"Error reading {file_type} file: {e}")
            
    def _get_file_path(self, file_type: str) -> Optional[str]:
        """Get file path based on file type.
        
        Args:
            file_type: Type of file (FIX/NAV)
            
        Returns:
            File path if valid, None otherwise
        """
        file_path = self.fix_file_path if file_type == "FIX" else self.nav_file_path
        if not file_path:
            messagebox.showerror("File Error", f"Please select a {file_type} data file.")
            return None
        return file_path
        
    def _search_file(self, file_path: str, identifier: str, file_type: str) -> List[List[str]]:
        """Search file for matching identifier.
        
        Args:
            file_path: Path to file to search
            identifier: Identifier to search for
            file_type: Type of file (FIX/NAV)
            
        Returns:
            List of matching lines
        """
        matching_lines = []
        relevant_index = 7 if file_type == "NAV" else 2
        
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) > relevant_index and parts[relevant_index] == identifier:
                    matching_lines.append(parts)
                    
        return matching_lines
        
    def handle_duplicate_entries(self, matching_lines: List[List[str]], mode: str) -> None:
        """Handle multiple matching entries.
        
        Args:
            matching_lines: List of matching lines
            mode: Current mode (WAYPOINT/FIX)
        """
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Choose Entry")
        tk.Label(choice_window, text="Multiple entries found. Please choose one:").pack()
        
        selected_line = tk.StringVar()
        
        for line_parts in matching_lines:
            first_part = line_parts[0]
            type_str = NAV_TYPE_MAPPING.get(first_part, "Unknown")
            relevant_index = 7 if self.search_file_type.get() == "NAV" else 2
            display_text = f"{type_str} - {line_parts[relevant_index]}"
            
            if len(line_parts) > 9:
                display_text += f" - {line_parts[9]}"
            else:
                display_text += " - [Tenth part missing]"
                
            tk.Radiobutton(
                choice_window, 
                text=display_text, 
                variable=selected_line, 
                value=",".join(line_parts)
            ).pack()
            
        def confirm_choice() -> None:
            chosen_line = selected_line.get()
            if chosen_line:
                if mode == "WAYPOINT":
                    self.set_waypoint_coords(chosen_line.split(","))
                elif mode == "FIX":
                    self.set_fix_coords(chosen_line.split(","))
                choice_window.destroy()
            else:
                messagebox.showwarning("Selection Required", "Please select an entry.")
                
        tk.Button(choice_window, text="Confirm", command=confirm_choice).pack()
        choice_window.wait_window()
        
    def set_waypoint_coords(self, line_parts: List[str]) -> None:
        """Set waypoint coordinates from line parts.
        
        Args:
            line_parts: List of parts from file line
        """
        try:
            file_type = self.search_file_type.get()
            lat_index = 1 if file_type == "NAV" else 0
            lon_index = 2 if file_type == "NAV" else 1
            
            lat = float(line_parts[lat_index])
            lon = float(line_parts[lon_index])
            
            self.entry_waypoint_coords.delete(0, tk.END)
            self.entry_waypoint_coords.insert(0, f"{lat} {lon}")
            
            if hasattr(self, 'pending_calculation_params'):
                magnetic_bearing, distance_nm, declination, airport_code, vor_identifier = self.pending_calculation_params
                self.on_calculate_waypoint()
                del self.pending_calculation_params
                
        except (ValueError, IndexError):
            messagebox.showerror("Data Error", "Invalid coordinate data in the selected file.")
            
    def set_fix_coords(self, line_parts: List[str]) -> None:
        """Set FIX coordinates from line parts.
        
        Args:
            line_parts: List of parts from file line
        """
        try:
            file_type = self.search_file_type.get()
            lat_index = 0 if file_type == "FIX" else 1
            lon_index = 1 if file_type == "FIX" else 2
            
            lat = float(line_parts[lat_index])
            lon = float(line_parts[lon_index])
            
            self.entry_fix_coords.delete(0, tk.END)
            self.entry_fix_coords.insert(0, f"{lat} {lon}")
            
        except (ValueError, IndexError):
            messagebox.showerror("Data Error", "Invalid coordinate data in the selected file.")

    def search_waypoint_coords_and_calculate(self, identifier, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier):
        """Searches waypoint coordinates and then performs calculation."""
        file_type = self.search_file_type.get()
        file_path = self.nav_file_path if file_type == "NAV" else self.fix_file_path
        if not file_path:
            messagebox.showerror("File Error", f"Please select a {file_type} data file.")
            return

        try:
            with open(file_path, 'r') as file:
                matching_lines = []
                for line in file:
                    parts = line.strip().split()
                    relevant_index = 7 if file_type == "NAV" else 2
                    if len(parts) > relevant_index and parts[relevant_index] == identifier:
                        matching_lines.append(parts)

            if not matching_lines:
                messagebox.showinfo("Not Found", f"{file_type} identifier '{identifier}' not found.")
                return

            if len(matching_lines) > 1:
                self.pending_calculation_params = (magnetic_bearing, distance_nm, declination, airport_code, vor_identifier) # Store parameters
                self.handle_duplicate_entries(matching_lines, "WAYPOINT") # Let duplicate handler set coords and then calculation will trigger in set_waypoint_coords after selection
            else:
                self.set_waypoint_coords_and_continue_calculation(matching_lines[0], magnetic_bearing, distance_nm, declination, airport_code, vor_identifier) # Continue calculation directly
        except FileNotFoundError:
            messagebox.showerror("File Error", f"File not found: {file_path}")
        except Exception as e:
            messagebox.showerror("File Read Error", f"Error reading {file_type} file: {e}")

    def set_waypoint_coords_and_continue_calculation(self, line_parts, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier):
        """Sets waypoint coordinates and continues with the calculation."""
        try:
            file_type = self.search_file_type.get()
            lat_index = 1 if file_type == "NAV" else 0
            lon_index = 2 if file_type == "NAV" else 1

            lat_vor = float(line_parts[lat_index])
            lon_vor = float(line_parts[lon_index])

            lat_target, lon_target = self.calculate_target_coords_vincenty(lat_vor, lon_vor, magnetic_bearing, distance_nm, declination)
            radius_letter = get_radius_letter(distance_nm)
            operation_code_map = {"Departure": "4464713", "Arrival": "4530249", "Approach": "4595785"}
            operation_code = operation_code_map.get(self.combo_operation_type.get(), "")
            result = (round(lat_target, 9), round(lon_target, 9), radius_letter, airport_code, operation_code)
            self.process_output(result, "WAYPOINT", vor_identifier, magnetic_bearing, distance_nm)

        except (ValueError, IndexError) as e:
            messagebox.showerror("Data Error", f"Invalid coordinate data or calculation error: {e}")

    def process_output(self, result: Tuple[Any, ...], mode: str, vor_identifier: str = "", 
                      magnetic_bearing: str = "", distance_nm: str = "") -> None:
        """Process and display calculation results.
        
        Args:
            result: Calculation result tuple
            mode: Calculation mode (WAYPOINT/FIX)
            vor_identifier: VOR identifier for waypoint mode
            magnetic_bearing: Magnetic bearing for waypoint mode
            distance_nm: Distance in nautical miles for waypoint mode
        """
        try:
            output = self._format_output(result, mode, vor_identifier, magnetic_bearing, distance_nm)
            self._display_output(output)
        except Exception as e:
            messagebox.showerror("Output Error", f"Error processing output: {str(e)}")
            
    def _format_output(self, result: Tuple[Any, ...], mode: str, vor_identifier: str,
                      magnetic_bearing: str, distance_nm: str) -> str:
        """Format calculation result for display.
        
        Args:
            result: Calculation result tuple
            mode: Calculation mode (WAYPOINT/FIX)
            vor_identifier: VOR identifier for waypoint mode
            magnetic_bearing: Magnetic bearing for waypoint mode
            distance_nm: Distance in nautical miles for waypoint mode
            
        Returns:
            Formatted output string
        """
        if mode == "WAYPOINT":
            return self._format_waypoint_output(result, vor_identifier, magnetic_bearing, distance_nm)
        elif mode == "FIX":
            return self._format_fix_output(result)
        return ""
        
    def _format_waypoint_output(self, result: Tuple[Any, ...], vor_identifier: str,
                              magnetic_bearing: str, distance_nm: str) -> str:
        """Format waypoint calculation result.
        
        Args:
            result: Calculation result tuple
            vor_identifier: VOR identifier
            magnetic_bearing: Magnetic bearing
            distance_nm: Distance in nautical miles
            
        Returns:
            Formatted waypoint output string
        """
        lat_target, lon_target, radius_letter, airport_code, operation_code = result
        distance_nm_float = float(distance_nm)
        rounded_distance = int(round(distance_nm_float))
        
        if distance_nm_float > MAX_DISTANCE_NM:
            output = (f"{lat_target:.9f} {lon_target:.9f} "
                     f"{vor_identifier}{rounded_distance} "
                     f"{airport_code} {airport_code[:2]}")
                     
            if vor_identifier:
                magnetic_bearing_int = int(float(magnetic_bearing))
                output += f" {operation_code} {vor_identifier}{magnetic_bearing_int:03d}{rounded_distance:03d}"
            else:
                output += f" {operation_code}"
        else:
            output = (f"{lat_target:.9f} {lon_target:.9f} "
                     f"D{int(float(magnetic_bearing)):03d}{radius_letter} "
                     f"{airport_code} {airport_code[:2]}")
                     
            if vor_identifier:
                magnetic_bearing_int = int(float(magnetic_bearing))
                output += f" {operation_code} {vor_identifier}{magnetic_bearing_int:03d}{rounded_distance:03d}"
            else:
                output += f" {operation_code}"
                
        return output
        
    def _format_fix_output(self, result: Tuple[Any, ...]) -> str:
        """Format FIX calculation result.
        
        Args:
            result: Calculation result tuple
            
        Returns:
            Formatted FIX output string
        """
        lat, lon, fix_code, usage_code, runway_code, airport_code, operation_code = result
        return (f"{lat:.9f} {lon:.9f} {usage_code}{fix_code}{int(runway_code):02d} "
                f"{airport_code} {airport_code[:2]} {operation_code}")
                
    def _display_output(self, output: str) -> None:
        """Display formatted output in text widget.
        
        Args:
            output: Formatted output string
        """
        self.output_entry.config(state=tk.NORMAL)
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.insert(tk.END, output)
        self.output_entry.config(state=tk.DISABLED)

def main() -> None:
    """Main entry point for the application."""
    try:
        root = tk.Tk()
        app = CoordinateCalculatorApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", f"Error starting application: {str(e)}")

if __name__ == "__main__":
    main()
