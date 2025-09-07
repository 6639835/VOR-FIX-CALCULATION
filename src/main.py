"""
VOR Fix Calculation Tool - Main Application

A comprehensive tool for calculating waypoints and fixes using VOR/DME and NDB navigation data.
Supports both magnetic and true bearing calculations with automatic magnetic declination.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import logging
from typing import List

from .models import AppMode, CalculationResult
from .services import NavigationDataService, MagneticDeclinationService
from .calculator import CoordinateCalculator
from .ui_base import FileSelectionFrame
from .ui_waypoint import WaypointCalculationFrame

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoordinateCalculatorApp:
    """Main application class for the coordinate calculator."""

    def __init__(self, root):
        self.root = root
        self.root.title("VOR FIX Coordinate Calculator")
        self.root.geometry("900x700")

        # Initialize services
        self.nav_data_service = NavigationDataService()
        self.declination_service = MagneticDeclinationService()
        self.calculator = CoordinateCalculator()

        # Initialize state
        self.mode_var = tk.StringVar(value=AppMode.WAYPOINT.value)
        self.history: List[CalculationResult] = []

        # Create UI components
        self._create_ui()

        logger.info("Application initialized successfully")

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

        # Show the appropriate frame
        if current_mode == AppMode.WAYPOINT:
            self.waypoint_frame.pack(side=tk.TOP, fill="x", pady=5)

    def _on_calculation_complete(self, result: CalculationResult):
        """Handle completion of a calculation."""
        # Add to history
        self.history.append(result)
        logger.info(f"Calculation completed: {result.output_string}")

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
        history_window.geometry("900x500")

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
        history_tree.column("Output", width=600, anchor="w")

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
