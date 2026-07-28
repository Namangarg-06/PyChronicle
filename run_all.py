#!/usr/bin/env python3
"""
Run all Pychronicle projects together
"""

import subprocess
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def run_project(week_name, project_dir, script_file, args=None):
    """Run a specific project"""
    try:
        print(f"\nRunning {week_name}...")
        base_dir = Path(__file__).parent
        python_exe = str(base_dir / ".venv" / "Scripts" / "python.exe")
        
        cmd = [python_exe, str(script_file)]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = f"\n{'='*60}\n"
        output += f" {week_name} Output:\n"
        output += f"{'='*60}\n"
        
        if result.returncode == 0:
            output += f" {week_name} - COMPLETED SUCCESSFULLY!\n"
        else:
            output += f" {week_name} - ERROR!\n"
        
        if result.stdout:
            output += f"\nOutput:\n{result.stdout}\n"
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}\n"
            
        return week_name, output, result.returncode
    except subprocess.TimeoutExpired:
        return week_name, f"\n {week_name} - TIMEOUT\n", 1
    except Exception as e:
        return week_name, f"\n {week_name} - ERROR: {str(e)}\n", 1

def main():
    """Run all projects"""
    base_dir = Path(__file__).parent
    
    projects = [
        ("Week1", base_dir / "pychoweek1", base_dir / "pychoweek1" / "main.py", ["sample.py"]),
        ("Week2", base_dir / "Week2", base_dir / "Week2" / "run_week2.py", ["--no-ui"]),
        ("Week3", base_dir / "Week3", base_dir / "Week3" / "run_week3.py", ["--auto"]),
        ("Week4", base_dir / "Week4", base_dir / "Week4" / "run_week4.py", ["run", "--no-ui"]),
    ]
    
    print("STARTING ALL PROJECTS IN PARALLEL...")
    print("="*60)
    
    results = {}
    
    # Run all projects in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for week_name, project_dir, script_file, args in projects:
            if script_file.exists():
                future = executor.submit(run_project, week_name, project_dir, script_file, args)
                futures.append(future)
            else:
                print(f" {week_name} script not found: {script_file}")
        
        # Collect results
        for future in futures:
            week_name, output, returncode = future.result()
            results[week_name] = (output, returncode)
    
    # Print all results
    print("\n" + "="*60)
    print(" EXECUTION RESULTS")
    print("="*60)
    
    for week_name, (output, returncode) in results.items():
        print(output)
    
    # Final summary
    passed = sum(1 for _, rc in results.values() if rc == 0)
    total = len(results)
    
    print("\n" + "="*60)
    print(f" FINAL SUMMARY: {passed}/{total} projects executed successfully")
    print("="*60)
    
    if passed == total:
        print(" ALL PROJECTS RAN SUCCESSFULLY! ")
    else:
        print(f" {total - passed} project(s) failed")

if __name__ == "__main__":
    main()
