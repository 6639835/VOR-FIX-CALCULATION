#!/usr/bin/env python3
"""
VOR Fix Calculation Tool - Main Entry Point

A comprehensive tool for calculating waypoints and fixes using VOR/DME and NDB navigation data.
Supports both magnetic and true bearing calculations with automatic magnetic declination.

Usage:
    python run.py
    
Or after installation:
    vor-fix-calculator
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import main

if __name__ == "__main__":
    main()

