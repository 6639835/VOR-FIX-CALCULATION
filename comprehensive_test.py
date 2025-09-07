#!/usr/bin/env python3
"""
Comprehensive test of the fixed VOR calculation system.
"""

import sys
import os
import time

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_vor_calc import (
    Coordinates, CoordinateCalculator, MagneticDeclinationService,
    InputValidator, NavigationDataService, FileType
)

def run_comprehensive_tests():
    """Run comprehensive tests to ensure the system works correctly."""
    print("Running comprehensive VOR calculation tests...")
    print("=" * 50)
    
    test_count = 0
    passed_count = 0
    
    # Test 1: Coordinate boundary validation
    print("Test 1: Coordinate validation")
    test_count += 1
    try:
        # Test all boundary conditions
        coords_tests = [
            (0.0, 0.0, True),      # Equator/Prime meridian
            (90.0, 0.0, True),     # North pole
            (-90.0, 0.0, True),    # South pole
            (0.0, 180.0, True),    # Date line east
            (0.0, -180.0, True),   # Date line west (FIXED!)
            (45.0, -75.0, True),   # Normal coordinates
            (91.0, 0.0, False),    # Invalid lat (too high)
            (-91.0, 0.0, False),   # Invalid lat (too low)
            (0.0, 181.0, False),   # Invalid lon (too high)
            (0.0, -181.0, False),  # Invalid lon (too low)
        ]
        
        all_coord_tests_passed = True
        for lat, lon, should_work in coords_tests:
            try:
                coords = Coordinates(lat, lon)
                if not should_work:
                    print(f"  ❌ Expected failure for ({lat}, {lon}) but it passed")
                    all_coord_tests_passed = False
            except ValueError:
                if should_work:
                    print(f"  ❌ Expected success for ({lat}, {lon}) but it failed")
                    all_coord_tests_passed = False
        
        if all_coord_tests_passed:
            print("  ✅ All coordinate validation tests passed")
            passed_count += 1
        else:
            print("  ❌ Some coordinate validation tests failed")
    except Exception as e:
        print(f"  ❌ Coordinate test crashed: {e}")
    
    # Test 2: Basic calculations
    print("\nTest 2: Basic coordinate calculations")
    test_count += 1
    try:
        calc = CoordinateCalculator()
        start = Coordinates(45.0, -75.0)
        
        # Test in all cardinal directions
        directions = [
            (0.0, "North"),
            (90.0, "East"), 
            (180.0, "South"),
            (270.0, "West")
        ]
        
        all_calc_tests_passed = True
        for bearing, direction in directions:
            result = calc.calculate_target_coords_geodesic(start, bearing, 1.0)
            
            # Verify basic directional logic
            if bearing == 0.0 and result.lat <= start.lat:  # North should increase lat
                all_calc_tests_passed = False
                print(f"  ❌ {direction} calculation: lat didn't increase")
            elif bearing == 180.0 and result.lat >= start.lat:  # South should decrease lat
                all_calc_tests_passed = False
                print(f"  ❌ {direction} calculation: lat didn't decrease")
            elif bearing == 90.0 and result.lon <= start.lon:  # East should increase lon
                all_calc_tests_passed = False
                print(f"  ❌ {direction} calculation: lon didn't increase")
            elif bearing == 270.0 and result.lon >= start.lon:  # West should decrease lon
                all_calc_tests_passed = False
                print(f"  ❌ {direction} calculation: lon didn't decrease")
        
        if all_calc_tests_passed:
            print("  ✅ All basic calculation tests passed")
            passed_count += 1
        else:
            print("  ❌ Some basic calculation tests failed")
    except Exception as e:
        print(f"  ❌ Basic calculation test crashed: {e}")
    
    # Test 3: Precision metrics with edge cases
    print("\nTest 3: Precision metrics")
    test_count += 1
    try:
        # Test empty list (FIXED!)
        result = CoordinateCalculator.calculate_precision_metrics([])
        if result['total_calculations'] == 0:
            print("  ✅ Empty list handled correctly")
            
            # Test with actual data
            start = Coordinates(40.0, -74.0)
            end = Coordinates(40.001, -74.0)
            test_data = [(start, end, 0.0, 0.1)]
            result2 = CoordinateCalculator.calculate_precision_metrics(test_data)
            
            if result2['total_calculations'] == 1:
                print("  ✅ Normal precision calculation works")
                passed_count += 1
            else:
                print("  ❌ Normal precision calculation failed")
        else:
            print("  ❌ Empty list not handled correctly")
    except Exception as e:
        print(f"  ❌ Precision metrics test crashed: {e}")
    
    # Test 4: Input validation robustness
    print("\nTest 4: Input validation")
    test_count += 1
    try:
        validation_tests = [
            ("45.0 -75.0", True, "Valid coordinates"),
            ("", False, "Empty string"),
            ("45.0", False, "Single number"),
            ("45.0 -75.0 extra", False, "Too many numbers"),
            ("not_a_number -75.0", False, "Invalid number"),
            ("91.0 -75.0", False, "Invalid latitude"),
            ("45.0 -181.0", False, "Invalid longitude"),
        ]
        
        all_validation_passed = True
        for coords_str, should_work, description in validation_tests:
            try:
                result = InputValidator.validate_coordinates(coords_str)
                if not should_work:
                    print(f"  ❌ {description}: Expected failure but got success")
                    all_validation_passed = False
            except ValueError:
                if should_work:
                    print(f"  ❌ {description}: Expected success but got failure")
                    all_validation_passed = False
        
        if all_validation_passed:
            print("  ✅ All input validation tests passed")
            passed_count += 1
        else:
            print("  ❌ Some input validation tests failed")
    except Exception as e:
        print(f"  ❌ Input validation test crashed: {e}")
    
    # Test 5: Performance test
    print("\nTest 5: Performance")
    test_count += 1
    try:
        calc = CoordinateCalculator()
        start_time = time.time()
        
        # Perform 100 calculations
        for i in range(100):
            start = Coordinates(float(i % 90), float(i % 180))
            result = calc.calculate_target_coords_geodesic(start, float(i % 360), 1.0)
        
        elapsed = time.time() - start_time
        
        if elapsed < 5.0:  # Should complete within 5 seconds
            print(f"  ✅ Performance test passed ({elapsed:.3f}s for 100 calculations)")
            passed_count += 1
        else:
            print(f"  ❌ Performance test failed ({elapsed:.3f}s for 100 calculations)")
    except Exception as e:
        print(f"  ❌ Performance test crashed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {passed_count}/{test_count}")
    
    if passed_count == test_count:
        print("🎉 ALL TESTS PASSED - System is working correctly!")
        return 0
    else:
        print("⚠️  Some tests failed - additional investigation needed")
        return 1

if __name__ == "__main__":
    exit_code = run_comprehensive_tests()
    sys.exit(exit_code)