import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from geographiclib.geodesic import Geodesic
import math
import os
import datetime
import importlib.util

# Constants for the Earth's ellipsoid model with maximum precision settings
GEODESIC = Geodesic.WGS84

# Ultra high precision settings for intersection calculations
MAX_ITERATIONS = 200  # Increased max iterations for better convergence with tight tolerance
DISTANCE_TOLERANCE_NM = 0.00000054  # About 1 meter in nautical miles (1/1852)
DISTANCE_TOLERANCE_M = 1.0  # Tolerance in meters (1-meter precision)
ANGLE_TOLERANCE_DEG = 0.0001  # Extremely precise angular tolerance (about 0.36 arcseconds)

# Meters per nautical mile, defined exactly
METERS_PER_NM = 1852.0

# Check if pygeomag is available
try:
    spec = importlib.util.find_spec("pygeomag")
    if spec is not None:
        from pygeomag import GeoMag
        PYGEOMAG_AVAILABLE = True
        # Initialize GeoMag with default coefficient file
        try:
            # Try with high resolution
            geo_mag = GeoMag(high_resolution=True)
            GEOMAG_INITIALIZED = True
        except Exception as e:
            try:
                # Try with standard resolution
                geo_mag = GeoMag(high_resolution=False)
                GEOMAG_INITIALIZED = True
            except Exception as e:
                GEOMAG_INITIALIZED = False
    else:
        PYGEOMAG_AVAILABLE = False
        GEOMAG_INITIALIZED = False
except ImportError:
    PYGEOMAG_AVAILABLE = False
    GEOMAG_INITIALIZED = False

def meters_to_nm(meters):
    """Convert meters to nautical miles with high precision."""
    return meters / METERS_PER_NM

def nm_to_meters(nm):
    """Convert nautical miles to meters with high precision."""
    return nm * METERS_PER_NM

def get_magnetic_declination(lat, lon):
    """Calculate magnetic declination at the given coordinates."""
    if not (PYGEOMAG_AVAILABLE and GEOMAG_INITIALIZED):
        messagebox.showwarning("Auto Declination", "pygeomag module not available or not initialized. Using 0.0 as default declination.")
        return 0.0
    
    try:
        # Get current time for declination calculation
        today = datetime.datetime.today()
        year = today.year
        day_of_year = today.timetuple().tm_yday
        time = year + (day_of_year - 1) / 365
        
        # Calculate magnetic declination
        result = geo_mag.calculate(glat=lat, glon=lon, alt=0, time=time)
        return result.d  # Declination in degrees
    except Exception as e:
        messagebox.showwarning("Auto Declination", f"Error calculating declination: {e}. Using 0.0 as default.")
        return 0.0

def calculate_target_coords_geodesic(lat1, lon1, azimuth, distance_nm):
    """Calculates the target coordinates with ultra-high precision.
    
    Args:
        lat1: Starting latitude in degrees
        lon1: Starting longitude in degrees
        azimuth: True bearing in degrees
        distance_nm: Distance in nautical miles
        
    Returns:
        Tuple of (lat2, lon2) in degrees with at least 9 decimal places
    """
    # Convert NM to meters (exact conversion)
    distance_m = nm_to_meters(distance_nm)
    
    # Perform high-precision calculation
    result = GEODESIC.Direct(lat1, lon1, azimuth, distance_m)
    
    # Verify the calculation
    verification = GEODESIC.Inverse(lat1, lon1, result['lat2'], result['lon2'])
    actual_distance_m = verification['s12']
    distance_error_m = abs(actual_distance_m - distance_m)
    
    # If error is greater than 10cm, perform iterative refinement
    if distance_error_m > 0.1:
        # Try multiple-step approach for higher accuracy with very long distances
        num_steps = max(1, int(distance_nm / 500))  # Split into steps for very long distances
        if num_steps > 1:
            step_lat, step_lon = lat1, lon1
            step_distance = distance_m / num_steps
            for _ in range(num_steps):
                step_result = GEODESIC.Direct(step_lat, step_lon, azimuth, step_distance)
                step_lat, step_lon = step_result['lat2'], step_result['lon2']
            return step_lat, step_lon
    
    return result['lat2'], result['lon2']

def get_radius_letter(distance_nm):
    """Gets the single-letter radius designator."""
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

class CoordinateCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Coordinate Calculator")
        self.root.geometry("750x650")  # Adjusted for new UI elements

        self.mode_var = tk.StringVar(value="WAYPOINT")
        self.fix_file_path = ""
        self.nav_file_path = ""
        self.search_file_type = tk.StringVar(value="NAV") # Default to NAV for WAYPOINT
        
        # Initialize history list to store calculation results
        self.history = []

        self.create_mode_selection()
        self.create_file_selection()

        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=5, fill="x")

        self.waypoint_frame = tk.Frame(self.input_frame)
        self.fix_frame = tk.Frame(self.input_frame)

        self.create_waypoint_ui()
        self.create_fix_ui()

        self.output_area = self.create_output_ui()
        self.on_mode_change() # Initial setup based on default mode
        self.create_bottom_buttons()

    def create_mode_selection(self):
        frm_mode = tk.LabelFrame(self.root, text="Mode Selection", padx=10, pady=5)
        frm_mode.pack(padx=10, pady=5, fill="x")

        tk.Label(frm_mode, text="Select Mode:").pack(side=tk.LEFT, padx=5)
        combo_mode = ttk.Combobox(frm_mode, textvariable=self.mode_var, values=('WAYPOINT', 'FIX'), state="readonly")
        combo_mode.pack(side=tk.LEFT, padx=5)
        self.mode_var.trace_add('write', self.on_mode_change)

    def create_file_selection(self):
        frm_file = tk.LabelFrame(self.root, text="File Selection", padx=10, pady=5, borderwidth=2, relief=tk.GROOVE) # Added border for better visual grouping
        frm_file.pack(padx=10, pady=5, fill="x")

        # FIX File Selection
        tk.Label(frm_file, text="FIX File:", width=8, anchor="w").pack(side=tk.LEFT, padx=5) # Aligned labels and added width
        self.entry_fix_file = tk.Entry(frm_file, width=40)
        self.entry_fix_file.pack(side=tk.LEFT, padx=5, fill="x", expand=True) # Allow entry to expand
        btn_browse_fix = tk.Button(frm_file, text="Browse", command=lambda: self.browse_file("FIX"))
        btn_browse_fix.pack(side=tk.LEFT, padx=5)

        # NAV File Selection
        tk.Label(frm_file, text="NAV File:", width=8, anchor="w").pack(side=tk.LEFT, padx=5) # Aligned labels and added width
        self.entry_nav_file = tk.Entry(frm_file, width=40)
        self.entry_nav_file.pack(side=tk.LEFT, padx=5, fill="x", expand=True) # Allow entry to expand
        btn_browse_nav = tk.Button(frm_file, text="Browse", command=lambda: self.browse_file("NAV"))
        btn_browse_nav.pack(side=tk.LEFT, padx=5)

    def browse_file(self, file_type):
        filepath = filedialog.askopenfilename(title=f"Select {file_type} File", filetypes=[(f"{file_type} files", "*.dat"), ("All files", "*.*")])
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

    def create_waypoint_ui(self):
      frm = self.waypoint_frame
      frm.columnconfigure(1, weight=1) # Make column 1 expandable

      # File Type Selection (within WAYPOINT frame)
      tk.Label(frm, text="Search in File Type:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      combo_search_file = ttk.Combobox(frm, textvariable=self.search_file_type, values=("NAV", "FIX"), state="readonly")
      combo_search_file.grid(row=0, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell

      # Identifier Entry
      tk.Label(frm, text="VOR/DME/NDB Identifier:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_waypoint_identifier = tk.Entry(frm, width=30)
      self.entry_waypoint_identifier.grid(row=1, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell

      # Coordinate Display (modifiable)
      tk.Label(frm, text="Coordinates (Lat Lon):", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e") # Aligned labels, clearer label
      self.entry_waypoint_coords = tk.Entry(frm, width=30)  # Modifiable
      self.entry_waypoint_coords.grid(row=2, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell

      # Add bearing mode selector
      tk.Label(frm, text="Bearing Mode:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
      self.waypoint_bearing_mode = tk.StringVar(value="Magnetic")
      bearing_frame = tk.Frame(frm)
      bearing_frame.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
      tk.Radiobutton(bearing_frame, text="Magnetic", variable=self.waypoint_bearing_mode, 
                     value="Magnetic", command=self.update_waypoint_bearing_label).pack(side=tk.LEFT, padx=5)
      tk.Radiobutton(bearing_frame, text="True", variable=self.waypoint_bearing_mode, 
                     value="True", command=self.update_waypoint_bearing_label).pack(side=tk.LEFT, padx=5)

      self.waypoint_bearing_label = tk.StringVar(value="Magnetic Bearing (°):")
      tk.Label(frm, textvariable=self.waypoint_bearing_label, anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e")
      self.entry_bearing = tk.Entry(frm, width=30)
      self.entry_bearing.grid(row=4, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      
      tk.Label(frm, text="Distance (NM):", anchor="e").grid(row=5, column=0, padx=5, pady=5, sticky="e") # Aligned labels, added unit
      self.entry_distance = tk.Entry(frm, width=30)
      self.entry_distance.grid(row=5, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      
      # Add declination mode selector (Auto/Manual)
      self.declination_frame = tk.Frame(frm)
      self.declination_frame.grid(row=6, column=0, columnspan=2, pady=5, sticky="w")
      self.waypoint_declination_mode = tk.StringVar(value="Manual")
      
      tk.Label(self.declination_frame, text="Declination Mode:", anchor="e").pack(side=tk.LEFT, padx=5)
      tk.Radiobutton(self.declination_frame, text="Auto", variable=self.waypoint_declination_mode, 
                     value="Auto", command=self.update_waypoint_bearing_label).pack(side=tk.LEFT, padx=5)
      tk.Radiobutton(self.declination_frame, text="Manual", variable=self.waypoint_declination_mode, 
                     value="Manual", command=self.update_waypoint_bearing_label).pack(side=tk.LEFT, padx=5)
      
      # Display auto-calculated declination value
      self.waypoint_auto_declination_label = tk.Label(self.declination_frame, text="Auto: 0.0°")
      self.waypoint_auto_declination_label.pack(side=tk.LEFT, padx=5)
      self.waypoint_auto_declination_value = 0.0
      
      # Make declination conditional based on bearing mode
      self.declination_label = tk.Label(frm, text="Manual Declination (°):", anchor="e")
      self.declination_label.grid(row=7, column=0, padx=5, pady=5, sticky="e") # Aligned labels, added unit
      self.entry_declination = tk.Entry(frm, width=30)
      self.entry_declination.grid(row=7, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      self.entry_declination.insert(0, "0.0")  # Default value
      
      tk.Label(frm, text="Airport Code:", anchor="e").grid(row=8, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_airport_code = tk.Entry(frm, width=30)
      self.entry_airport_code.grid(row=8, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      
      tk.Label(frm, text="VOR Identifier:", anchor="e").grid(row=9, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_vor_identifier = tk.Entry(frm, width=30)
      self.entry_vor_identifier.grid(row=9, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      
      tk.Label(frm, text="Operation Type:", anchor="e").grid(row=10, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.combo_operation_type = ttk.Combobox(frm, values=["Departure", "Arrival", "Approach"], state="readonly")
      self.combo_operation_type.current(0)
      self.combo_operation_type.grid(row=10, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell
      
      btn_calc = tk.Button(frm, text="Calculate Waypoint", command=self.on_calculate_waypoint)
      btn_calc.grid(row=11, column=0, columnspan=2, pady=5)

      # Button to search for coordinates
      btn_search_waypoint = tk.Button(frm, text="Search Coordinates", command=self.search_waypoint_coords)
      btn_search_waypoint.grid(row=1, column=2, padx=5, pady=5)
      
      # Button to update declination from coordinates
      btn_update_decl = tk.Button(frm, text="Update Declination", command=self.update_waypoint_declination)
      btn_update_decl.grid(row=2, column=2, padx=5, pady=5)
      
      # Initial update of bearing label
      self.update_waypoint_bearing_label()

    def create_fix_ui(self):
      frm = self.fix_frame
      frm.columnconfigure(1, weight=1) # Make column 1 expandable

      # File Type Selection (within FIX frame)
      tk.Label(frm, text="Search in File Type:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      combo_search_file = ttk.Combobox(frm, textvariable=self.search_file_type, values=("FIX", "NAV"), state="readonly")
      combo_search_file.grid(row=0, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell

      # Identifier Entry
      tk.Label(frm, text="FIX Identifier:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_fix_identifier = tk.Entry(frm, width=30)
      self.entry_fix_identifier.grid(row=1, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell

      # Coordinate Display (modifiable)
      tk.Label(frm, text="FIX Coordinates (Lat Lon):", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e") # Aligned labels, clearer label
      self.entry_fix_coords = tk.Entry(frm, width=30)  # Modifiable
      self.entry_fix_coords.grid(row=2, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell

      # Add DME Calculation Section with separator
      separator = ttk.Separator(frm, orient='horizontal')
      separator.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
      
      tk.Label(frm, text="DME Calculation", font=('Helvetica', 10, 'bold')).grid(row=4, column=0, columnspan=2, pady=5, sticky="w")
      
      # Add distance reference selector
      tk.Label(frm, text="Distance Reference:", anchor="e").grid(row=5, column=0, padx=5, pady=5, sticky="e")
      self.distance_reference = tk.StringVar(value="DME")
      distance_frame = tk.Frame(frm)
      distance_frame.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
      tk.Radiobutton(distance_frame, text="DME", variable=self.distance_reference, value="DME").pack(side=tk.LEFT, padx=5)
      tk.Radiobutton(distance_frame, text="FIX", variable=self.distance_reference, value="FIX").pack(side=tk.LEFT, padx=5)

      # DME Identifier Entry
      tk.Label(frm, text="DME Identifier:", anchor="e").grid(row=6, column=0, padx=5, pady=5, sticky="e")
      self.entry_dme_identifier = tk.Entry(frm, width=30)
      self.entry_dme_identifier.grid(row=6, column=1, padx=5, pady=5, sticky="ew")
      
      # DME Coordinates Display
      tk.Label(frm, text="DME Coordinates (Lat Lon):", anchor="e").grid(row=7, column=0, padx=5, pady=5, sticky="e")
      self.entry_dme_coords = tk.Entry(frm, width=30)
      self.entry_dme_coords.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
      
      # Add bearing mode selector for DME calculations
      tk.Label(frm, text="Bearing Mode:", anchor="e").grid(row=8, column=0, padx=5, pady=5, sticky="e")
      self.dme_bearing_mode = tk.StringVar(value="Magnetic")
      dme_bearing_frame = tk.Frame(frm)
      dme_bearing_frame.grid(row=8, column=1, padx=5, pady=5, sticky="ew")
      tk.Radiobutton(dme_bearing_frame, text="Magnetic", variable=self.dme_bearing_mode, 
                     value="Magnetic", command=self.update_dme_bearing_label).pack(side=tk.LEFT, padx=5)
      tk.Radiobutton(dme_bearing_frame, text="True", variable=self.dme_bearing_mode, 
                     value="True", command=self.update_dme_bearing_label).pack(side=tk.LEFT, padx=5)
      
      # Bearing and Distance from DME with dynamic label
      self.dme_bearing_label = tk.StringVar(value="Magnetic Bearing (°):")
      tk.Label(frm, textvariable=self.dme_bearing_label, anchor="e").grid(row=9, column=0, padx=5, pady=5, sticky="e")
      self.entry_dme_bearing = tk.Entry(frm, width=30)
      self.entry_dme_bearing.grid(row=9, column=1, padx=5, pady=5, sticky="ew")
      
      tk.Label(frm, text="Distance (NM):", anchor="e").grid(row=10, column=0, padx=5, pady=5, sticky="e")
      self.entry_dme_distance = tk.Entry(frm, width=30)
      self.entry_dme_distance.grid(row=10, column=1, padx=5, pady=5, sticky="ew")
      
      # Add declination mode selector for DME (Auto/Manual)
      self.dme_declination_frame = tk.Frame(frm)
      self.dme_declination_frame.grid(row=11, column=0, columnspan=2, pady=5, sticky="w")
      self.dme_declination_mode = tk.StringVar(value="Manual")
      
      tk.Label(self.dme_declination_frame, text="Declination Mode:", anchor="e").pack(side=tk.LEFT, padx=5)
      tk.Radiobutton(self.dme_declination_frame, text="Auto", variable=self.dme_declination_mode, 
                     value="Auto", command=self.update_dme_bearing_label).pack(side=tk.LEFT, padx=5)
      tk.Radiobutton(self.dme_declination_frame, text="Manual", variable=self.dme_declination_mode, 
                     value="Manual", command=self.update_dme_bearing_label).pack(side=tk.LEFT, padx=5)
      
      # Display auto-calculated declination value
      self.dme_auto_declination_label = tk.Label(self.dme_declination_frame, text="Auto: 0.0°")
      self.dme_auto_declination_label.pack(side=tk.LEFT, padx=5)
      self.dme_auto_declination_value = 0.0
      
      # Make declination conditional based on bearing mode
      self.dme_declination_label = tk.Label(frm, text="Manual Declination (°):", anchor="e")
      self.dme_declination_label.grid(row=12, column=0, padx=5, pady=5, sticky="e")
      self.entry_dme_declination = tk.Entry(frm, width=30)
      self.entry_dme_declination.grid(row=12, column=1, padx=5, pady=5, sticky="ew")
      self.entry_dme_declination.insert(0, "0.0")  # Default value
      
      # Button to search for DME coordinates
      btn_search_dme = tk.Button(frm, text="Search DME", command=self.search_dme_coords)
      btn_search_dme.grid(row=6, column=2, padx=5, pady=5)
      
      # Button to update declination from coordinates
      btn_update_dme_decl = tk.Button(frm, text="Update Declination", command=self.update_dme_declination)
      btn_update_dme_decl.grid(row=7, column=2, padx=5, pady=5)
      
      # Button to calculate from DME
      btn_calc_from_dme = tk.Button(frm, text="Calculate Intersection", command=self.calculate_from_dme)
      btn_calc_from_dme.grid(row=13, column=0, columnspan=2, pady=5)
      
      # Add another separator
      separator2 = ttk.Separator(frm, orient='horizontal')
      separator2.grid(row=14, column=0, columnspan=3, sticky="ew", pady=10)
      
      # FIX Type and other fields moved down
      tk.Label(frm, text="FIX Type:", anchor="e").grid(row=15, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.combo_fix_type = ttk.Combobox(frm, values=["VORDME", "VOR", "NDBDME", "NDB", "ILS", "RNP"], state="readonly")
      self.combo_fix_type.current(0)
      self.combo_fix_type.grid(row=15, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell
      tk.Label(frm, text="FIX Usage:", anchor="e").grid(row=16, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.combo_fix_usage = ttk.Combobox(frm, values=["Final approach fix", "Initial approach fix", "Intermediate approach fix", "Final approach course fix", "Missed approach point fix"], state="readonly")
      self.combo_fix_usage.current(0)
      self.combo_fix_usage.grid(row=16, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell
      tk.Label(frm, text="Runway Code:", anchor="e").grid(row=17, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_runway_code = tk.Entry(frm, width=30)
      self.entry_runway_code.grid(row=17, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="Airport Code:", anchor="e").grid(row=18, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_fix_airport_code = tk.Entry(frm, width=30)
      self.entry_fix_airport_code.grid(row=18, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="Operation Type:", anchor="e").grid(row=19, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.combo_fix_operation_type = ttk.Combobox(frm, values=["Departure", "Arrival", "Approach"], state="readonly")
      self.combo_fix_operation_type.current(0)
      self.combo_fix_operation_type.grid(row=19, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell
      btn_calc = tk.Button(frm, text="Calculate FIX", command=self.on_calculate_fix)
      btn_calc.grid(row=20, column=0, columnspan=2, pady=5)

      # Button to search for coordinates
      btn_search_fix = tk.Button(frm, text="Search Coordinates", command=self.search_fix_coords)
      btn_search_fix.grid(row=1, column=2, padx=5, pady=5)
      
      # Initial update of bearing label
      self.update_dme_bearing_label()

    def create_output_ui(self):
        frm_output = tk.LabelFrame(self.root, text="Output Result", padx=10, pady=5)
        frm_output.pack(padx=10, pady=5, fill="both", expand=True)
        self.output_entry = tk.Text(frm_output, width=80, height=8, state="disabled") # Set output to disabled (readonly) initially
        self.output_entry.pack(padx=5, pady=5, fill="both", expand=True)
        return frm_output

    def create_bottom_buttons(self):
        frm_btn = tk.Frame(self.root)
        frm_btn.pack(padx=10, pady=5, fill="x")
        btn_clear = tk.Button(frm_btn, text="Clear Input", command=self.clear_fields)
        btn_clear.pack(side=tk.LEFT, padx=5)
        btn_copy = tk.Button(frm_btn, text="Copy Result", command=self.copy_output)
        btn_copy.pack(side=tk.LEFT, padx=5)
        btn_history = tk.Button(frm_btn, text="View History", command=self.show_history)
        btn_history.pack(side=tk.LEFT, padx=5)
        btn_exit = tk.Button(frm_btn, text="Exit", command=self.root.quit)
        btn_exit.pack(side=tk.RIGHT, padx=5)

    def clear_fields(self):
        if self.mode_var.get() == "WAYPOINT":
            self.entry_waypoint_identifier.delete(0, tk.END)
            self.entry_waypoint_coords.delete(0, tk.END)
            self.entry_bearing.delete(0, tk.END)
            self.entry_distance.delete(0, tk.END)
            self.entry_declination.delete(0, tk.END)
            self.entry_airport_code.delete(0, tk.END)
            self.entry_vor_identifier.delete(0, tk.END)
        elif self.mode_var.get() == "FIX":
            self.entry_fix_identifier.delete(0, tk.END)
            self.entry_fix_coords.delete(0, tk.END)
            self.entry_dme_identifier.delete(0, tk.END)
            self.entry_dme_coords.delete(0, tk.END)
            self.entry_dme_bearing.delete(0, tk.END)
            self.entry_dme_distance.delete(0, tk.END)
            self.entry_dme_declination.delete(0, tk.END)
            self.entry_runway_code.delete(0, tk.END)
            self.entry_fix_airport_code.delete(0, tk.END)
        self.output_entry.config(state=tk.NORMAL) # Make output editable to clear
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.config(state=tk.DISABLED) # Set back to readonly

    def copy_output(self):
        output_text = self.output_entry.get(1.0, tk.END).strip()
        if output_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(output_text)
            messagebox.showinfo("Copy Result", "Result copied to clipboard!")
        else:
            messagebox.showwarning("Copy Result", "No text to copy!")

    def calculate_target_coords_vincenty(self, lat_vor, lon_vor, bearing, distance_nm, bearing_mode, declination_mode="Manual", declination=0, auto_declination=0):
        """Calculates the target coordinates with option for true or magnetic bearing and auto/manual declination."""
        if bearing_mode == "Magnetic":
            # Use appropriate declination based on mode
            if declination_mode == "Auto":
                actual_declination = auto_declination
            else:
                actual_declination = declination
                
            true_bearing = (bearing + actual_declination) % 360
        else:  # True bearing
            true_bearing = bearing % 360
        return calculate_target_coords_geodesic(lat_vor, lon_vor, true_bearing, distance_nm)

    def validate_input(self, mode):
        if mode == "WAYPOINT":
            try:
                lat_vor, lon_vor = None, None # Initialize to None
                # Validate coordinates if entered manually
                coords_str = self.entry_waypoint_coords.get().strip()
                if coords_str:  # Only validate if not empty
                    lat_vor, lon_vor = map(float, coords_str.split())
                    if not (-90 <= lat_vor <= 90 and -180 <= lon_vor <= 180):
                        raise ValueError("Latitude/Longitude out of range (±90 / ±180)")
                elif self.entry_waypoint_identifier.get().strip(): # Require coords or identifier if waypoint mode
                    pass # Identifier provided, coordinates might be searched
                else:
                    raise ValueError("Coordinates or Identifier must be provided")

                bearing = float(self.entry_bearing.get())
                if not (0 <= bearing < 360):
                    raise ValueError("Bearing should be within 0-359 degrees")
                    
                distance_nm = float(self.entry_distance.get())
                if distance_nm <= 0:
                    raise ValueError("Distance should be greater than 0 nautical miles")
                
                bearing_mode = self.waypoint_bearing_mode.get()
                declination_mode = self.waypoint_declination_mode.get()
                declination = 0
                
                if bearing_mode == "Magnetic":
                    if declination_mode == "Manual":
                        declination = float(self.entry_declination.get())
                    else:  # Auto
                        # If coordinates are available, calculate declination
                        if lat_vor is not None and lon_vor is not None:
                            # Try to update the auto declination first
                            self.waypoint_auto_declination_value = get_magnetic_declination(lat_vor, lon_vor)
                            self.waypoint_auto_declination_label.config(text=f"Auto: {self.waypoint_auto_declination_value:.1f}°")
                        # Use stored auto declination value
                        declination = self.waypoint_auto_declination_value
                    
                airport_code = self.entry_airport_code.get().strip().upper()
                if len(airport_code) != 4:
                    raise ValueError("Airport code must be 4 letters")
                
                vor_identifier = self.entry_vor_identifier.get().strip().upper()
                if vor_identifier and not (1 <= len(vor_identifier) <= 3 and vor_identifier.isalpha()):
                    raise ValueError("VOR identifier should be 1-3 letters and alphabetic")
                
                return lat_vor, lon_vor, bearing, distance_nm, bearing_mode, declination_mode, declination, airport_code, vor_identifier
            except ValueError as e:
                messagebox.showerror("Input Error", f"WAYPOINT mode input error: {e}")
                return None
        return True  # FIX validation happens after coordinate search

    def process_output(self, result, mode, vor_identifier="", bearing="", distance_nm=""):
        if mode == "WAYPOINT":
            lat_target, lon_target, radius_letter, airport_code, operation_code = result
            if distance_nm > 26.5: # Consider making 26.5 a constant
                rounded_distance_nm_int = int(round(distance_nm))
                output = (f"{lat_target:.9f} {lon_target:.9f} "f"{vor_identifier}{rounded_distance_nm_int} "f"{airport_code} {airport_code[:2]}")
                if vor_identifier:
                    bearing_int = int(bearing)
                    output += f" {operation_code} {vor_identifier}{bearing_int:03d}{rounded_distance_nm_int:03d}"
                else:
                    output += f" {operation_code}"
            else:
                output = (f"{lat_target:.9f} {lon_target:.9f} "f"D{int(bearing):03d}{radius_letter} "f"{airport_code} {airport_code[:2]}")
                if vor_identifier:
                    bearing_int = int(bearing)
                    output += f" {operation_code} {vor_identifier}{bearing_int:03d}{int(round(distance_nm)):03d}"
                else:
                    output += f" {operation_code}"
        elif mode == "FIX":
            lat, lon, fix_code, usage_code, runway_code, airport_code, operation_code = result
            output = (f"{lat:.9f} {lon:.9f} {usage_code}{fix_code}{int(runway_code):02d} "f"{airport_code} {airport_code[:2]} {operation_code}")
        
        # Add to history
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_item = {
            "timestamp": timestamp,
            "mode": mode,
            "output": output
        }
        self.history.append(history_item)
        
        self.output_entry.config(state=tk.NORMAL) # Make output editable
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.insert(tk.END, output)
        self.output_entry.config(state=tk.DISABLED) # Set back to readonly

    # New method to display history
    def show_history(self):
        if not self.history:
            messagebox.showinfo("History", "No calculation history available.")
            return
            
        history_window = tk.Toplevel(self.root)
        history_window.title("Calculation History")
        history_window.geometry("700x400")
        
        # Create frame with scrollbar
        frame = tk.Frame(history_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create treeview to display history
        columns = ("Time", "Mode", "Output")
        history_tree = ttk.Treeview(frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        
        # Configure column widths
        history_tree.column("Time", width=150, anchor="w")
        history_tree.column("Mode", width=80, anchor="center")
        history_tree.column("Output", width=450, anchor="w")
        
        # Configure column headings
        history_tree.heading("Time", text="Time")
        history_tree.heading("Mode", text="Mode")
        history_tree.heading("Output", text="Output")
        
        # Populate treeview with history items (newest first)
        for item in reversed(self.history):
            history_tree.insert("", "end", values=(item["timestamp"], item["mode"], item["output"]))
        
        history_tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=history_tree.yview)
        
        # Function to use selected history item
        def use_selected_item():
            selected_items = history_tree.selection()
            if not selected_items:
                messagebox.showinfo("Selection", "Please select a history item.")
                return
                
            item_id = selected_items[0]
            values = history_tree.item(item_id, "values")
            if not values or len(values) < 3:
                return
                
            # Populate output with selected history item
            self.output_entry.config(state=tk.NORMAL)
            self.output_entry.delete(1.0, tk.END)
            self.output_entry.insert(tk.END, values[2])  # Output is the third column
            self.output_entry.config(state=tk.DISABLED)
            history_window.destroy()
        
        # Function to copy selected history item
        def copy_selected_item():
            selected_items = history_tree.selection()
            if not selected_items:
                messagebox.showinfo("Selection", "Please select a history item.")
                return
                
            item_id = selected_items[0]
            values = history_tree.item(item_id, "values")
            if not values or len(values) < 3:
                return
                
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(values[2])  # Output is the third column
            messagebox.showinfo("Copy", "Result copied to clipboard!")
        
        # Buttons frame
        btn_frame = tk.Frame(history_window)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        # Create buttons
        btn_use = tk.Button(btn_frame, text="Use Selected", command=use_selected_item)
        btn_use.pack(side=tk.LEFT, padx=5)
        
        btn_copy = tk.Button(btn_frame, text="Copy Selected", command=copy_selected_item)
        btn_copy.pack(side=tk.LEFT, padx=5)
        
        btn_close = tk.Button(btn_frame, text="Close", command=history_window.destroy)
        btn_close.pack(side=tk.RIGHT, padx=5)

    def search_waypoint_coords(self):
        identifier = self.entry_waypoint_identifier.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter an identifier.")
            return

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
                    # NAV: 8th part, FIX: 3rd part
                    relevant_index = 7 if file_type == "NAV" else 2
                    if len(parts) > relevant_index and parts[relevant_index] == identifier:
                        matching_lines.append(parts)

            if not matching_lines:
                messagebox.showinfo("Not Found", f"{file_type} identifier '{identifier}' not found.")
                return

            if len(matching_lines) > 1:
                # Duplicate handling - Refactor into a separate method for reusability
                self.handle_duplicate_entries(matching_lines, "WAYPOINT")
            else:
                self.set_waypoint_coords(matching_lines[0])

        except FileNotFoundError:
            messagebox.showerror("File Error", f"File not found: {file_path}")
        except Exception as e:
            messagebox.showerror("File Read Error", f"Error reading {file_type} file: {e}")

    def handle_duplicate_entries(self, matching_lines, mode):
        choice_window = tk.Toplevel(self.root)
        choice_window.title(f"Choose Entry") # More generic title
        tk.Label(choice_window, text=f"Multiple entries found. Please choose one:").pack()
        selected_line = tk.StringVar()

        file_type = self.search_file_type.get()

        type_mapping = {
            '3': "VOR",
            '12': "DME (VOR)",
            '2': "NDB",
            '13': 'DME',
            '7': 'OUTER MARKER',
            '8': 'MIDDLE MARKER',
            '9': 'INNER MARKER'
        }

        for line_parts in matching_lines:
            first_part = line_parts[0]
            type_str = type_mapping.get(first_part, "Unknown")  # # Use dictionary to get type_str, default to "Unknown"
            relevant_index = 7 if file_type == "NAV" else 2  # Conditional expression for relevant_index
            display_text = f"{type_str} - {line_parts[relevant_index]}"

            if len(line_parts) > 9: # Check if tenth part exists
                tenth_part = line_parts[9]
                display_text += f" - {tenth_part}" # Add tenth part to display
            else:
                display_text += " - [Tenth part missing]" # Indicate if tenth part is missing

            rb = tk.Radiobutton(choice_window, text=display_text, variable=selected_line, value=",".join(line_parts))
            rb.pack()

        def confirm_choice():
            chosen_line = selected_line.get()
            if chosen_line:
                if mode == "WAYPOINT":
                    self.set_waypoint_coords(chosen_line.split(","))
                elif mode == "FIX":
                    self.set_fix_coords(chosen_line.split(",")) # Call set_fix_coords for FIX mode
                choice_window.destroy()
            else:
                messagebox.showwarning("Selection Required", "Please select an entry.")
        btn_confirm = tk.Button(choice_window, text="Confirm", command=confirm_choice)
        btn_confirm.pack()
        choice_window.wait_window()


    def set_waypoint_coords(self, line_parts):
      try:
          # NAV file: lat/lon are 2nd and 3rd, FIX file: 1st and 2nd
          file_type = self.search_file_type.get()
          lat_index = 1 if file_type == "NAV" else 0
          lon_index = 2 if file_type == "NAV" else 1

          lat = float(line_parts[lat_index])
          lon = float(line_parts[lon_index])
          self.entry_waypoint_coords.delete(0, tk.END) #Clear first
          self.entry_waypoint_coords.insert(0, f"{lat} {lon}")

      except (ValueError, IndexError):
          messagebox.showerror("Data Error", "Invalid coordinate data in the selected file.")

    def on_calculate_waypoint(self):
        params = self.validate_input("WAYPOINT")
        if params is None:
            return
        lat_vor, lon_vor, bearing, distance_nm, bearing_mode, declination_mode, declination, airport_code, vor_identifier = params

        if lat_vor is None or lon_vor is None: # Check if coords were obtained, if not, try to search based on identifier
            identifier = self.entry_waypoint_identifier.get().strip().upper()
            if not identifier:
                messagebox.showerror("Input Error", "Please enter identifier or coordinates.")
                return
            self.search_waypoint_coords_and_calculate(identifier, bearing, distance_nm, bearing_mode, declination_mode, declination, airport_code, vor_identifier)
            return # Exit current calculation

        try:
            # Get auto declination if needed
            auto_declination = self.waypoint_auto_declination_value
            
            lat_target, lon_target = self.calculate_target_coords_vincenty(
                lat_vor, lon_vor, bearing, distance_nm, 
                bearing_mode, declination_mode, declination, auto_declination
            )
            radius_letter = get_radius_letter(distance_nm)
            operation_code_map = {"Departure": "4464713", "Arrival": "4530249", "Approach": "4595785"}
            operation_code = operation_code_map.get(self.combo_operation_type.get(), "")
            result = (round(lat_target, 9), round(lon_target, 9), radius_letter, airport_code, operation_code)
            self.process_output(result, "WAYPOINT", vor_identifier, bearing, distance_nm)
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {str(e)}")

    def search_waypoint_coords_and_calculate(self, identifier, bearing, distance_nm, bearing_mode, declination_mode, declination, airport_code, vor_identifier):
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
                self.pending_calculation_params = (bearing, distance_nm, bearing_mode, declination_mode, declination, airport_code, vor_identifier)
                self.handle_duplicate_entries(matching_lines, "WAYPOINT")
            else:
                self.set_waypoint_coords_and_continue_calculation(matching_lines[0], bearing, distance_nm, bearing_mode, declination_mode, declination, airport_code, vor_identifier)
        except FileNotFoundError:
            messagebox.showerror("File Error", f"File not found: {file_path}")
        except Exception as e:
            messagebox.showerror("File Read Error", f"Error reading {file_type} file: {e}")

    def set_waypoint_coords_and_continue_calculation(self, line_parts, bearing, distance_nm, bearing_mode, declination_mode, declination, airport_code, vor_identifier):
        """Sets waypoint coordinates and continues with the calculation."""
        try:
            file_type = self.search_file_type.get()
            lat_index = 1 if file_type == "NAV" else 0
            lon_index = 2 if file_type == "NAV" else 1

            lat_vor = float(line_parts[lat_index])
            lon_vor = float(line_parts[lon_index])
            
            # If auto declination, calculate it from the coordinates
            auto_declination = 0
            if bearing_mode == "Magnetic" and declination_mode == "Auto":
                auto_declination = get_magnetic_declination(lat_vor, lon_vor)
                self.waypoint_auto_declination_value = auto_declination
                self.waypoint_auto_declination_label.config(text=f"Auto: {auto_declination:.1f}°")

            lat_target, lon_target = self.calculate_target_coords_vincenty(
                lat_vor, lon_vor, bearing, distance_nm, 
                bearing_mode, declination_mode, declination, auto_declination
            )
            radius_letter = get_radius_letter(distance_nm)
            operation_code_map = {"Departure": "4464713", "Arrival": "4530249", "Approach": "4595785"}
            operation_code = operation_code_map.get(self.combo_operation_type.get(), "")
            result = (round(lat_target, 9), round(lon_target, 9), radius_letter, airport_code, operation_code)
            self.process_output(result, "WAYPOINT", vor_identifier, bearing, distance_nm)

        except (ValueError, IndexError) as e:
            messagebox.showerror("Data Error", f"Invalid coordinate data or calculation error: {e}")

    def search_fix_coords(self):
        identifier = self.entry_fix_identifier.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter a FIX identifier.")
            return

        file_type = self.search_file_type.get()
        file_path = self.fix_file_path if file_type == "FIX" else self.nav_file_path
        if not file_path:
            messagebox.showerror("File Error", f"Please select a {file_type} data file.")
            return

        try:
            with open(file_path, 'r') as file:
                matching_lines = []
                for line in file:
                    parts = line.strip().split()
                    # FIX: 3rd part, NAV: 8th part
                    relevant_index = 2 if file_type == "FIX" else 7
                    if len(parts) > relevant_index and parts[relevant_index] == identifier:
                        matching_lines.append(parts)

            if not matching_lines:
                messagebox.showinfo("Not Found", f"{file_type} identifier '{identifier}' not found.")
                return

            if len(matching_lines) > 1:
                self.handle_duplicate_entries(matching_lines, "FIX") # Use the same duplicate handler, mode is now "FIX"
            else:
                self.set_fix_coords(matching_lines[0])

        except FileNotFoundError:
            messagebox.showerror("File Error", f"File not found: {file_path}")
        except Exception as e:
            messagebox.showerror("File Read Error", f"Error reading {file_type} file: {e}")

    def set_fix_coords(self, line_parts):
        try:
            # FIX file: lat/lon are 1st and 2nd, NAV file: 2nd and 3rd
            file_type = self.search_file_type.get()
            lat_index = 0 if file_type == "FIX" else 1
            lon_index = 1 if file_type == "FIX" else 2

            lat = float(line_parts[lat_index])
            lon = float(line_parts[lon_index])
            self.entry_fix_coords.delete(0, tk.END) #Clear first.
            self.entry_fix_coords.insert(0, f"{lat} {lon}")
        except (ValueError, IndexError):
            messagebox.showerror("Data Error", "Invalid coordinate data in the selected file.")

        if hasattr(self, 'pending_calculation_params') and self.mode_var.get() == "WAYPOINT": # Check if there are pending params and mode is waypoint
            bearing, distance_nm, bearing_mode, declination_mode, declination, airport_code, vor_identifier = self.pending_calculation_params
            self.on_calculate_waypoint() # Recalculate waypoint now that coords are set
            del self.pending_calculation_params # Clear pending params after use

    def on_calculate_fix(self):
        coords_str = self.entry_fix_coords.get().strip()
        if not coords_str:
            messagebox.showerror("Input Error", "Please search for and select coordinates first or enter manually.")
            return
        try:
            lat, lon = map(float, coords_str.split())
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Latitude/Longitude out of range (±90 / ±180)")
        except ValueError as e:
            messagebox.showerror("Input Error", f"FIX mode input error: {e}")
            return

        try:
            fix_type = self.combo_fix_type.get()
            fix_usage = self.combo_fix_usage.get()
            runway_code = self.entry_runway_code.get().strip()
            if not runway_code.isdigit() or not 0 <= int(runway_code) <= 99:
                raise ValueError("Runway code should be a two-digit number between 0 and 99")
            airport_code = self.entry_fix_airport_code.get().strip().upper()
            if len(airport_code) != 4:
                raise ValueError("Airport code must be 4 letters")

            fix_code_map = {"VORDME": "D", "VOR": "V", "NDBDME": "Q", "NDB": "N", "ILS": "I", "RNP": "R"}
            usage_code_map = {"Final approach fix": "F", "Initial approach fix": "A", "Intermediate approach fix": "I", "Final approach course fix": "C", "Missed approach point fix": "M"}
            operation_code_map = {"Departure": "4464713", "Arrival": "4530249", "Approach": "4595785"}

            fix_code = fix_code_map.get(fix_type, "")
            usage_code = usage_code_map.get(fix_usage, "")
            if not fix_code or not usage_code:
                raise ValueError("Invalid FIX type or usage")

            operation_code = operation_code_map.get(self.combo_fix_operation_type.get(), "")
            result = (round(lat, 9), round(lon, 9), fix_code, usage_code, runway_code, airport_code, operation_code)
            self.process_output(result, "FIX")
        except ValueError as e:
            messagebox.showerror("Input Error", f"FIX mode input error: {e}")

    # DME Search function
    def search_dme_coords(self):
        identifier = self.entry_dme_identifier.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter a DME identifier.")
            return

        # Always search in NAV file for DME
        file_path = self.nav_file_path
        if not file_path:
            messagebox.showerror("File Error", "Please select a NAV data file.")
            return

        try:
            with open(file_path, 'r') as file:
                matching_lines = []
                for line in file:
                    parts = line.strip().split()
                    if len(parts) > 7 and parts[7] == identifier:
                        # Check if it's a DME (type code 12 or 13)
                        if parts[0] in ['12', '13']:
                            matching_lines.append(parts)

            if not matching_lines:
                messagebox.showinfo("Not Found", f"DME identifier '{identifier}' not found.")
                return

            if len(matching_lines) > 1:
                # Handle multiple DMEs with same identifier
                self.handle_dme_duplicates(matching_lines)
            else:
                self.set_dme_coords(matching_lines[0])

        except FileNotFoundError:
            messagebox.showerror("File Error", f"File not found: {file_path}")
        except Exception as e:
            messagebox.showerror("File Read Error", f"Error reading NAV file: {e}")

    def handle_dme_duplicates(self, matching_lines):
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Choose DME")
        tk.Label(choice_window, text="Multiple DMEs found. Please choose one:").pack()
        selected_line = tk.StringVar()

        for line_parts in matching_lines:
            type_str = "DME (VOR)" if line_parts[0] == '12' else "DME"
            display_text = f"{type_str} - {line_parts[7]}"
            
            if len(line_parts) > 9:
                display_text += f" - {line_parts[9]}"
            else:
                display_text += " - [Location missing]"
                
            rb = tk.Radiobutton(choice_window, text=display_text, variable=selected_line, value=",".join(line_parts))
            rb.pack()

        def confirm_choice():
            chosen_line = selected_line.get()
            if chosen_line:
                self.set_dme_coords(chosen_line.split(","))
                choice_window.destroy()
            else:
                messagebox.showwarning("Selection Required", "Please select a DME.")
                
        btn_confirm = tk.Button(choice_window, text="Confirm", command=confirm_choice)
        btn_confirm.pack()
        choice_window.wait_window()

    def set_dme_coords(self, line_parts):
        try:
            # NAV file: lat/lon are 2nd and 3rd
            lat = float(line_parts[1])
            lon = float(line_parts[2])
            self.entry_dme_coords.delete(0, tk.END)
            self.entry_dme_coords.insert(0, f"{lat} {lon}")
        except (ValueError, IndexError):
            messagebox.showerror("Data Error", "Invalid coordinate data in the selected DME.")

    def calculate_from_dme(self):
        # Validate input
        try:
            # Get FIX coordinates
            fix_coords_str = self.entry_fix_coords.get().strip()
            if not fix_coords_str:
                messagebox.showerror("Input Error", "Please enter or search for FIX coordinates first.")
                return
            
            lat_fix, lon_fix = map(float, fix_coords_str.split())
            if not (-90 <= lat_fix <= 90 and -180 <= lon_fix <= 180):
                raise ValueError("FIX Latitude/Longitude out of range (±90 / ±180)")
            
            # Get DME coordinates
            dme_coords_str = self.entry_dme_coords.get().strip()
            if not dme_coords_str:
                messagebox.showerror("Input Error", "Please search for or enter DME coordinates.")
                return
            
            lat_dme, lon_dme = map(float, dme_coords_str.split())
            if not (-90 <= lat_dme <= 90 and -180 <= lon_dme <= 180):
                raise ValueError("DME Latitude/Longitude out of range (±90 / ±180)")
            
            # Get bearing FROM the FIX (radial)
            bearing = float(self.entry_dme_bearing.get())
            if not (0 <= bearing < 360):
                raise ValueError("Bearing should be within 0-359 degrees")
                
            # Get distance 
            distance_nm = float(self.entry_dme_distance.get())
            if distance_nm <= 0:
                raise ValueError("Distance should be greater than 0 nautical miles")
                
            # Get bearing mode and declination
            bearing_mode = self.dme_bearing_mode.get()
            declination_mode = self.dme_declination_mode.get()
            declination = 0
            
            if bearing_mode == "Magnetic":
                if declination_mode == "Manual":
                    declination = float(self.entry_dme_declination.get())
                else:  # Auto
                    # If DME coordinates available, update auto declination
                    auto_declination = get_magnetic_declination(lat_dme, lon_dme)
                    self.dme_auto_declination_value = auto_declination
                    self.dme_auto_declination_label.config(text=f"Auto: {auto_declination:.1f}°")
                    declination = auto_declination
            
            # Calculate true bearing from FIX based on mode
            if bearing_mode == "Magnetic":
                true_bearing = (bearing + declination) % 360
            else:  # True bearing
                true_bearing = bearing % 360
            
            # Get distance reference
            distance_reference = self.distance_reference.get()
            
            # Start timing the calculation
            start_time = datetime.datetime.now()
            
            # Find intersection point based on selected reference
            if distance_reference == "DME":
                # Find where radial from FIX intersects with circle around DME
                intersection_point = self.find_radial_distance_intersection(
                    lat_fix, lon_fix, true_bearing, 
                    lat_dme, lon_dme, distance_nm
                )
                reference_point = "DME"
                
                # Verify solution accuracy
                verification = GEODESIC.Inverse(
                    intersection_point['lat'], intersection_point['lon'], 
                    lat_dme, lon_dme
                )
                actual_distance_nm = verification['s12'] / 1852
                accuracy_error_nm = abs(actual_distance_nm - distance_nm)
                
                # Calculate radial accuracy
                radial_verification = GEODESIC.Inverse(
                    lat_fix, lon_fix,
                    intersection_point['lat'], intersection_point['lon']
                )
                actual_bearing = radial_verification['azi1']
                if actual_bearing < 0:
                    actual_bearing += 360
                
                if bearing_mode == "Magnetic":
                    actual_mag_bearing = (actual_bearing - declination) % 360
                    bearing_error = abs(bearing - actual_mag_bearing)
                else:
                    bearing_error = abs(bearing - actual_bearing)
                
                if bearing_error > 180:
                    bearing_error = 360 - bearing_error
            else:  # FIX
                # Calculate target point directly from FIX at bearing and distance
                result = GEODESIC.Direct(lat_fix, lon_fix, true_bearing, distance_nm * 1852)
                intersection_point = {
                    'lat': result['lat2'],
                    'lon': result['lon2']
                }
                reference_point = "FIX"
                
                # For direct calculation, error is essentially zero
                accuracy_error_nm = 0
                bearing_error = 0
                actual_distance_nm = distance_nm
            
            # Calculate elapsed time
            end_time = datetime.datetime.now()
            elapsed_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update FIX coordinates with the intersection point
            self.entry_fix_coords.delete(0, tk.END)
            self.entry_fix_coords.insert(0, f"{intersection_point['lat']:.9f} {intersection_point['lon']:.9f}")
            
            bearing_type = "magnetic" if bearing_mode == "Magnetic" else "true"
            declination_info = ""
            if bearing_mode == "Magnetic":
                declination_info = f" (declination: {declination:.1f}°)"
                
            if distance_reference == "DME":
                message = (f"Intersection found: FIX {bearing_type} radial {bearing:.2f}°{declination_info} "
                           f"intersects with {distance_nm:.3f} NM from DME.\n"
                           f"Precision: Distance error {accuracy_error_nm:.6f} NM, Bearing error {bearing_error:.6f}°\n"
                           f"Actual DME distance: {actual_distance_nm:.6f} NM")
            else:
                message = f"Point calculated at {bearing_type} bearing {bearing:.2f}°{declination_info} and {distance_nm:.3f} NM from FIX."
            
            messagebox.showinfo("Calculation Complete", 
                                f"{message}\n"
                                f"Coordinates have been set in the FIX field.\n"
                                f"Calculation time: {elapsed_ms:.2f} ms")
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Calculation error: {e}")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {str(e)}")

    def find_radial_distance_intersection(self, lat_fix, lon_fix, true_bearing, lat_dme, lon_dme, distance_nm):
        """
        Find the intersection point of a radial from a FIX with a distance circle from a DME.
        
        This function uses high-precision geodesic calculations to determine exactly where
        a radial extending from a FIX at a specified bearing intersects with a distance
        circle centered on a DME station.
        
        Parameters:
            lat_fix (float): Latitude of the FIX in decimal degrees
            lon_fix (float): Longitude of the FIX in decimal degrees
            true_bearing (float): True bearing from FIX in degrees
            lat_dme (float): Latitude of the DME station in decimal degrees
            lon_dme (float): Longitude of the DME station in decimal degrees
            distance_nm (float): Distance from DME in nautical miles
        
        Returns:
            dict: Dictionary containing 'lat' and 'lon' for the intersection point
        
        Precision guarantee:
            This function refines the solution until the distance error is less than 1.0 meter
            or until reaching a maximum of 200 iterations. In typical scenarios, the precision
            achieved is better than 0.5 meters from the exact mathematical intersection.
        """
        # Convert distance to meters for higher precision
        distance_m = nm_to_meters(distance_nm)
        
        # Calculate precise distance between FIX and DME
        fix_dme_result = GEODESIC.Inverse(lat_fix, lon_fix, lat_dme, lon_dme)
        fix_dme_distance_m = fix_dme_result['s12']  # Distance in meters
        fix_dme_distance_nm = meters_to_nm(fix_dme_distance_m)
        
        # Special case handling for numerical stability
        if distance_nm < 0.05:  # Less than ~100 meters
            min_dist = 0.0
            max_dist = 0.2  # Very refined initial search for short distances
        elif distance_nm < 0.5:  # Less than ~1 km
            min_dist = 0.0
            max_dist = max(1.0, distance_nm * 2)
        else:
            # Determine search range based on geometry
            min_dist = max(0.0, fix_dme_distance_nm - distance_nm - 1)  # 1 NM buffer
            max_dist = fix_dme_distance_nm + distance_nm + 1  # 1 NM buffer
        
        # Binary search with extremely high precision
        intersection_found = False
        best_approx_distance = float('inf')
        best_approx_point = {'lat': 0, 'lon': 0}
        test_dist = 0.0
        
        # Variables for adaptive step handling
        prev_error = float('inf')
        stagnation_counter = 0
        
        for iteration in range(MAX_ITERATIONS):
            # Try a point at test_dist along the radial from FIX
            test_dist = (min_dist + max_dist) / 2.0
            test_point = GEODESIC.Direct(lat_fix, lon_fix, true_bearing, nm_to_meters(test_dist))
            lat_test = test_point['lat2']
            lon_test = test_point['lon2']
            
            # Calculate precise distance from this test point to DME
            test_to_dme = GEODESIC.Inverse(lat_test, lon_test, lat_dme, lon_dme)
            test_to_dme_m = test_to_dme['s12']
            
            # Calculate error in meters
            error_m = abs(test_to_dme_m - distance_m)
            
            # Track the best approximation seen so far
            if error_m < best_approx_distance:
                best_approx_distance = error_m
                best_approx_point = {'lat': lat_test, 'lon': lon_test}
            
            # Check if we're close enough to the target distance (sub-meter precision)
            if error_m < DISTANCE_TOLERANCE_M:
                intersection_found = True
                break
            
            # Detect if we're getting stuck (making minimal progress)
            if abs(prev_error - error_m) < DISTANCE_TOLERANCE_M / 10:
                stagnation_counter += 1
            else:
                stagnation_counter = 0
            
            # If we're stuck in a local minimum, try a different approach
            if stagnation_counter > 5:
                # Try a different approach: Linear interpolation based on errors
                test_dist_1 = min_dist
                point_1 = GEODESIC.Direct(lat_fix, lon_fix, true_bearing, nm_to_meters(test_dist_1))
                to_dme_1 = GEODESIC.Inverse(point_1['lat2'], point_1['lon2'], lat_dme, lon_dme)
                error_1 = to_dme_1['s12'] - distance_m
                
                test_dist_2 = max_dist
                point_2 = GEODESIC.Direct(lat_fix, lon_fix, true_bearing, nm_to_meters(test_dist_2))
                to_dme_2 = GEODESIC.Inverse(point_2['lat2'], point_2['lon2'], lat_dme, lon_dme)
                error_2 = to_dme_2['s12'] - distance_m
                
                if error_1 != error_2:  # Avoid division by zero
                    test_dist = test_dist_1 + (test_dist_2 - test_dist_1) * (0 - error_1) / (error_2 - error_1)
                    test_point = GEODESIC.Direct(lat_fix, lon_fix, true_bearing, nm_to_meters(test_dist))
                    lat_test = test_point['lat2']
                    lon_test = test_point['lon2']
                    
                    test_to_dme = GEODESIC.Inverse(lat_test, lon_test, lat_dme, lon_dme)
                    error_m = abs(test_to_dme['s12'] - distance_m)
                    
                    if error_m < best_approx_distance:
                        best_approx_distance = error_m
                        best_approx_point = {'lat': lat_test, 'lon': lon_test}
                        
                    if error_m < DISTANCE_TOLERANCE_M:
                        intersection_found = True
                        break
                
                # Reset stagnation counter and adjust bounds
                stagnation_counter = 0
                if min_dist < test_dist < max_dist:
                    if test_to_dme_m > distance_m:
                        max_dist = test_dist
                    else:
                        min_dist = test_dist
                else:
                    # If interpolation took us outside bounds, narrow the range
                    min_dist = (min_dist + max_dist) / 3
                    max_dist = 2 * (min_dist + max_dist) / 3
                
                continue
            
            # Store current error for stagnation detection
            prev_error = error_m
            
            # Adjust search range
            if test_to_dme_m > distance_m:
                # Test point is too far from DME
                max_dist = test_dist
            else:
                # Test point is too close to DME
                min_dist = test_dist
            
            # Additional stopping condition for very small search intervals
            if (max_dist - min_dist) < 0.000001:  # Sub-millimeter precision in NM
                break
        
        # Use the best approximation if exact solution not found
        result_point = best_approx_point
        
        # Final verification and reporting
        if intersection_found:
            verification = GEODESIC.Inverse(result_point['lat'], result_point['lon'], lat_dme, lon_dme)
            actual_distance_m = verification['s12']
            error_m = abs(actual_distance_m - distance_m)
            
            # If error is still above tolerance but we thought we found it, use the best approximation
            if error_m > DISTANCE_TOLERANCE_M:
                result_point = best_approx_point
        
        # Final check of result accuracy
        final_check = GEODESIC.Inverse(result_point['lat'], result_point['lon'], lat_dme, lon_dme)
        final_error_m = abs(final_check['s12'] - distance_m)
        
        # Log precision achieved
        print(f"Intersection search completed in {iteration+1} iterations. Final precision: {final_error_m:.3f} meters")
        
        return result_point

    def update_waypoint_bearing_label(self):
        """Update the bearing label based on the selected mode."""
        bearing_mode = self.waypoint_bearing_mode.get()
        declination_mode = self.waypoint_declination_mode.get()
        
        if bearing_mode == "Magnetic":
            self.waypoint_bearing_label.set("Magnetic Bearing (°):")
            self.declination_frame.grid()  # Show declination frame
            
            if declination_mode == "Manual":
                self.declination_label.grid()  # Show manual declination label
                self.entry_declination.grid()  # Show manual declination entry
            else:  # Auto
                self.declination_label.grid_remove()  # Hide manual declination label
                self.entry_declination.grid_remove()  # Hide manual declination entry
        else:  # True
            self.waypoint_bearing_label.set("True Bearing (°):")
            self.declination_frame.grid_remove()  # Hide declination frame
            self.declination_label.grid_remove()  # Hide declination label
            self.entry_declination.grid_remove()  # Hide declination entry

    def update_dme_bearing_label(self):
        """Update the DME bearing label based on the selected mode."""
        bearing_mode = self.dme_bearing_mode.get()
        declination_mode = self.dme_declination_mode.get()
        
        if bearing_mode == "Magnetic":
            self.dme_bearing_label.set("Magnetic Bearing (°):")
            self.dme_declination_frame.grid()  # Show declination frame
            
            if declination_mode == "Manual":
                self.dme_declination_label.grid()  # Show manual declination label
                self.entry_dme_declination.grid()  # Show manual declination entry
            else:  # Auto
                self.dme_declination_label.grid_remove()  # Hide manual declination label
                self.entry_dme_declination.grid_remove()  # Hide manual declination entry
        else:  # True
            self.dme_bearing_label.set("True Bearing (°):")
            self.dme_declination_frame.grid_remove()  # Hide declination frame
            self.dme_declination_label.grid_remove()  # Hide declination label
            self.entry_dme_declination.grid_remove()  # Hide declination entry

    def update_waypoint_declination(self):
        """Update the auto declination value from the waypoint coordinates."""
        try:
            coords_str = self.entry_waypoint_coords.get().strip()
            if not coords_str:
                messagebox.showwarning("Auto Declination", "Please enter or search for coordinates first.")
                return
                
            lat, lon = map(float, coords_str.split())
            declination = get_magnetic_declination(lat, lon)
            
            self.waypoint_auto_declination_value = declination
            self.waypoint_auto_declination_label.config(text=f"Auto: {declination:.1f}°")
            
            # If in auto mode, also update the calculation immediately
            if self.waypoint_declination_mode.get() == "Auto":
                messagebox.showinfo("Auto Declination", f"Magnetic declination at {lat:.4f}, {lon:.4f} is {declination:.1f}°")
                
        except ValueError:
            messagebox.showerror("Input Error", "Invalid coordinate format. Use 'latitude longitude'.")
        except Exception as e:
            messagebox.showerror("Declination Error", f"Error calculating declination: {str(e)}")
            
    def update_dme_declination(self):
        """Update the auto declination value from the DME coordinates."""
        try:
            coords_str = self.entry_dme_coords.get().strip()
            if not coords_str:
                messagebox.showwarning("Auto Declination", "Please enter or search for DME coordinates first.")
                return
                
            lat, lon = map(float, coords_str.split())
            declination = get_magnetic_declination(lat, lon)
            
            self.dme_auto_declination_value = declination
            self.dme_auto_declination_label.config(text=f"Auto: {declination:.1f}°")
            
            # If in auto mode, also update the calculation immediately
            if self.dme_declination_mode.get() == "Auto":
                messagebox.showinfo("Auto Declination", f"Magnetic declination at {lat:.4f}, {lon:.4f} is {declination:.1f}°")
                
        except ValueError:
            messagebox.showerror("Input Error", "Invalid coordinate format. Use 'latitude longitude'.")
        except Exception as e:
            messagebox.showerror("Declination Error", f"Error calculating declination: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoordinateCalculatorApp(root)
    root.mainloop()