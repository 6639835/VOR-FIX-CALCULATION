#!/usr/bin/env python3
"""
Test script to verify that the bug fixes work correctly.
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_vor_calc import Coordinates, CoordinateCalculator

def test_longitude_boundary_fix():
    """Test that -180.0 longitude is now accepted."""
    print("Testing longitude boundary fix...")
    
    try:
        # Test exact boundary cases
        coords1 = Coordinates(0.0, -180.0)  # Should work now
        coords2 = Coordinates(0.0, 180.0)   # Should still work
        coords3 = Coordinates(0.0, 0.0)     # Should still work
        
        print("✅ All boundary longitude values accepted")
        return True
    except ValueError as e:
        print(f"❌ Longitude boundary test failed: {e}")
        return False

def test_precision_metrics_fix():
    """Test that precision metrics calculation handles empty lists."""
    print("Testing precision metrics fix...")
    
    try:
        calc = CoordinateCalculator()
        
        # Test with empty list (should not crash)
        result = CoordinateCalculator.calculate_precision_metrics([])
        
        # Verify that it returns proper default values
        expected_keys = [
            'mean_distance_error_m', 'max_distance_error_m', 'min_distance_error_m',
            'mean_azimuth_error_deg', 'max_azimuth_error_deg', 'min_azimuth_error_deg',
            'total_calculations'
        ]
        
        for key in expected_keys:
            if key not in result:
                print(f"❌ Missing key in result: {key}")
                return False
            if result[key] != 0.0 and result[key] != 0:
                print(f"❌ Expected 0 for key {key}, got {result[key]}")
                return False
        
        print("✅ Empty list handled correctly")
        
        # Test with actual data to ensure normal operation still works
        coords1 = Coordinates(45.0, -75.0)
        coords2 = Coordinates(45.001, -75.0)  # Slightly different
        
        test_data = [(coords1, coords2, 0.0, 0.1)]
        result2 = CoordinateCalculator.calculate_precision_metrics(test_data)
        
        if result2['total_calculations'] != 1:
            print("❌ Normal precision calculation broken")
            return False
            
        print("✅ Normal precision calculation still works")
        return True
        
    except Exception as e:
        print(f"❌ Precision metrics test failed: {e}")
        return False

def test_coordinate_calculations():
    """Test that coordinate calculations still work correctly after fixes."""
    print("Testing coordinate calculations...")
    
    try:
        calc = CoordinateCalculator()
        
        # Test basic calculation
        start = Coordinates(45.0, -75.0)
        result = calc.calculate_target_coords_geodesic(start, 90.0, 1.0)
        
        # Verify result is reasonable (should be east of start point)
        if result.lon <= start.lon:
            print("❌ Expected eastward movement")
            return False
        
        # Test validation
        validation = calc.validate_calculation_accuracy(start, result, 90.0, 1.0)
        if 'distance_error_m' not in validation:
            print("❌ Validation missing distance error")
            return False
            
        print("✅ Coordinate calculations working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Coordinate calculation test failed: {e}")
        return False

def test_edge_cases():
    """Test various edge cases to ensure robustness."""
    print("Testing edge cases...")
    
    try:
        calc = CoordinateCalculator()
        
        # Test very small distances
        start = Coordinates(0.0, 0.0)
        result = calc.calculate_target_coords_geodesic(start, 0.0, 1e-10)
        
        # Should be very close to start
        if abs(result.lat - start.lat) > 1e-6 or abs(result.lon - start.lon) > 1e-6:
            print("❌ Very small distance calculation issue")
            return False
        
        # Test polar regions
        polar_start = Coordinates(89.0, 0.0)
        polar_result = calc.calculate_target_coords_geodesic(polar_start, 0.0, 1.0)
        
        # Should move towards north pole
        if polar_result.lat <= polar_start.lat:
            print("❌ Polar region calculation issue")
            return False
        
        print("✅ Edge cases handled correctly")
        return True
        
    except Exception as e:
        print(f"❌ Edge case test failed: {e}")
        return False

def main():
    """Run all fix verification tests."""
    print("VOR Fix Calculation - Fix Verification Tests")
    print("===========================================")
    
    tests = [
        test_longitude_boundary_fix,
        test_precision_metrics_fix,
        test_coordinate_calculations,
        test_edge_cases
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All fixes verified successfully!")
        return 0
    else:
        print("⚠️  Some tests failed - additional fixes may be needed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)