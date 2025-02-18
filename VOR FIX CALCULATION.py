import tkinter as tk
from tkinter import ttk, messagebox
from geographiclib.geodesic import Geodesic
import math

# Constants for the Earth's ellipsoid model
GEODESIC = Geodesic.WGS84

def calculate_target_coords_geodesic(lat1, lon1, azimuth, distance_nm):
    """
    Calculates the target coordinates using the Geodesic class from geographiclib.

    Args:
        lat1 (float): Latitude of the starting point.
        lon1 (float): Longitude of the starting point.
        azimuth (float): Azimuth (bearing) in degrees.
        distance_nm (float): Distance in nautical miles.

    Returns:
        tuple: A tuple containing the latitude and longitude of the target point.
    """
    distance = distance_nm * 1852  # Convert nautical miles to meters
    result = GEODESIC.Direct(lat1, lon1, azimuth, distance)
    return result['lat2'], result['lon2']

def get_radius_letter(distance_nm):
    """
    Gets the single-letter radius designator based on the distance.

    Args:
        distance_nm (float): Distance in nautical miles.

    Returns:
        str: The radius letter.
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
    # 'Z' is chosen as the fallback letter when the distance does not fall within any specified range
    return 'Z'

class CoordinateCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Coordinate Calculator")

        # Set window size and position (adjust as needed)
        self.root.geometry("700x650")  # Adjust window height to accommodate new input fields

        # Mode selection
        self.mode_var = tk.StringVar(value="WAYPOINT")
        self.create_mode_selection()

        # Frame containing all input controls
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=5, fill="x")

        # Create separate interfaces for WAYPOINT and FIX
        self.waypoint_frame = tk.Frame(self.input_frame)
        self.fix_frame = tk.Frame(self.input_frame)

        self.create_waypoint_ui()
        self.create_fix_ui()

        # Output area
        self.create_output_ui()

        # Show WAYPOINT interface by default
        self.on_mode_change()

        # Add operation buttons at the bottom of the interface
        self.create_bottom_buttons()

    def create_mode_selection(self):
        """
        Creates the mode selection area at the top.
        """
        frm_mode = tk.LabelFrame(self.root, text="Mode Selection", padx=10, pady=5)
        frm_mode.pack(padx=10, pady=5, fill="x")

        tk.Label(frm_mode, text="Select Mode:").pack(side=tk.LEFT, padx=5)
        combo_mode = ttk.Combobox(frm_mode, textvariable=self.mode_var, values=('WAYPOINT', 'FIX'), state="readonly")
        combo_mode.pack(side=tk.LEFT, padx=5)

        # Triggered when the selection changes
        # 'write' means that the callback function is triggered when the value of the variable changes
        self.mode_var.trace_add('write', self.on_mode_change)

    def on_mode_change(self, *args):
        """
        Switches the display of different input forms based on the mode.
        """
        current_mode = self.mode_var.get()
        # Hide both interfaces
        self.waypoint_frame.pack_forget()
        self.fix_frame.pack_forget()

        # Show controls based on the mode
        if current_mode == "WAYPOINT":
            self.waypoint_frame.pack(side=tk.TOP, fill="x", pady=5)
        else:
            self.fix_frame.pack(side=tk.TOP, fill="x", pady=5)

    def create_waypoint_ui(self):
        """
        Creates the input area for the WAYPOINT interface.
        """
        frm = self.waypoint_frame

        tk.Label(frm, text="VOR/DME/NDB Coordinates (Latitude Longitude):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_vor_coords = tk.Entry(frm, width=30)
        self.entry_vor_coords.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frm, text="Magnetic Bearing (degrees):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_bearing = tk.Entry(frm, width=30)
        self.entry_bearing.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frm, text="Distance (nautical miles):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_distance = tk.Entry(frm, width=30)
        self.entry_distance.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(frm, text="Magnetic Declination (degrees):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entry_declination = tk.Entry(frm, width=30)
        self.entry_declination.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(frm, text="Airport Code (4 letters):").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.entry_airport_code = tk.Entry(frm, width=30)
        self.entry_airport_code.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(frm, text="VOR Identifier (3-4 letters):").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.entry_vor_identifier = tk.Entry(frm, width=30)
        self.entry_vor_identifier.grid(row=5, column=1, padx=5, pady=5)

        tk.Label(frm, text="Operation Type:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.combo_operation_type = ttk.Combobox(frm, values=["Departure", "Arrival", "Approach"], state="readonly")
        self.combo_operation_type.current(0)
        self.combo_operation_type.grid(row=6, column=1, padx=5, pady=5)

        btn_calc = tk.Button(frm, text="Calculate Waypoint", command=self.on_calculate_waypoint)
        btn_calc.grid(row=7, column=0, columnspan=2, pady=5)

    def create_fix_ui(self):
        """
        Creates the input area for the FIX interface.
        """
        frm = self.fix_frame

        tk.Label(frm, text="FIX Coordinates (Latitude Longitude):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_fix_coords = tk.Entry(frm, width=30)
        self.entry_fix_coords.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frm, text="FIX Type:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.combo_fix_type = ttk.Combobox(frm, values=["VORDME", "VOR", "NDBDME", "NDB", "ILS", "RNP"], state="readonly")
        self.combo_fix_type.current(0)
        self.combo_fix_type.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frm, text="FIX Usage:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.combo_fix_usage = ttk.Combobox(frm,
            values=[
                "Final approach fix",
                "Initial approach fix",
                "Intermediate approach fix",
                "Final approach course fix",
                "Missed approach point fix"
            ],
            state="readonly"
        )
        self.combo_fix_usage.current(0)
        self.combo_fix_usage.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(frm, text="Runway Code (two digits):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entry_runway_code = tk.Entry(frm, width=30)
        self.entry_runway_code.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(frm, text="Airport Code (4 letters):").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.entry_fix_airport_code = tk.Entry(frm, width=30)
        self.entry_fix_airport_code.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(frm, text="Operation Type:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.combo_fix_operation_type = ttk.Combobox(frm, values=["Departure", "Arrival", "Approach"], state="readonly")
        self.combo_fix_operation_type.current(0)
        self.combo_fix_operation_type.grid(row=5, column=1, padx=5, pady=5)

        btn_calc = tk.Button(frm, text="Calculate FIX", command=self.on_calculate_fix)
        btn_calc.grid(row=6, column=0, columnspan=2, pady=5)

    def create_output_ui(self):
        """
        Creates the output area.
        """
        frm_output = tk.LabelFrame(self.root, text="Output Result", padx=10, pady=5)
        frm_output.pack(padx=10, pady=5, fill="both", expand=True)

        self.output_entry = tk.Text(frm_output, width=80, height=8)  # Increase height to prevent output content from being too long
        self.output_entry.pack(padx=5, pady=5, fill="both", expand=True)

    def create_bottom_buttons(self):
        """
        Creates bottom operation buttons, such as clear, copy, etc.
        """
        frm_btn = tk.Frame(self.root)
        frm_btn.pack(padx=10, pady=5, fill="x")

        btn_clear = tk.Button(frm_btn, text="Clear Input", command=self.clear_fields)
        btn_clear.pack(side=tk.LEFT, padx=5)

        btn_copy = tk.Button(frm_btn, text="Copy Result", command=self.copy_output)
        btn_copy.pack(side=tk.LEFT, padx=5)

        btn_exit = tk.Button(frm_btn, text="Exit", command=self.root.quit)
        btn_exit.pack(side=tk.RIGHT, padx=5)

    def clear_fields(self):
        """
        Clears all input and output fields.
        """
        if self.mode_var.get() == "WAYPOINT":
            self.entry_vor_coords.delete(0, tk.END)
            self.entry_bearing.delete(0, tk.END)
            self.entry_distance.delete(0, tk.END)
            self.entry_declination.delete(0, tk.END)
            self.entry_airport_code.delete(0, tk.END)
            self.entry_vor_identifier.delete(0, tk.END)  # Clear VOR Identifier
        else:
            self.entry_fix_coords.delete(0, tk.END)
            self.entry_runway_code.delete(0, tk.END)
            self.entry_fix_airport_code.delete(0, tk.END)

        self.output_entry.delete(1.0, tk.END)

    def copy_output(self):
        """
        Copies the output result to the clipboard.
        """
        output_text = self.output_entry.get(1.0, tk.END).strip()
        if output_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(output_text)
            messagebox.showinfo("Copy Result", "Result copied to clipboard!")
        else:
            messagebox.showwarning("Copy Result", "No text to copy!")

    def calculate_target_coords_vincenty(self, lat_vor, lon_vor, magnetic_bearing, distance_nm, declination):
        """
        Calculates the target point coordinates based on the VOR coordinates, magnetic bearing, distance, and declination.
        """
        true_bearing = (magnetic_bearing + declination) % 360
        return calculate_target_coords_geodesic(lat_vor, lon_vor, true_bearing, distance_nm)

    def validate_input(self, mode):
        """
        Validates the input for correctness.
        """
        if mode == "WAYPOINT":
            try:
                lat_vor, lon_vor = map(float, self.entry_vor_coords.get().split())
                if not (-90 <= lat_vor <= 90 and -180 <= lon_vor <= 180):
                    raise ValueError("Latitude/Longitude out of range (±90 / ±180)")
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
                vor_identifier = self.entry_vor_identifier.get().strip().upper()  # Get VOR Identifier
                if vor_identifier and not (3 <= len(vor_identifier) <= 4) and not vor_identifier.isalpha():  # Basic validation for identifier format
                    raise ValueError("VOR identifier should be 3-4 letters")

                return lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier  # Return vor_identifier
            except ValueError as e:
                messagebox.showerror("Input Error", f"WAYPOINT mode input error: {e}")
                return None

        elif mode == "FIX":
            try:
                lat, lon = map(float, self.entry_fix_coords.get().split())
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Latitude/Longitude out of range (±90 / ±180)")
                fix_type = self.combo_fix_type.get()
                fix_usage = self.combo_fix_usage.get()
                runway_code = self.entry_runway_code.get().strip()
                if not runway_code.isdigit() or not 0 <= int(runway_code) <= 99:
                    raise ValueError("Runway code should be a two-digit number between 0 and 99")
                airport_code = self.entry_fix_airport_code.get().strip().upper()
                if len(airport_code) != 4:
                    raise ValueError("Airport code must be 4 letters")
                return (lat, lon, fix_type, fix_usage, runway_code, airport_code)
            except ValueError as e:
                messagebox.showerror("Input Error", f"FIX mode input error: {e}")
                return None

    def process_output(self, result, mode, vor_identifier="", magnetic_bearing="", distance_nm=""):  # Add vor_identifier, magnetic_bearing, distance_nm parameters
        """
        Processes the calculation result and displays the output.
        """
        if mode == "WAYPOINT":
            lat_target, lon_target, radius_letter, airport_code, operation_code = result
            if distance_nm > 26.5:  # Check if nautical miles exceed 26.5
                rounded_distance_nm_int = int(round(distance_nm))
                output = (
                    f"{lat_target:.9f} {lon_target:.9f} "
                    f"{vor_identifier}{rounded_distance_nm_int} "  # Output VOR Identifier + nautical miles, without leading zeros
                    f"{airport_code} {airport_code[:2]}"
                )
                if vor_identifier:  # If VOR Identifier is not empty, add extra information
                    magnetic_bearing_int = int(magnetic_bearing)  # Integer magnetic bearing
                    output += f" {operation_code} {vor_identifier}{magnetic_bearing_int:03d}{rounded_distance_nm_int:03d}"  # Add VOR info, format distance to three digits with leading zeros, magnetic bearing to three digits
                else:
                    output += f" {operation_code}"

            else:  # Nautical miles less than or equal to 26.5, keep original format
                output = (
                    f"{lat_target:.9f} {lon_target:.9f} "
                    f"D{int(magnetic_bearing):03d}{radius_letter} "  # Original format: DXXX[Radius Letter]
                    f"{airport_code} {airport_code[:2]}"
                )
                if vor_identifier:  # If VOR Identifier is not empty, add extra information
                    magnetic_bearing_int = int(magnetic_bearing)  # Integer magnetic bearing
                    output += f" {operation_code} {vor_identifier}{magnetic_bearing_int:03d}{int(round(distance_nm)):03d}"  # Add VOR info, format distance to three digits with leading zeros, magnetic bearing to three digits
                else:
                    output += f" {operation_code}"

        else:  # FIX mode remains unchanged
            lat, lon, fix_code, usage_code, runway_code, airport_code, operation_code = result
            output = (
                f"{lat:.9f} {lon:.9f} {usage_code}{fix_code}{int(runway_code):02d} "
                f"{airport_code} {airport_code[:2]} {operation_code}"
            )
        self.output_entry.delete(1.0, tk.END)
        self.output_entry.insert(tk.END, output)

    def on_calculate_waypoint(self):
        """
        Calculates WAYPOINT coordinates and outputs them.
        """
        params = self.validate_input("WAYPOINT")
        if params is None:
            return

        lat_vor, lon_vor, magnetic_bearing, distance_nm, declination, airport_code, vor_identifier = params  # Get vor_identifier
        try:
            lat_target, lon_target = self.calculate_target_coords_vincenty(
                lat_vor, lon_vor, magnetic_bearing, distance_nm, declination
            )
            radius_letter = get_radius_letter(distance_nm)
            operation_code_map = {
                "Departure": "4464713",
                "Arrival": "4530249",
                "Approach": "4595785"
            }
            operation_code = operation_code_map.get(self.combo_operation_type.get(), "")
            result = (
                round(lat_target, 9),
                round(lon_target, 9),
                radius_letter,
                airport_code,
                operation_code
            )
            self.process_output(
                result,
                "WAYPOINT",
                vor_identifier,  # Pass vor_identifier
                magnetic_bearing,  # Pass magnetic_bearing
                distance_nm  # Pass distance_nm
            )
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {str(e)}")

    def on_calculate_fix(self):
        """
        Calculates FIX coordinates and outputs them.
        """
        params = self.validate_input("FIX")
        if params is None:
            return

        lat, lon, fix_type, fix_usage, runway_code, airport_code = params
        try:
            fix_code_map = {
                "VORDME": "D", "VOR": "V", "NDBDME": "Q", "NDB": "N",
                "ILS": "I", "RNP": "R"
            }
            usage_code_map = {
                "Final approach fix": "F",
                "Initial approach fix": "A",
                "Intermediate approach fix": "I",
                "Final approach course fix": "C",
                "Missed approach point fix": "M"
            }
            operation_code_map = {
                "Departure": "4464713",
                "Arrival": "4530249",
                "Approach": "4595785"
            }

            fix_code = fix_code_map.get(fix_type, "")
            usage_code = usage_code_map.get(fix_usage, "")
            if not fix_code or not usage_code:
                raise ValueError("Invalid FIX type or usage")

            operation_code = operation_code_map.get(self.combo_fix_operation_type.get(), "")
            result = (
                round(lat, 9),
                round(lon, 9),
                fix_code,
                usage_code,
                runway_code,
                airport_code,
                operation_code
            )
            self.process_output(result, "FIX")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoordinateCalculatorApp(root)
    root.mainloop()
