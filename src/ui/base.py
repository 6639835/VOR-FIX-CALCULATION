"""
VOR Fix Calculation Tool - UI Base Components

This module contains the base user interface components for the application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
from typing import Callable, List, Optional

from ..models import (
    AppMode, FileType, BearingMode, DeclinationMode, Coordinates,
    CalculationResult, NavigationEntry, NAV_TYPE_DESCRIPTIONS,
    OPERATION_CODES, FIX_TYPE_CODES, FIX_USAGE_CODES
)
from ..services import NavigationDataService, MagneticDeclinationService
from ..calculator import CoordinateCalculator
from ..validation import InputValidator, ValidationResult


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
        # FIX File Selection
        tk.Label(self.frame, text="FIX File:", width=8, anchor="w").pack(
            side=tk.LEFT, padx=5
        )
        self.entry_fix_file = tk.Entry(self.frame, width=40)
        self.entry_fix_file.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

        btn_browse_fix = tk.Button(
            self.frame,
            text="Browse",
            command=lambda: self._browse_file(FileType.FIX)
        )
        btn_browse_fix.pack(side=tk.LEFT, padx=5)

        # NAV File Selection
        tk.Label(self.frame, text="NAV File:", width=8, anchor="w").pack(
            side=tk.LEFT, padx=5
        )
        self.entry_nav_file = tk.Entry(self.frame, width=40)
        self.entry_nav_file.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

        btn_browse_nav = tk.Button(
            self.frame,
            text="Browse",
            command=lambda: self._browse_file(FileType.NAV)
        )
        btn_browse_nav.pack(side=tk.LEFT, padx=5)

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

