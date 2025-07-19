#!/usr/bin/env python3
"""
Bug Analysis and Testing Script for VOR Fix Calculation

This script identifies and tests for potential bugs in the VOR calculation system
without requiring tkinter or GUI components.
"""

import sys
import os
import math
import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core calculation classes without tkinter dependencies
try:
    from core_vor_calc import (
        Coordinates, CoordinateCalculator, MagneticDeclinationService,
        InputValidator, NavigationDataService, DISTANCE_TOLERANCE_M, 
        ANGLE_TOLERANCE_DEG, METERS_PER_NM, MAX_ITERATIONS,
        NEWTON_RAPHSON_TOLERANCE_M, GRADIENT_STEP_SIZE, MIN_SEARCH_RANGE_NM,
        FileType
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False

class BugTester:
    """Comprehensive bug testing for the VOR calculation system."""
    
    def __init__(self):
        if not IMPORTS_AVAILABLE:
            print("Core imports not available - limited testing possible")
            return
        self.test_results = []
        self.bugs_found = []
        
    def test_division_by_zero_scenarios(self):
        """Test for potential division by zero bugs."""
        print("Testing division by zero scenarios...")
        
        if not IMPORTS_AVAILABLE:
            return ["Import not available - cannot test"]
        
        bugs_found = []
        
        # Test 1: Zero distance conversion
        try:
            calc = CoordinateCalculator()
            result = calc.meters_to_nm(0)
            assert result == 0, "Zero meters should convert to zero nautical miles"
        except ZeroDivisionError:
            bugs_found.append("Division by zero in meters_to_nm with zero input")
        except Exception as e:
            bugs_found.append(f"Unexpected error in meters_to_nm: {e}")
        
        # Test 2: Very small numbers
        try:
            calc = CoordinateCalculator()
            result = calc.nm_to_meters(1e-15)  # Very small number
            # Should not cause issues
        except Exception as e:
            bugs_found.append(f"Error with very small distance: {e}")
        
        # Test 3: Test constant validation
        try:
            from core_vor_calc import _validate_constants
            _validate_constants()
        except Exception as e:
            bugs_found.append(f"Constants validation failed: {e}")
        
        print(f"  Found {len(bugs_found)} division by zero related issues")
        return bugs_found
    
    def test_coordinate_edge_cases(self):
        """Test coordinate validation edge cases."""
        print("Testing coordinate edge cases...")
        
        if not IMPORTS_AVAILABLE:
            return ["Import not available - cannot test"]
        
        bugs_found = []
        
        # Test cases that might cause issues
        edge_cases = [
            (90.0, 0.0, "North Pole"),
            (-90.0, 0.0, "South Pole"),
            (0.0, 180.0, "International Date Line East"),
            (0.0, -180.0, "International Date Line West"),
            (89.999999, 179.999999, "Near North Pole, near date line"),
            (-89.999999, -179.999999, "Near South Pole, near date line"),
        ]
        
        for lat, lon, description in edge_cases:
            try:
                coords = Coordinates(lat, lon)
                # Test basic operations
                calc = CoordinateCalculator()
                result = calc.calculate_target_coords_geodesic(coords, 45.0, 1.0)
            except Exception as e:
                bugs_found.append(f"Coordinate edge case failure ({description}): {e}")
        
        # Test invalid coordinates
        invalid_cases = [
            (91.0, 0.0, "Latitude too high"),
            (-91.0, 0.0, "Latitude too low"),
            (0.0, 181.0, "Longitude too high"),
            (0.0, -181.0, "Longitude too low"),
        ]
        
        for lat, lon, description in invalid_cases:
            try:
                coords = Coordinates(lat, lon)
                bugs_found.append(f"Invalid coordinates accepted ({description})")
            except ValueError:
                # This is expected behavior
                pass
            except Exception as e:
                bugs_found.append(f"Unexpected error for invalid coordinates ({description}): {e}")
        
        print(f"  Found {len(bugs_found)} coordinate-related issues")
        return bugs_found
    
    def test_input_validation_bugs(self):
        """Test input validation for potential bugs."""
        print("Testing input validation...")
        
        if not IMPORTS_AVAILABLE:
            return ["Import not available - cannot test"]
        
        bugs_found = []
        
        # Test coordinate validation edge cases
        test_cases = [
            ("", "Empty string"),
            ("45.0", "Single number"),
            ("45.0 -75.0 extra", "Too many numbers"),
            ("not_a_number -75.0", "Invalid number"),
            ("45.0 not_a_number", "Invalid second number"),
            ("91.0 -75.0", "Invalid latitude"),
            ("45.0 -181.0", "Invalid longitude"),
        ]
        
        for coords_str, description in test_cases:
            try:
                result = InputValidator.validate_coordinates(coords_str)
                if description in ["Empty string", "Single number", "Too many numbers", 
                                 "Invalid number", "Invalid second number", 
                                 "Invalid latitude", "Invalid longitude"]:
                    bugs_found.append(f"Invalid coordinates accepted: {description}")
            except ValueError:
                # Expected for invalid inputs
                pass
            except Exception as e:
                bugs_found.append(f"Unexpected error in coordinate validation ({description}): {e}")
        
        # Test bearing validation
        bearing_cases = [
            ("", "Empty bearing"),
            ("360", "Bearing equals 360"),
            ("-1", "Negative bearing"),
            ("not_a_number", "Invalid bearing format"),
        ]
        
        for bearing_str, description in bearing_cases:
            try:
                result = InputValidator.validate_bearing(bearing_str)
                if description in ["Empty bearing", "Bearing equals 360", "Negative bearing", "Invalid bearing format"]:
                    bugs_found.append(f"Invalid bearing accepted: {description}")
            except ValueError:
                # Expected for invalid inputs
                pass
            except Exception as e:
                bugs_found.append(f"Unexpected error in bearing validation ({description}): {e}")
        
        print(f"  Found {len(bugs_found)} input validation issues")
        return bugs_found
    
    def test_iteration_limits(self):
        """Test for potential infinite loops in iterative algorithms."""
        print("Testing iteration limits...")
        
        if not IMPORTS_AVAILABLE:
            return ["Import not available - cannot test"]
        
        bugs_found = []
        
        try:
            # Test with conditions that might cause convergence issues
            calc = CoordinateCalculator()
            
            # Test very long distance calculation
            start_coords = Coordinates(0.0, 0.0)
            
            # This should complete within reasonable time
            import time
            start_time = time.time()
            result = calc.calculate_target_coords_geodesic(start_coords, 45.0, 10000.0)  # Very long distance
            elapsed = time.time() - start_time
            
            if elapsed > 10.0:  # If it takes more than 10 seconds, it might be problematic
                bugs_found.append(f"Very long calculation time for long distance: {elapsed:.2f}s")
                
        except Exception as e:
            bugs_found.append(f"Error in long distance calculation: {e}")
        
        print(f"  Found {len(bugs_found)} iteration-related issues")
        return bugs_found
    
    def test_precision_edge_cases(self):
        """Test numerical precision edge cases."""
        print("Testing precision edge cases...")
        
        if not IMPORTS_AVAILABLE:
            return ["Import not available - cannot test"]
        
        bugs_found = []
        
        try:
            calc = CoordinateCalculator()
            
            # Test very small distances
            start_coords = Coordinates(45.0, -75.0)
            
            # Test extremely small distance
            result = calc.calculate_target_coords_geodesic(start_coords, 90.0, 1e-10)
            
            # Verify the result is reasonable (should be very close to start)
            if abs(result.lat - start_coords.lat) > 1e-6 or abs(result.lon - start_coords.lon) > 1e-6:
                bugs_found.append("Very small distance calculation produced unreasonable result")
                
            # Test precision with validation
            validation = calc.validate_calculation_accuracy(start_coords, result, 90.0, 1e-10)
            if validation['distance_error_m'] > 1.0:  # More than 1 meter error for tiny distance
                bugs_found.append(f"Poor precision for very small distance: {validation['distance_error_m']:.6f}m error")
        
        except Exception as e:
            bugs_found.append(f"Error in precision testing: {e}")
        
        print(f"  Found {len(bugs_found)} precision-related issues")
        return bugs_found
    
    def test_memory_leaks(self):
        """Test for potential memory leaks."""
        print("Testing memory usage patterns...")
        
        if not IMPORTS_AVAILABLE:
            return ["Import not available - cannot test"]
        
        bugs_found = []
        
        # This is a basic test - in a real scenario we'd use memory profiling tools
        try:
            calc = CoordinateCalculator()
            
            # Perform many calculations to see if memory grows excessively
            for i in range(1000):
                coords = Coordinates(float(i % 90), float(i % 180))
                result = calc.calculate_target_coords_geodesic(coords, float(i % 360), 1.0)
            
            # If we get here without issues, that's good
            
        except MemoryError:
            bugs_found.append("Memory error during repeated calculations")
        except Exception as e:
            bugs_found.append(f"Error during memory test: {e}")
        
        print(f"  Found {len(bugs_found)} memory-related issues")
        return bugs_found
    
    def test_file_parsing_safety(self):
        """Test file parsing for potential crashes."""
        print("Testing file parsing safety...")
        
        if not IMPORTS_AVAILABLE:
            return ["Import not available - cannot test"]
        
        bugs_found = []
        
        try:
            nav_service = NavigationDataService()
            
            # Test with empty file path  
            try:
                result = nav_service.search_identifier("TEST", FileType.NAV)
                bugs_found.append("Search succeeded with no file path set")
            except FileNotFoundError:
                # Expected behavior
                pass
            except Exception as e:
                bugs_found.append(f"Unexpected error with empty file path: {e}")
        
        except Exception as e:
            bugs_found.append(f"Error testing navigation data service: {e}")
        
        print(f"  Found {len(bugs_found)} file parsing issues")
        return bugs_found
    
    def run_all_tests(self):
        """Run all bug detection tests."""
        print("Starting comprehensive bug analysis...")
        print("=" * 50)
        
        all_bugs = []
        
        all_bugs.extend(self.test_division_by_zero_scenarios())
        all_bugs.extend(self.test_coordinate_edge_cases())
        all_bugs.extend(self.test_input_validation_bugs())
        all_bugs.extend(self.test_iteration_limits())
        all_bugs.extend(self.test_precision_edge_cases())
        all_bugs.extend(self.test_memory_leaks())
        all_bugs.extend(self.test_file_parsing_safety())
        
        print("\n" + "=" * 50)
        print("BUG ANALYSIS SUMMARY")
        print("=" * 50)
        
        if not all_bugs:
            print("✅ No obvious bugs detected!")
        else:
            print(f"❌ Found {len(all_bugs)} potential issues:")
            for i, bug in enumerate(all_bugs, 1):
                print(f"{i:2d}. {bug}")
        
        self.bugs_found = all_bugs
        return all_bugs

def main():
    """Main function to run bug analysis."""
    print("VOR Fix Calculation - Bug Analysis")
    print("==================================")
    
    tester = BugTester()
    bugs = tester.run_all_tests()
    
    print(f"\nAnalysis complete. Found {len(bugs)} potential issues.")
    
    if bugs:
        print("\nRecommendations:")
        print("1. Review and fix the identified issues")
        print("2. Add more comprehensive error handling")
        print("3. Implement bounds checking for all array access")
        print("4. Add convergence checks for iterative algorithms")
        print("5. Consider adding logging for debugging")
    
    return len(bugs)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(min(exit_code, 1))  # Return 1 if any bugs found, 0 otherwise