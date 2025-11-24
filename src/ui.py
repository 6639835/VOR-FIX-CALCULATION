"""
User interface for the VOR-FIX Coordinate Calculator.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .calculations import calculate_waypoint, get_radius_designator
from .constants import FileType, FixType, FixUsage, OperationType
from .file_operations import DataFileReader
from .formatters import FixFormatter, NavAidFormatter, WaypointFormatter
from .models import FixResult, NavAidEntry, WaypointResult
from .validators import (
    AirportCodeValidator,
    BearingValidator,
    CoordinateValidator,
    DeclinationValidator,
    DistanceValidator,
    RunwayCodeValidator,
    ValidationError,
    VORIdentifierValidator,
)


class CoordinateCalculatorApp:
    """Main application class for the VOR-FIX Coordinate Calculator."""

    def __init__(self, root: tk.Tk):
        """Initialize the application."""
        self.root = root
        self.root.title("VOR-FIX Coordinate Calculator")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)

        # State variables
        self.mode_var = tk.StringVar(value="WAYPOINT")
        self.fix_file_path = ""
        self.nav_file_path = ""
        self.search_file_type = tk.StringVar(value="NAV")

        # Build UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Mode selection
        self._create_mode_section()

        # File selection
        self._create_file_section()

        # Input section (contains both waypoint and fix frames)
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=5, fill="x")

        self.waypoint_frame = tk.Frame(self.input_frame)
        self.fix_frame = tk.Frame(self.input_frame)

        self._create_waypoint_section()
        self._create_fix_section()

        # Output section
        self._create_output_section()

        # Bottom buttons
        self._create_button_section()

        # Initialize view based on default mode
        self._on_mode_change()

    def _create_mode_section(self):
        """Create the mode selection section."""
        frame = tk.LabelFrame(self.root, text="Mode Selection", padx=10, pady=5)
        frame.pack(padx=10, pady=5, fill="x")

        tk.Label(frame, text="Select Mode:").pack(side=tk.LEFT, padx=5)

        mode_combo = ttk.Combobox(
            frame,
            textvariable=self.mode_var,
            values=["WAYPOINT", "FIX"],
            state="readonly",
            width=15,
        )
        mode_combo.pack(side=tk.LEFT, padx=5)
        self.mode_var.trace_add("write", lambda *args: self._on_mode_change())

    def _create_file_section(self):
        """Create the file selection section."""
        frame = tk.LabelFrame(self.root, text="Data Files", padx=10, pady=5)
        frame.pack(padx=10, pady=5, fill="x")

        # FIX file row
        fix_frame = tk.Frame(frame)
        fix_frame.pack(fill="x", pady=2)

        tk.Label(fix_frame, text="FIX File:", width=10, anchor="w").pack(side=tk.LEFT)
        self.entry_fix_file = tk.Entry(fix_frame)
        self.entry_fix_file.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        tk.Button(fix_frame, text="Browse", command=lambda: self._browse_file(FileType.FIX)).pack(
            side=tk.LEFT
        )

        # NAV file row
        nav_frame = tk.Frame(frame)
        nav_frame.pack(fill="x", pady=2)

        tk.Label(nav_frame, text="NAV File:", width=10, anchor="w").pack(side=tk.LEFT)
        self.entry_nav_file = tk.Entry(nav_frame)
        self.entry_nav_file.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        tk.Button(nav_frame, text="Browse", command=lambda: self._browse_file(FileType.NAV)).pack(
            side=tk.LEFT
        )

    def _create_waypoint_section(self):
        """Create the waypoint input section."""
        frame = self.waypoint_frame
        frame.columnconfigure(1, weight=1)

        row = 0

        # Search file type
        tk.Label(frame, text="Search in:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        search_combo = ttk.Combobox(
            frame,
            textvariable=self.search_file_type,
            values=["NAV", "FIX"],
            state="readonly",
            width=10,
        )
        search_combo.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # Identifier
        tk.Label(frame, text="VOR/DME/NDB ID:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_waypoint_id = tk.Entry(frame)
        self.entry_waypoint_id.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        tk.Button(frame, text="Search", command=self._search_waypoint_coords).grid(
            row=row, column=2, padx=5, pady=3
        )
        row += 1

        # Coordinates
        tk.Label(frame, text="Coordinates (Lat Lon):", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_waypoint_coords = tk.Entry(frame)
        self.entry_waypoint_coords.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Magnetic bearing
        tk.Label(frame, text="Magnetic Bearing (°):", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_bearing = tk.Entry(frame)
        self.entry_bearing.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Distance
        tk.Label(frame, text="Distance (NM):", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_distance = tk.Entry(frame)
        self.entry_distance.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Declination
        tk.Label(frame, text="Mag Declination (°):", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_declination = tk.Entry(frame)
        self.entry_declination.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Airport code
        tk.Label(frame, text="Airport Code:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_airport_code = tk.Entry(frame)
        self.entry_airport_code.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # VOR identifier
        tk.Label(frame, text="VOR Identifier:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_vor_id = tk.Entry(frame)
        self.entry_vor_id.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Operation type
        tk.Label(frame, text="Operation Type:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.combo_wp_operation = ttk.Combobox(
            frame, values=[op.label for op in OperationType], state="readonly"
        )
        self.combo_wp_operation.current(0)
        self.combo_wp_operation.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Calculate button
        tk.Button(frame, text="Calculate Waypoint", command=self._calculate_waypoint).grid(
            row=row, column=0, columnspan=3, pady=10
        )

    def _create_fix_section(self):
        """Create the fix input section."""
        frame = self.fix_frame
        frame.columnconfigure(1, weight=1)

        row = 0

        # Search file type
        tk.Label(frame, text="Search in:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        search_combo = ttk.Combobox(
            frame,
            textvariable=self.search_file_type,
            values=["FIX", "NAV"],
            state="readonly",
            width=10,
        )
        search_combo.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # FIX identifier
        tk.Label(frame, text="FIX Identifier:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_fix_id = tk.Entry(frame)
        self.entry_fix_id.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        tk.Button(frame, text="Search", command=self._search_fix_coords).grid(
            row=row, column=2, padx=5, pady=3
        )
        row += 1

        # Coordinates
        tk.Label(frame, text="Coordinates (Lat Lon):", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_fix_coords = tk.Entry(frame)
        self.entry_fix_coords.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # FIX type
        tk.Label(frame, text="FIX Type:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.combo_fix_type = ttk.Combobox(
            frame, values=[ft.label for ft in FixType], state="readonly"
        )
        self.combo_fix_type.current(0)
        self.combo_fix_type.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # FIX usage
        tk.Label(frame, text="FIX Usage:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.combo_fix_usage = ttk.Combobox(
            frame, values=[fu.label for fu in FixUsage], state="readonly"
        )
        self.combo_fix_usage.current(0)
        self.combo_fix_usage.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Runway code
        tk.Label(frame, text="Runway Code:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_runway_code = tk.Entry(frame)
        self.entry_runway_code.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Airport code
        tk.Label(frame, text="Airport Code:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.entry_fix_airport_code = tk.Entry(frame)
        self.entry_fix_airport_code.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Operation type
        tk.Label(frame, text="Operation Type:", anchor="e").grid(
            row=row, column=0, padx=5, pady=3, sticky="e"
        )
        self.combo_fix_operation = ttk.Combobox(
            frame, values=[op.label for op in OperationType], state="readonly"
        )
        self.combo_fix_operation.current(0)
        self.combo_fix_operation.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        row += 1

        # Calculate button
        tk.Button(frame, text="Calculate FIX", command=self._calculate_fix).grid(
            row=row, column=0, columnspan=3, pady=10
        )

    def _create_output_section(self):
        """Create the output display section."""
        frame = tk.LabelFrame(self.root, text="Output Result", padx=10, pady=5)
        frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.output_text = tk.Text(
            frame, height=6, state="disabled", wrap="word", font=("Courier", 10)
        )
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _create_button_section(self):
        """Create the bottom button section."""
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10, fill="x")

        tk.Button(frame, text="Clear Input", command=self._clear_fields).pack(side=tk.LEFT, padx=5)

        tk.Button(frame, text="Copy Result", command=self._copy_output).pack(side=tk.LEFT, padx=5)

        tk.Button(frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

    def _on_mode_change(self):
        """Handle mode selection change."""
        mode = self.mode_var.get()

        self.waypoint_frame.pack_forget()
        self.fix_frame.pack_forget()

        if mode == "WAYPOINT":
            self.waypoint_frame.pack(fill="x", pady=5)
            self.search_file_type.set("NAV")
        else:
            self.fix_frame.pack(fill="x", pady=5)
            self.search_file_type.set("FIX")

    def _browse_file(self, file_type: FileType):
        """Open file browser dialog."""
        filepath = filedialog.askopenfilename(
            title=f"Select {file_type.value} File",
            filetypes=[(f"{file_type.value} files", "*.dat"), ("All files", "*.*")],
        )

        if filepath:
            if file_type == FileType.FIX:
                self.fix_file_path = filepath
                self.entry_fix_file.delete(0, tk.END)
                self.entry_fix_file.insert(0, filepath)
            else:
                self.nav_file_path = filepath
                self.entry_nav_file.delete(0, tk.END)
                self.entry_nav_file.insert(0, filepath)

    def _get_file_type_and_path(self) -> tuple[FileType, str]:
        """Get current file type and path based on search selection."""
        file_type_str = self.search_file_type.get()
        file_type = FileType.NAV if file_type_str == "NAV" else FileType.FIX

        if file_type == FileType.NAV:
            return file_type, self.nav_file_path
        return file_type, self.fix_file_path

    def _search_waypoint_coords(self):
        """Search for waypoint coordinates in data file."""
        identifier = self.entry_waypoint_id.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter an identifier.")
            return

        file_type, file_path = self._get_file_type_and_path()

        if not file_path:
            messagebox.showerror("File Error", f"Please select a {file_type.value} file.")
            return

        try:
            entries = DataFileReader.read_file(file_path, file_type, identifier)

            if not entries:
                messagebox.showinfo("Not Found", f"Identifier '{identifier}' not found.")
                return

            if len(entries) > 1:
                self._show_entry_selection(entries, self._set_waypoint_coords)
            else:
                self._set_waypoint_coords(entries[0])

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _search_fix_coords(self):
        """Search for fix coordinates in data file."""
        identifier = self.entry_fix_id.get().strip().upper()
        if not identifier:
            messagebox.showerror("Input Error", "Please enter a FIX identifier.")
            return

        file_type, file_path = self._get_file_type_and_path()

        if not file_path:
            messagebox.showerror("File Error", f"Please select a {file_type.value} file.")
            return

        try:
            entries = DataFileReader.read_file(file_path, file_type, identifier)

            if not entries:
                messagebox.showinfo("Not Found", f"Identifier '{identifier}' not found.")
                return

            if len(entries) > 1:
                self._show_entry_selection(entries, self._set_fix_coords)
            else:
                self._set_fix_coords(entries[0])

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _show_entry_selection(self, entries: list[NavAidEntry], callback):
        """Show dialog for selecting from multiple entries."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Entry")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Multiple entries found. Please select one:").pack(pady=10)

        selected_var = tk.StringVar()

        for i, entry in enumerate(entries):
            display_text = NavAidFormatter.format_for_display(entry)
            rb = tk.Radiobutton(dialog, text=display_text, variable=selected_var, value=str(i))
            rb.pack(anchor="w", padx=20)

        def on_confirm():
            selection = selected_var.get()
            if not selection:
                messagebox.showwarning("Selection Required", "Please select an entry.")
                return
            callback(entries[int(selection)])
            dialog.destroy()

        tk.Button(dialog, text="Confirm", command=on_confirm).pack(pady=10)

        dialog.wait_window()

    def _set_waypoint_coords(self, entry: NavAidEntry):
        """Set waypoint coordinates from selected entry."""
        self.entry_waypoint_coords.delete(0, tk.END)
        self.entry_waypoint_coords.insert(0, f"{entry.latitude} {entry.longitude}")

    def _set_fix_coords(self, entry: NavAidEntry):
        """Set fix coordinates from selected entry."""
        self.entry_fix_coords.delete(0, tk.END)
        self.entry_fix_coords.insert(0, f"{entry.latitude} {entry.longitude}")

    def _calculate_waypoint(self):
        """Perform waypoint calculation."""
        try:
            # Parse and validate inputs
            coords_str = self.entry_waypoint_coords.get().strip()
            if not coords_str:
                # Try to search by identifier
                identifier = self.entry_waypoint_id.get().strip()
                if not identifier:
                    raise ValidationError("Please enter coordinates or an identifier.")
                self._search_waypoint_coords()
                return

            origin = CoordinateValidator.parse_coordinates(coords_str)
            bearing = BearingValidator.parse(self.entry_bearing.get())
            distance = DistanceValidator.parse(self.entry_distance.get())
            declination = DeclinationValidator.parse(self.entry_declination.get())
            airport_code = AirportCodeValidator.parse(self.entry_airport_code.get())
            vor_id = VORIdentifierValidator.parse(self.entry_vor_id.get())

            # Calculate waypoint
            target = calculate_waypoint(origin, bearing, distance, declination)
            radius_letter = get_radius_designator(distance)

            # Get operation code
            op_label = self.combo_wp_operation.get()
            op_code = ""
            for op in OperationType:
                if op.label == op_label:
                    op_code = op.code
                    break

            # Create result
            result = WaypointResult(
                coordinates=target,
                radius_letter=radius_letter,
                airport_code=airport_code,
                operation_code=op_code,
                vor_identifier=vor_id,
                magnetic_bearing=bearing,
                distance_nm=distance,
            )

            # Format and display output
            output = WaypointFormatter.format(result)
            self._set_output(output)

        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))

    def _calculate_fix(self):
        """Perform fix calculation."""
        try:
            # Parse and validate inputs
            coords_str = self.entry_fix_coords.get().strip()
            if not coords_str:
                raise ValidationError("Please enter or search for coordinates first.")

            coords = CoordinateValidator.parse_coordinates(coords_str)
            runway_code = RunwayCodeValidator.parse(self.entry_runway_code.get())
            airport_code = AirportCodeValidator.parse(self.entry_fix_airport_code.get())

            # Get fix type code
            fix_type_label = self.combo_fix_type.get()
            fix_code = ""
            for ft in FixType:
                if ft.label == fix_type_label:
                    fix_code = ft.code
                    break

            # Get usage code
            usage_label = self.combo_fix_usage.get()
            usage_code = ""
            for fu in FixUsage:
                if fu.label == usage_label:
                    usage_code = fu.code
                    break

            # Get operation code
            op_label = self.combo_fix_operation.get()
            op_code = ""
            for op in OperationType:
                if op.label == op_label:
                    op_code = op.code
                    break

            if not fix_code or not usage_code:
                raise ValidationError("Invalid FIX type or usage selection.")

            # Create result
            result = FixResult(
                coordinates=coords,
                fix_code=fix_code,
                usage_code=usage_code,
                runway_code=str(runway_code),
                airport_code=airport_code,
                operation_code=op_code,
            )

            # Format and display output
            output = FixFormatter.format(result)
            self._set_output(output)

        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))

    def _set_output(self, text: str):
        """Set the output text."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state=tk.DISABLED)

    def _clear_fields(self):
        """Clear all input fields."""
        if self.mode_var.get() == "WAYPOINT":
            self.entry_waypoint_id.delete(0, tk.END)
            self.entry_waypoint_coords.delete(0, tk.END)
            self.entry_bearing.delete(0, tk.END)
            self.entry_distance.delete(0, tk.END)
            self.entry_declination.delete(0, tk.END)
            self.entry_airport_code.delete(0, tk.END)
            self.entry_vor_id.delete(0, tk.END)
        else:
            self.entry_fix_id.delete(0, tk.END)
            self.entry_fix_coords.delete(0, tk.END)
            self.entry_runway_code.delete(0, tk.END)
            self.entry_fix_airport_code.delete(0, tk.END)

        self._set_output("")

    def _copy_output(self):
        """Copy output text to clipboard."""
        self.output_text.config(state=tk.NORMAL)
        text = self.output_text.get(1.0, tk.END).strip()
        self.output_text.config(state=tk.DISABLED)

        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Copied", "Result copied to clipboard!")
        else:
            messagebox.showwarning("No Output", "No text to copy.")
