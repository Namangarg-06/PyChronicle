"""
Run all Pychronicle projects together
"""

import sys
import subprocess
import os
import tempfile
import webbrowser
import html
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import threading
import argparse
import jinja2
import io
from typing import List, Optional


@dataclass
class Project:
    """Represents a Pychronicle project to be executed."""
    name: str
    directory: Path
    script: Path
    args: Optional[List[str]] = None

def truncate_text(text: str, max_lines: int = 20, max_chars: int = 2000) -> str: # Removed type: ignore
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

def run_project(week_name, project_dir, script_file, args=None, output_dir: Optional[Path] = None):
    """Run a specific project with real-time output streaming and save logs to output_dir."""
    print(f"\nRunning {week_name}...")
    python_exe = sys.executable
    
    cmd = [python_exe, str(script_file)]
    if args:
        cmd.extend(args)
    
    stdout_lines = []
    stderr_lines = []
    process = None

    def _read_stream(stream, buffer_list):
        """Helper function to read lines from a stream and append to a list."""
        for line in stream:
            buffer_list.append(line)

    try:
        process = subprocess.Popen(
            cmd,
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1 # Line-buffered output
        )

        # Create threads to read stdout and stderr
        stdout_thread = threading.Thread(target=_read_stream, args=(process.stdout, stdout_lines))
        stderr_thread = threading.Thread(target=_read_stream, args=(process.stderr, stderr_lines))

        stdout_thread.start()
        stderr_thread.start()

        # Wait for the process to terminate, with a timeout
        process.wait(timeout=60) # Corrected syntax: removed extra ')'
        
        # Build full raw output and save to temp file for full inspection
        status_text = "COMPLETED SUCCESSFULLY" if process.returncode == 0 else "ERROR" # Use process.returncode
        full_parts = ["="*60, f" {week_name} Output:", "="*60, f"Status: {status_text}"]
        
        # Ensure reader threads have finished before processing output
        stdout_thread.join()
        stderr_thread.join()

        stdout_str = "".join(stdout_lines)
        stderr_str = "".join(stderr_lines)

        if stdout_str:
            full_parts.append("Stdout:\n" + stdout_str)
        if stderr_str:
            full_parts.append("Stderr:\n" + stderr_str)
        full_output = "\n".join(full_parts)

        # Build a concise, truncated output for console and HTML preview
        parts = [f"{week_name} - {status_text}"]
        if stdout_str:
            parts.append("Stdout:\n" + truncate_text(stdout_str))
        if stderr_str:
            parts.append("Stderr:\n" + truncate_text(stderr_str))

        output = "\n".join(parts)
        return week_name, stdout_str, stderr_str, process.returncode
    except subprocess.TimeoutExpired:
        if process:
            process.kill()
            # Ensure threads are joined even if process is killed
            stdout_thread.join()
            stderr_thread.join()
        return week_name, "", f"\n {week_name} - TIMEOUT\n", 1
    except Exception as e:
        if process:
            process.kill()
            # Ensure threads are joined even if process is killed
            stdout_thread.join()
            stderr_thread.join()
        return week_name, "", f"\n {week_name} - ERROR: {str(e)}\n", 1

def get_projects(base_dir: Path) -> List[Project]:
    """Returns a list of all Pychronicle projects to run."""
    return [
        Project(
            name="Week1",
            directory=base_dir / "pychoweek1",
            script=base_dir / "pychoweek1" / "main.py",
            args=["sample.py"],
        ),
        Project(
            name="Week2",
            directory=base_dir / "Week2",
            script=base_dir / "Week2" / "run_week2.py",
            args=["--no-ui"],
        ),
        Project(
            name="Week3",
            directory=base_dir / "Week3",
            script=base_dir / "Week3" / "run_week3.py",
            args=["--auto"],
        ),
        Project(
            name="Week4",
            directory=base_dir / "Week4",
            script=base_dir / "Week4" / "run_week4.py",
            args=["run", "--no-ui"],
        ),
    ]

def parse_args():
    """Parses command-line arguments for project selection."""
    parser = argparse.ArgumentParser(description="Run selected Pychronicle projects.")
    parser.add_argument(
        "--projects",
        nargs="*", # 0 or more arguments
        default=None,
        help="Specify which projects to run (e.g., Week1 Week3). If not specified, all projects will run."
    )
    parser.add_argument(
        "--skip-ui",
        action="store_true",
        help="Do not open the HTML report in a web browser automatically."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save HTML report and log files. Defaults to a temporary directory."
    )

    return parser.parse_args()

