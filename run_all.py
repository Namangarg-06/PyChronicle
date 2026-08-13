#!/usr/bin/env python3
"""
Run all Pychronicle projects together
"""

import subprocess
import os
import tempfile
import webbrowser
import html
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


def truncate_text(text, max_lines=20, max_chars=2000):
    if not text:
        return ""
    # prefer line-based truncation
    lines = text.splitlines()
    if len(lines) > max_lines:
        truncated = "\n".join(lines[:max_lines])
        return truncated + f"\n... (truncated, total {len(lines)} lines)"
    if len(text) > max_chars:
        return text[:max_chars] + f"\n... (truncated, total {len(text)} chars)"
    return text

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
        
        # Build full raw output and save to temp file for full inspection
        status_text = "COMPLETED SUCCESSFULLY" if result.returncode == 0 else "ERROR"
        full_parts = ["="*60, f" {week_name} Output:", "="*60, f"Status: {status_text}"]
        if result.stdout:
            full_parts.append("Stdout:\n" + result.stdout)
        if result.stderr:
            full_parts.append("Stderr:\n" + result.stderr)
        full_output = "\n".join(full_parts)

        # save full output to temp file
        temp_dir = tempfile.gettempdir()
        log_file = Path(temp_dir) / f"pychronicle_{week_name}_full_output.txt"
        try:
            log_file.write_text(full_output, encoding="utf-8")
        except Exception:
            # best-effort; ignore write failures
            pass

        # Build a concise, truncated output for console and HTML preview
        parts = [f"{week_name} - {status_text}"]
        if result.stdout:
            parts.append("Stdout:\n" + truncate_text(result.stdout))
        if result.stderr:
            parts.append("Stderr:\n" + truncate_text(result.stderr))

        output = "\n".join(parts)
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

    # Generate HTML report and open it in the browser
    report_html = generate_html_report(results, passed, total)
    report_file = save_html_report(report_html)
    webbrowser.open_new_tab(report_file)


def generate_html_report(results, passed, total):
    rows = []
    for week_name, (output, returncode) in results.items():
        status = "SUCCESS" if returncode == 0 else "FAIL"
        # Extract truncated Stdout and Stderr for preview
        stdout = ""
        stderr = ""
        if "Stdout:" in output:
            after = output.split("Stdout:", 1)[1]
            if "Stderr:" in after:
                stdout, stderr = after.split("Stderr:", 1)
            else:
                stdout = after
        elif "Stderr:" in output:
            stderr = output.split("Stderr:", 1)[1]
        else:
            stdout = output

        # link to full log if present
        temp_dir = tempfile.gettempdir()
        log_path = Path(temp_dir) / f"pychronicle_{week_name}_full_output.txt"
        log_link = ""
        try:
            if log_path.exists():
                log_link = f"<a href=\"{log_path.as_uri()}\" target=\"_blank\">Full log</a>"
        except Exception:
            log_link = ""

        rows.append(
            f"<tr>"
            f"<td>{week_name}</td>"
            f"<td class=\"{'success' if returncode==0 else 'fail'}\">{status}</td>"
            f"<td><pre>{html.escape(stdout.strip())}</pre></td>"
            f"<td><pre>{html.escape(stderr.strip())}</pre></td>"
            f"<td>{log_link}</td>"
            f"</tr>"
        )

    summary = f"{passed}/{total} successful"
    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Pychronicle Run Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }}
        th {{ background: #f4f4f4; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; margin: 0; }}
        .success {{ color: green; font-weight: bold; }}
        .fail {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Pychronicle Run Report</h1>
    <p><strong>Summary:</strong> {summary}</p>
    <table>
        <thead>
            <tr><th>Project</th><th>Status</th><th>Stdout</th><th>Stderr</th><th>Full Log</th></tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</body>
</html>
"""


def save_html_report(html_content):
    temp_dir = tempfile.gettempdir()
    report_file = Path(temp_dir) / "pychronicle_run_report.html"
    report_file.write_text(html_content, encoding="utf-8")
    return report_file.as_uri()


if __name__ == "__main__":
    main()


