#!/usr/bin/env python3
"""
VOR-FIX Coordinate Calculator

A tool for calculating aviation navigation waypoints and approach fixes
using geodesic calculations based on VOR/DME/NDB data.
"""

import tkinter as tk
from src.ui import CoordinateCalculatorApp


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = CoordinateCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()