def main():
    """Run all projects"""
    args = parse_args()
    base_dir = Path(__file__).parent
    all_projects = get_projects(base_dir)
    
    if args.projects:
        selected_project_names = {p.lower() for p in args.projects}
        projects_to_run = [p for p in all_projects if p.name.lower() in selected_project_names]
        print(f"STARTING SELECTED PROJECTS IN PARALLEL: {', '.join([p.name for p in projects_to_run])}...")
    else:
        projects_to_run = all_projects
        print("STARTING ALL PROJECTS IN PARALLEL...")

    # Determine and create output directory
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        output_dir = Path(tempfile.gettempdir()) / "pychronicle_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving reports and logs to: {output_dir}")
    print("="*60)
    
    results = {}
    
    # Run all projects in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for proj in projects_to_run:
            if proj.script.exists():
                future = executor.submit(run_project, proj.name, proj.directory, proj.script, proj.args, output_dir)
                futures.append(future)
            else:
                print(f" {proj.name} script not found: {proj.script}")
        
        # Collect results
        for future in futures:
            week_name, stdout_str, stderr_str, returncode = future.result()
            results[week_name] = (stdout_str, stderr_str, returncode)
    
    # Print all results
    print("\n" + "="*60)
    print(" EXECUTION RESULTS")
    print("="*60)
    
    for week_name, (stdout_str, stderr_str, returncode) in results.items():
        print(f"\n{week_name} - {'SUCCESS' if returncode == 0 else 'ERROR'}\nStdout:\n{truncate_text(stdout_str)}\nStderr:\n{truncate_text(stderr_str)}")
    
    # Final summary
    passed = sum(1 for _, _, rc in results.values() if rc == 0)
    total = len(results)
    
    print("\n" + "="*60)
    print(f" FINAL SUMMARY: {passed}/{total} projects executed successfully")
    print("="*60)
    
    if passed == total:
        print(" ALL PROJECTS RAN SUCCESSFULLY! ")
    else:
        print(f" {total - passed} project(s) failed")

    # Generate HTML report and open it in the browser
    reporter = ReportGenerator(output_dir)
    report_html = reporter.generate_report_html(results, passed, total)
    report_file = reporter.save_report_file(report_html)
    if not args.skip_ui:
        webbrowser.open_new_tab(report_file)


class ReportGenerator:
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Pychronicle Run Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #fdfdfd; color: #333; }
            h1 { color: #444; }
            table { width: 100%; border-collapse: collapse; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            th, td { border: 1px solid #ccc; padding: 12px; text-align: left; vertical-align: top; }
            th { background: #f4f4f4; font-weight: bold; }
            pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; font-family: Consolas, monospace; }
            .status-cell.success { color: #28a745; font-weight: bold; }
            .status-cell.fail { color: #dc3545; font-weight: bold; }
            .summary { font-size: 1.2em; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>Pychronicle Run Report</h1>
        <p class="summary"><strong>Summary:</strong> {{ summary }}</p>
        <table>
            <thead>
                <tr><th>Project</th><th>Status</th><th>Stdout</th><th>Stderr</th><th>Full Log</th></tr>
            </thead>
            <tbody>
                {% for row in rows %}
                <tr>
                    <td>{{ row.name }}</td>
                    <td class="status-cell {{ 'success' if row.status == 'SUCCESS' else 'fail' }}">{{ row.status }}</td>
                    <td><pre>{{ row.stdout }}</pre></td>
                    <td><pre>{{ row.stderr }}</pre></td>
                    <td><a href="{{ row.log_uri }}" target="_blank">Full log</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def generate_report_html(self, results: dict, passed: int, total: int) -> str:
        """Generates the HTML content for the report."""
        report_rows = []
        for week_name, (stdout_str, stderr_str, returncode) in results.items():
            # Write the full, untruncated log file for this project run.
            log_path = self.output_dir / f"pychronicle_{week_name}_full_output.txt"
            full_log_content = f"Stdout:\n{stdout_str}\n\nStderr:\n{stderr_str}"
            log_path.write_text(full_log_content, encoding="utf-8")

            # Truncate for display in the HTML report
            stdout_display = truncate_text(stdout_str, max_lines=10, max_chars=500)
            stderr_display = truncate_text(stderr_str, max_lines=10, max_chars=500)
            
            report_rows.append({
                "name": week_name,
                "status": "SUCCESS" if returncode == 0 else "FAIL",
                "stdout": stdout_display,
                "stderr": stderr_display,
                "log_uri": (self.output_dir / f"pychronicle_{week_name}_full_output.txt").as_uri()
            })

        template = jinja2.Template(self.HTML_TEMPLATE)
        return template.render(
            summary=f"{passed}/{total} successful",
            rows=report_rows
        )

    def save_report_file(self, html_content: str) -> str:
        """Saves the HTML content to a file and returns its URI."""
        report_file = self.output_dir / "pychronicle_run_report.html"
        report_file.write_text(html_content, encoding="utf-8")
        return report_file.as_uri()


if __name__ == "__main__":
    main()
