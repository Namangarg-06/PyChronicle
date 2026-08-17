#!/usr/bin/env python3
"""
Check all Pychronicle projects together - Run all tests
"""

import subprocess
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

def run_tests(week_name, test_dir, test_file):
    """Run tests for a specific week"""
    try:
        print(f"\n🧪 Testing {week_name}...")
        python_exe = sys.executable # Use the current Python executable
        
        # For Week1 (unittest), use unittest discovery
        if week_name == "Week1":
            result = subprocess.run(
                [python_exe, "-m", "unittest", "test_chronicle", "-v"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
        else:
            # For Week2-4 (pytest), use pytest
            result = subprocess.run(
                [python_exe, "-m", "pytest", str(test_file), "-v"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
        
        output = f"\n{'='*60}\n"
        output += f"📋 {week_name} Tests\n"
        output += f"{'='*60}\n"
        
        if result.returncode == 0:
            output += f"✅ {week_name} - ALL TESTS PASSED!\n"
        else:
            output += f"❌ {week_name} - TESTS FAILED!\n"
        
        if result.stdout:
            output += f"\nOutput:\n{result.stdout}\n"
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}\n"
            
        return week_name, output, result.returncode
    except subprocess.TimeoutExpired:
        return week_name, f"\n❌ {week_name} - TIMEOUT\n", 1
    except Exception as e:
        return week_name, f"\n❌ {week_name} - ERROR: {str(e)}\n", 1

def main():
    """Run all tests"""
    base_dir = Path(__file__).parent
    
    tests = [
        ("Week1", base_dir / "pychoweek1", base_dir / "pychoweek1" / "test_chronicle.py"),
        ("Week2", base_dir / "Week2", base_dir / "Week2" / "tests" / "test_delta_and_replay.py"),
        ("Week3", base_dir / "Week3", base_dir / "Week3" / "tests" / "test_delta_and_replay.py"),
        ("Week4", base_dir / "Week4", base_dir / "Week4" / "tests" / "test_week4_cli.py"),
    ]
    
    print("🚀 STARTING ALL TESTS IN PARALLEL...")
    print("="*60)
    
    results = {}
    
    # Run all tests in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for week_name, test_dir, test_file in tests:
            if test_file.exists():
                future = executor.submit(run_tests, week_name, test_dir, test_file)
                futures.append(future)
            else:
                print(f"⚠️  {week_name} test file not found: {test_file}")
        
        # Collect results
        for future in futures:
            week_name, output, returncode = future.result()
            results[week_name] = (output, returncode)
    
    # Print all results
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    for week_name, (output, returncode) in results.items():
        print(output)
    
    # Final summary
    passed = sum(1 for _, rc in results.values() if rc == 0)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"🎯 FINAL SUMMARY: {passed}/{total} weeks passed")
    print("="*60)
    
    if passed == total:
        print("✅ ALL TESTS PASSED! 🎉")
    else:
        print(f"❌ {total - passed} week(s) failed")

if __name__ == "__main__":
    main()
