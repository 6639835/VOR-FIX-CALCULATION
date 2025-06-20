#!/usr/bin/env python3
"""
Accuracy Testing Module for VOR Fix Calculation

This module provides comprehensive testing and validation tools to ensure
maximum accuracy in navigation calculations.
"""

import sys
import os
import math
import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vor_fix_calculation import (
    Coordinates, CoordinateCalculator, MagneticDeclinationService,
    DISTANCE_TOLERANCE_M, ANGLE_TOLERANCE_DEG
)

@dataclass
class TestCase:
    """Represents a single test case for accuracy validation."""
    name: str
    start_coords: Coordinates
    azimuth: float
    distance_nm: float
    expected_end_coords: Optional[Coordinates] = None
    tolerance_m: float = DISTANCE_TOLERANCE_M

class AccuracyTester:
    """Comprehensive accuracy testing for navigation calculations."""
    
    def __init__(self):
        self.calculator = CoordinateCalculator()
        self.declination_service = MagneticDeclinationService()
        self.test_results: List[Dict] = []
    
    def create_standard_test_cases(self) -> List[TestCase]:
        """Create a comprehensive set of standard test cases."""
        test_cases = [
            # Short distance tests (high precision required)
            TestCase("Short distance - 1 NM", Coordinates(45.0, -75.0), 90.0, 1.0),
            TestCase("Short distance - 0.1 NM", Coordinates(45.0, -75.0), 45.0, 0.1),
            TestCase("Very short - 0.01 NM", Coordinates(45.0, -75.0), 180.0, 0.01),
            
            # Medium distance tests
            TestCase("Medium distance - 50 NM", Coordinates(40.7128, -74.0060), 270.0, 50.0),
            TestCase("Medium distance - 100 NM", Coordinates(51.5074, -0.1278), 45.0, 100.0),
            
            # Long distance tests
            TestCase("Long distance - 500 NM", Coordinates(35.6762, 139.6503), 225.0, 500.0),
            TestCase("Very long - 1000 NM", Coordinates(55.7558, 37.6176), 315.0, 1000.0),
            TestCase("Extreme - 2000 NM", Coordinates(-33.8688, 151.2093), 135.0, 2000.0),
            
            # Polar region tests (challenging for geodesic calculations)
            TestCase("Arctic - Svalbard", Coordinates(78.2232, 15.6267), 0.0, 100.0),
            TestCase("Antarctic", Coordinates(-77.8419, 166.6863), 180.0, 200.0),
            
            # Equatorial tests
            TestCase("Equatorial - Pacific", Coordinates(0.0, -160.0), 90.0, 300.0),
            TestCase("Equatorial - Atlantic", Coordinates(0.0, -30.0), 270.0, 400.0),
            
            # International Date Line crossing
            TestCase("Date Line West", Coordinates(35.0, 179.0), 90.0, 200.0),
            TestCase("Date Line East", Coordinates(35.0, -179.0), 270.0, 200.0),
            
            # Various azimuth tests
            TestCase("North (0°)", Coordinates(40.0, -100.0), 0.0, 100.0),
            TestCase("Northeast (45°)", Coordinates(40.0, -100.0), 45.0, 100.0),
            TestCase("East (90°)", Coordinates(40.0, -100.0), 90.0, 100.0),
            TestCase("Southeast (135°)", Coordinates(40.0, -100.0), 135.0, 100.0),
            TestCase("South (180°)", Coordinates(40.0, -100.0), 180.0, 100.0),
            TestCase("Southwest (225°)", Coordinates(40.0, -100.0), 225.0, 100.0),
            TestCase("West (270°)", Coordinates(40.0, -100.0), 270.0, 100.0),
            TestCase("Northwest (315°)", Coordinates(40.0, -100.0), 315.0, 100.0),
        ]
        return test_cases
    
    def run_accuracy_test(self, test_case: TestCase) -> Dict:
        """Run a single accuracy test and return detailed results."""
        print(f"Running test: {test_case.name}")
        
        # Calculate target coordinates
        start_time = datetime.datetime.now()
        calculated_coords = self.calculator.calculate_target_coords_geodesic(
            test_case.start_coords, test_case.azimuth, test_case.distance_nm
        )
        end_time = datetime.datetime.now()
        calculation_time = (end_time - start_time).total_seconds()
        
        # Validate the result
        validation = self.calculator.validate_calculation_accuracy(
            test_case.start_coords, calculated_coords, 
            test_case.azimuth, test_case.distance_nm
        )
        
        # Check against expected coordinates if provided
        expected_coords_error = None
        if test_case.expected_end_coords:
            from geographiclib.geodesic import Geodesic
            geodesic = Geodesic.WGS84
            result = geodesic.Inverse(
                calculated_coords.lat, calculated_coords.lon,
                test_case.expected_end_coords.lat, test_case.expected_end_coords.lon
            )
            expected_coords_error = result['s12']  # Distance in meters
        
        # Determine pass/fail status
        distance_pass = validation['distance_error_m'] <= test_case.tolerance_m
        azimuth_pass = validation['azimuth_error_deg'] <= ANGLE_TOLERANCE_DEG
        overall_pass = distance_pass and azimuth_pass
        
        result = {
            'test_name': test_case.name,
            'start_coords': test_case.start_coords,
            'calculated_coords': calculated_coords,
            'expected_azimuth': test_case.azimuth,
            'expected_distance_nm': test_case.distance_nm,
            'validation': validation,
            'calculation_time_s': calculation_time,
            'distance_pass': distance_pass,
            'azimuth_pass': azimuth_pass,
            'overall_pass': overall_pass,
            'expected_coords_error_m': expected_coords_error,
            'tolerance_m': test_case.tolerance_m
        }
        
        self.test_results.append(result)
        return result
    
    def run_comprehensive_test_suite(self) -> Dict:
        """Run the complete test suite and generate summary report."""
        print("Starting comprehensive accuracy test suite...")
        print("=" * 60)
        
        test_cases = self.create_standard_test_cases()
        results = []
        
        for test_case in test_cases:
            result = self.run_accuracy_test(test_case)
            results.append(result)
            
            # Print immediate result
            status = "PASS" if result['overall_pass'] else "FAIL"
            print(f"  {status}: Error {result['validation']['distance_error_m']:.3f}m, "
                  f"Azimuth {result['validation']['azimuth_error_deg']:.6f}°, "
                  f"Rating: {result['validation']['accuracy_rating']}")
        
        # Generate summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['overall_pass'])
        failed_tests = total_tests - passed_tests
        
        distance_errors = [r['validation']['distance_error_m'] for r in results]
        azimuth_errors = [r['validation']['azimuth_error_deg'] for r in results]
        calculation_times = [r['calculation_time_s'] for r in results]
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': (passed_tests / total_tests) * 100,
            'distance_error_stats': {
                'mean': sum(distance_errors) / len(distance_errors),
                'max': max(distance_errors),
                'min': min(distance_errors),
                'median': sorted(distance_errors)[len(distance_errors) // 2]
            },
            'azimuth_error_stats': {
                'mean': sum(azimuth_errors) / len(azimuth_errors),
                'max': max(azimuth_errors),
                'min': min(azimuth_errors),
                'median': sorted(azimuth_errors)[len(azimuth_errors) // 2]
            },
            'performance_stats': {
                'mean_time_s': sum(calculation_times) / len(calculation_times),
                'max_time_s': max(calculation_times),
                'min_time_s': min(calculation_times)
            }
        }
        
        print("\n" + "=" * 60)
        print("TEST SUITE SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"\nDistance Error Statistics:")
        print(f"  Mean: {summary['distance_error_stats']['mean']:.3f}m")
        print(f"  Max:  {summary['distance_error_stats']['max']:.3f}m")
        print(f"  Min:  {summary['distance_error_stats']['min']:.3f}m")
        print(f"\nAzimuth Error Statistics:")
        print(f"  Mean: {summary['azimuth_error_stats']['mean']:.6f}°")
        print(f"  Max:  {summary['azimuth_error_stats']['max']:.6f}°")
        print(f"  Min:  {summary['azimuth_error_stats']['min']:.6f}°")
        print(f"\nPerformance Statistics:")
        print(f"  Mean Time: {summary['performance_stats']['mean_time_s']:.6f}s")
        print(f"  Max Time:  {summary['performance_stats']['max_time_s']:.6f}s")
        print(f"  Min Time:  {summary['performance_stats']['min_time_s']:.6f}s")
        
        return summary
    
    def benchmark_intersection_accuracy(self, num_tests: int = 50) -> Dict:
        """Benchmark the accuracy of intersection calculations."""
        print(f"\nBenchmarking intersection accuracy with {num_tests} tests...")
        
        results = []
        
        for i in range(num_tests):
            # Generate random test case
            fix_lat = (i % 180) - 89  # -89 to 89
            fix_lon = ((i * 7) % 359) - 179  # -179 to 179
            dme_lat = ((i * 3) % 178) - 89  # -89 to 89
            dme_lon = ((i * 11) % 359) - 179  # -179 to 179
            
            fix_coords = Coordinates(fix_lat, fix_lon)
            dme_coords = Coordinates(dme_lat, dme_lon)
            
            bearing = (i * 13) % 360  # Random bearing
            distance_nm = 1 + (i % 500)  # 1 to 500 NM
            
            # Test would go here - this is a framework for intersection testing
            # For now, we'll record the parameters for future implementation
            results.append({
                'fix_coords': fix_coords,
                'dme_coords': dme_coords,
                'bearing': bearing,
                'distance_nm': distance_nm
            })
        
        print(f"Generated {len(results)} intersection test cases")
        return {'test_cases': results, 'count': len(results)}
    
    def export_results_to_csv(self, filename: str = "accuracy_test_results.csv") -> None:
        """Export test results to CSV file for analysis."""
        try:
            import csv
            with open(filename, 'w', newline='') as csvfile:
                if not self.test_results:
                    print("No test results to export")
                    return
                
                fieldnames = [
                    'test_name', 'start_lat', 'start_lon', 'calc_lat', 'calc_lon',
                    'expected_azimuth', 'expected_distance_nm', 'distance_error_m',
                    'azimuth_error_deg', 'accuracy_rating', 'calculation_time_s',
                    'overall_pass'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in self.test_results:
                    row = {
                        'test_name': result['test_name'],
                        'start_lat': result['start_coords'].lat,
                        'start_lon': result['start_coords'].lon,
                        'calc_lat': result['calculated_coords'].lat,
                        'calc_lon': result['calculated_coords'].lon,
                        'expected_azimuth': result['expected_azimuth'],
                        'expected_distance_nm': result['expected_distance_nm'],
                        'distance_error_m': result['validation']['distance_error_m'],
                        'azimuth_error_deg': result['validation']['azimuth_error_deg'],
                        'accuracy_rating': result['validation']['accuracy_rating'],
                        'calculation_time_s': result['calculation_time_s'],
                        'overall_pass': result['overall_pass']
                    }
                    writer.writerow(row)
                
                print(f"Results exported to {filename}")
        except ImportError:
            print("CSV module not available for export")
        except Exception as e:
            print(f"Error exporting results: {e}")

def main():
    """Main function to run accuracy tests."""
    print("VOR Fix Calculation - Accuracy Tester")
    print("=====================================")
    
    tester = AccuracyTester()
    
    # Run comprehensive test suite
    summary = tester.run_comprehensive_test_suite()
    
    # Run intersection benchmark
    intersection_results = tester.benchmark_intersection_accuracy()
    
    # Export results
    tester.export_results_to_csv()
    
    # Print recommendations
    print("\n" + "=" * 60)
    print("ACCURACY RECOMMENDATIONS")
    print("=" * 60)
    
    pass_rate = summary['pass_rate']
    mean_distance_error = summary['distance_error_stats']['mean']
    
    if pass_rate >= 95 and mean_distance_error <= 1.0:
        print("✅ EXCELLENT: Your calculations are highly accurate!")
    elif pass_rate >= 90 and mean_distance_error <= 5.0:
        print("✅ VERY GOOD: Minor improvements possible")
    elif pass_rate >= 80:
        print("⚠️  GOOD: Some accuracy improvements recommended")
    else:
        print("❌ NEEDS IMPROVEMENT: Significant accuracy issues detected")
    
    print(f"\nKey Metrics:")
    print(f"- Pass Rate: {pass_rate:.1f}%")
    print(f"- Mean Distance Error: {mean_distance_error:.3f}m")
    print(f"- Max Distance Error: {summary['distance_error_stats']['max']:.3f}m")
    
    print(f"\nTo improve accuracy further:")
    print(f"1. Ensure GeographicLib >= 2.0 is installed")
    print(f"2. Verify pygeomag is properly configured")
    print(f"3. Use the highest precision settings available")
    print(f"4. Consider environmental factors (temperature, pressure)")
    print(f"5. Validate input data quality")

if __name__ == "__main__":
    main() 