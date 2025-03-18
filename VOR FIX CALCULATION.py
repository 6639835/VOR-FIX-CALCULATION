import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from geographiclib.geodesic import Geodesic
import math
import os

# Constants for the Earth's ellipsoid model
GEODESIC = Geodesic.WGS84

def calculate_target_coords_geodesic(lat1, lon1, azimuth, distance_nm):
    """Calculates the target coordinates."""
    distance = distance_nm * 1852  # Convert nautical miles to meters
    result = GEODESIC.Direct(lat1, lon1, azimuth, distance)
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

      tk.Label(frm, text="Magnetic Bearing (°):", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e") # Aligned labels, added unit
      self.entry_bearing = tk.Entry(frm, width=30)
      self.entry_bearing.grid(row=3, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="Distance (NM):", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e") # Aligned labels, added unit
      self.entry_distance = tk.Entry(frm, width=30)
      self.entry_distance.grid(row=4, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="Magnetic Declination (°):", anchor="e").grid(row=5, column=0, padx=5, pady=5, sticky="e") # Aligned labels, added unit
      self.entry_declination = tk.Entry(frm, width=30)
      self.entry_declination.grid(row=5, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="Airport Code:", anchor="e").grid(row=6, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_airport_code = tk.Entry(frm, width=30)
      self.entry_airport_code.grid(row=6, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="VOR Identifier:", anchor="e").grid(row=7, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_vor_identifier = tk.Entry(frm, width=30)
      self.entry_vor_identifier.grid(row=7, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="Operation Type:", anchor="e").grid(row=8, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.combo_operation_type = ttk.Combobox(frm, values=["Departure", "Arrival", "Approach"], state="readonly")
      self.combo_operation_type.current(0)
      self.combo_operation_type.grid(row=8, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell
      btn_calc = tk.Button(frm, text="Calculate Waypoint", command=self.on_calculate_waypoint)
      btn_calc.grid(row=9, column=0, columnspan=2, pady=5)

      # Button to search for coordinates
      btn_search_waypoint = tk.Button(frm, text="Search Coordinates", command=self.search_waypoint_coords)
      btn_search_waypoint.grid(row=1, column=2, padx=5, pady=5)

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

      tk.Label(frm, text="FIX Type:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.combo_fix_type = ttk.Combobox(frm, values=["VORDME", "VOR", "NDBDME", "NDB", "ILS", "RNP"], state="readonly")
      self.combo_fix_type.current(0)
      self.combo_fix_type.grid(row=3, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell
      tk.Label(frm, text="FIX Usage:", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.combo_fix_usage = ttk.Combobox(frm, values=["Final approach fix", "Initial approach fix", "Intermediate approach fix", "Final approach course fix", "Missed approach point fix"], state="readonly")
      self.combo_fix_usage.current(0)
      self.combo_fix_usage.grid(row=4, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell
      tk.Label(frm, text="Runway Code:", anchor="e").grid(row=5, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_runway_code = tk.Entry(frm, width=30)
      self.entry_runway_code.grid(row=5, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="Airport Code:", anchor="e").grid(row=6, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.entry_fix_airport_code = tk.Entry(frm, width=30)
      self.entry_fix_airport_code.grid(row=6, column=1, padx=5, pady=5, sticky="ew") # Expand entry to fill cell
      tk.Label(frm, text="Operation Type:", anchor="e").grid(row=7, column=0, padx=5, pady=5, sticky="e") # Aligned labels
      self.combo_fix_operation_type = ttk.Combobox(frm, values=["Departure", "Arrival", "Approach"], state="readonly")
      self.combo_fix_operation_type.current(0)
      self.combo_fix_operation_type.grid(row=7, column=1, padx=5, pady=5, sticky="ew") # Expand combobox to fill cell
      btn_calc = tk.Button(frm, text="Calculate FIX", command=self.on_calculate_fix)
      btn_calc.grid(row=8, column=0, columnspan=2, pady=5)

      # Button to search for coordinates
      btn_search_fix = tk.Button(frm, text="Search Coordinates", command=self.search_fix_coords)
      btn_search_fix.grid(row=1, column=2, padx=5, pady=5)

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

    def calculate_target_coords_vincenty(self, lat_vor, lon_vor, magnetic_bearing, distance_nm, declination):
        true_bearing = (magnetic_bearing + declination) % 360
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


                magnetic_bearing = float(self.entry_bearing.get())
                if not (0 <= magnetic_bearing < 360):
                    raise ValueError("Magnetic bearing should be within 0-359 degrees")
                distance_nm = float(self.entry_distance.get())
                if distance_nm <= 0:
                    raise ValueError("Distance should be greater than 0 nautical miles")
                declination = float(self.entry_declination.get())
                airport_code = self.entry_airport_code.get().strip().upper()
                if len(airport_code) != 4:
                    raise ValueError("Airport code must be 4 letters")
                vor_identifier = self.entry_vor_identifier.get().strip().upper()
                if vor_identifier and not (1 <= len(vor_identifier) <= 3 and vor_identifier.isalpha()):
                    raise ValueError("VOR identifier should be 1-3 letters and alphabetic")
                return lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier #Now return the coordinate
            except ValueError as e:
                messagebox.showerror("Input Error", f"WAYPOINT mode input error: {e}")
                return None
        return True  # FIX validation happens after coordinate search (mostly UI related validations in on_calculate_fix)

    def process_output(self, result, mode, vor_identifier="", magnetic_bearing="", distance_nm=""):
        if mode == "WAYPOINT":
            lat_target, lon_target, radius_letter, airport_code, operation_code = result
            if distance_nm > 26.5: # Consider making 26.5 a constant
                rounded_distance_nm_int = int(round(distance_nm))
                output = (f"{lat_target:.9f} {lon_target:.9f} "f"{vor_identifier}{rounded_distance_nm_int} "f"{airport_code} {airport_code[:2]}")
                if vor_identifier:
                    magnetic_bearing_int = int(magnetic_bearing)
                    output += f" {operation_code} {vor_identifier}{magnetic_bearing_int:03d}{rounded_distance_nm_int:03d}"
                else:
                    output += f" {operation_code}"
            else:
                output = (f"{lat_target:.9f} {lon_target:.9f} "f"D{int(magnetic_bearing):03d}{radius_letter} "f"{airport_code} {airport_code[:2]}")
                if vor_identifier:
                    magnetic_bearing_int = int(magnetic_bearing)
                    output += f" {operation_code} {vor_identifier}{magnetic_bearing_int:03d}{int(round(distance_nm)):03d}"
                else:
                    output += f" {operation_code}"
        elif mode == "FIX":
            lat, lon, fix_code, usage_code, runway_code, airport_code, operation_code = result
            output = (f"{lat:.9f} {lon:.9f} {usage_code}{fix_code}{int(runway_code):02d} "f"{airport_code} {airport_code[:2]} {operation_code}")
        self.output_entry.config(state=tk.NORMAL) # Make output editable
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.insert(tk.END, output)
        self.output_entry.config(state=tk.DISABLED) # Set back to readonly

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
        lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier = params

        if lat_vor is None or lon_vor is None: # Check if coords were obtained, if not, try to search based on identifier
            identifier = self.entry_waypoint_identifier.get().strip().upper()
            if not identifier:
                messagebox.showerror("Input Error", "Please enter identifier or coordinates.")
                return
            self.search_waypoint_coords_and_calculate(identifier, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier) # New method to handle search and calculation
            return # Exit current calculation

        try:
            lat_target, lon_target = self.calculate_target_coords_vincenty(lat_vor, lon_vor, magnetic_bearing, distance_nm, declination)
            radius_letter = get_radius_letter(distance_nm)
            operation_code_map = {"Departure": "4464713", "Arrival": "4530249", "Approach": "4595785"}
            operation_code = operation_code_map.get(self.combo_operation_type.get(), "")
            result = (round(lat_target, 9), round(lon_target, 9), radius_letter, airport_code, operation_code)
            self.process_output(result, "WAYPOINT", vor_identifier, magnetic_bearing, distance_nm)
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {str(e)}")

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
            magnetic_bearing, distance_nm, declination, airport_code, vor_identifier = self.pending_calculation_params
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

if __name__ == "__main__":
    root = tk.Tk()
    app = CoordinateCalculatorApp(root)
    root.mainloop()
