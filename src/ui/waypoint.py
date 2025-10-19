"""
VOR Fix Calculation Tool - Waypoint Calculation UI

This module contains the waypoint calculation user interface components.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from typing import Callable, List

from ..models import (
    AppMode, FileType, BearingMode, DeclinationMode, Coordinates,
    CalculationResult, NavigationEntry, OPERATION_CODES
)
from ..services import NavigationDataService, MagneticDeclinationService
from ..calculator import CoordinateCalculator
from ..validation import InputValidator, ValidationResult
from .base import BaseCalculationFrame


class WaypointCalculationFrame(BaseCalculationFrame):
    """Frame for waypoint calculations."""

    def __init__(
        self,
        parent,
        nav_data_service: NavigationDataService,
        declination_service: MagneticDeclinationService,
        calculator: CoordinateCalculator,
        on_calculate_callback: Callable[[CalculationResult], None]
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

    def _handle_duplicate_entries(self, matching_lines: List[NavigationEntry]):
        """Handle multiple entries with the same identifier."""
        choice_window = tk.Toplevel(self.frame)
        choice_window.title("Choose Entry")
        tk.Label(choice_window, text="Multiple entries found. Please choose one:").pack()

        selected_line = tk.StringVar()
        file_type = FileType(self.search_file_type.get())

        for entry in matching_lines:
            display_text = f"{entry.description} - {entry.identifier}"
            if len(entry.additional_info.get("raw_data", [])) > 9:
                display_text += f" - {entry.additional_info['raw_data'][9]}"
            else:
                display_text += " - [Location missing]"

            rb = tk.Radiobutton(
                choice_window,
                text=display_text,
                variable=selected_line,
                value=f"{entry.coordinates.lat},{entry.coordinates.lon}"
            )
            rb.pack()

        def confirm_choice():
            chosen_coords = selected_line.get()
            if chosen_coords:
                lat, lon = map(float, chosen_coords.split(","))
                coords = Coordinates(lat, lon)
                self.entry_coords.delete(0, tk.END)
                self.entry_coords.insert(0, str(coords))
                choice_window.destroy()
            else:
                messagebox.showwarning("Selection Required", "Please select an entry.")

        btn_confirm = tk.Button(choice_window, text="Confirm", command=confirm_choice)
        btn_confirm.pack()
        choice_window.wait_window()

    def _set_coordinates(self, entry: NavigationEntry):
        """Set coordinates from search results."""
        self.entry_coords.delete(0, tk.END)
        self.entry_coords.insert(0, str(entry.coordinates))

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

            validation = InputValidator.validate_coordinates(coords_str)
            if not validation.is_valid:
                messagebox.showerror("Input Error", validation.error_message)
                return

            coordinates = validation.value
            declination = self.declination_service.get_declination(coordinates)

            self.auto_declination_value = declination
            self.auto_declination_label.config(text=f"Auto: {declination:.1f}°")

            if self.declination_mode.get() == DeclinationMode.AUTO.value:
                messagebox.showinfo(
                    "Auto Declination",
                    f"Magnetic declination at {coordinates.lat:.4f}, {coordinates.lon:.4f} "
                    f"is {declination:.1f}°"
                )

        except Exception as e:
            messagebox.showerror("Declination Error", f"Error calculating declination: {e}")

    def calculate(self):
        """Perform waypoint calculation."""
        try:
            # Validate all inputs
            coords_str = self.entry_coords.get().strip()
            coordinates = None

            if coords_str:
                validation = InputValidator.validate_coordinates(coords_str)
                if not validation.is_valid:
                    messagebox.showerror("Input Error", validation.error_message)
                    return
                coordinates = validation.value
            elif self.entry_identifier.get().strip():
                # Try to search for coordinates first
                self.search_coordinates()
                coords_str = self.entry_coords.get().strip()
                if coords_str:
                    validation = InputValidator.validate_coordinates(coords_str)
                    if validation.is_valid:
                        coordinates = validation.value
                    else:
                        messagebox.showerror("Input Error", "Could not find valid coordinates for identifier.")
                        return
                else:
                    messagebox.showerror("Input Error", "Could not find coordinates for identifier.")
                    return
            else:
                messagebox.showerror("Input Error", "Please enter identifier or coordinates.")
                return

            # Validate other inputs
            bearing_validation = InputValidator.validate_bearing(self.entry_bearing.get())
            if not bearing_validation.is_valid:
                messagebox.showerror("Input Error", bearing_validation.error_message)
                return
            bearing = bearing_validation.value

            distance_validation = InputValidator.validate_distance(self.entry_distance.get())
            if not distance_validation.is_valid:
                messagebox.showerror("Input Error", distance_validation.error_message)
                return
            distance_nm = distance_validation.value

            airport_validation = InputValidator.validate_airport_code(self.entry_airport_code.get())
            if not airport_validation.is_valid:
                messagebox.showerror("Input Error", airport_validation.error_message)
                return
            airport_code = airport_validation.value

            vor_validation = InputValidator.validate_vor_identifier(self.entry_vor_identifier.get())
            if not vor_validation.is_valid:
                messagebox.showerror("Input Error", vor_validation.error_message)
                return
            vor_identifier = vor_validation.value

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

