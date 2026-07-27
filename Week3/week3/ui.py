"""
PyChronicle Week 3 - Interactive Timeline Viewer

Provides a terminal-based interface to browse recorded execution states
with support for navigating through variable changes over time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from week3.db import fetch_execution_records


class TimelineUI:
    """Interactive terminal-based timeline viewer for PyChronicle Week 3."""
    
    def __init__(self, db_path: Path, demo_mode: bool = False) -> None:
        """Initialize the timeline UI with database path.
        
        Args:
            db_path: Path to the SQLite database containing execution records.
            demo_mode: If True, auto-display all steps without waiting for input.
        """
        self.db_path = db_path
        self.records = fetch_execution_records(db_path)
        self.timeline_snapshots = self._build_timeline_snapshots()
        self.current_step = 0
        self.demo_mode = demo_mode
        
    def _build_timeline_snapshots(self) -> List[Dict[str, Any]]:
        """Build timeline snapshots from execution records with delta information.
        
        Returns:
            List of snapshots, each containing record info, deltas, and timestamps.
        """
        snapshots: List[Dict[str, Any]] = []
        previous_state: Dict[str, Any] = {}
        
        for record in self.records:
            locals_json = record.get("locals_json", "{}")
            current_state = json.loads(locals_json)
            
            # Extract deltas (changes from previous state)
            deltas = {}
            if isinstance(current_state, dict) and current_state.get("__pychronicle_payload__") == "delta":
                deltas = current_state.get("changes", {})
            else:
                # Calculate delta by comparing with previous state
                for key, value in current_state.items():
                    prev_value = previous_state.get(key)
                    if prev_value != value:
                        deltas[key] = {"old": prev_value, "new": value}
                previous_state = dict(current_state)
            
            snapshot = {
                "record": record,
                "deltas": deltas,
                "timestamp": record.get("timestamp", ""),
                "line_number": record.get("line_number", 0),
            }
            snapshots.append(snapshot)
        
        return snapshots
    
    def _format_value(self, value: Any) -> str:
        """Format a value for display in the timeline.
        
        Args:
            value: The value to format.
            
        Returns:
            String representation of the value.
        """
        if isinstance(value, str):
            return f'"{value}"'
        elif value is None:
            return "None"
        else:
            return str(value)
    
    def _display_step(self, step_index: int) -> None:
        """Display a specific step in the timeline.
        
        Args:
            step_index: Index of the step to display.
        """
        if not self.timeline_snapshots:
            print("No execution records available.")
            return
        
        # Clamp step index to valid range
        step_index = max(0, min(step_index, len(self.timeline_snapshots) - 1))
        self.current_step = step_index
        
        snapshot = self.timeline_snapshots[step_index]
        record = snapshot["record"]
        deltas = snapshot["deltas"]
        
        # Clear screen (simple approach)
        print("\033[2J\033[H", end="")
        
        # Display header
        print("=" * 50)
        print("PYCHRONICLE TIMELINE - WEEK 3")
        print("=" * 50)
        print()
        
        # Display step info
        total_steps = len(self.timeline_snapshots)
        print(f"Step {step_index + 1}/{total_steps}")
        print(f"Line: {record.get('line_number')}")
        print(f"Function: {record.get('function_name')}")
        print(f"Timestamp: {record.get('timestamp')}")
        print()
        
        # Display variable changes
        if deltas:
            print("Variable Changes:")
            print("-" * 50)
            for var_name, change_info in deltas.items():
                if isinstance(change_info, dict) and "old" in change_info:
                    old_val = change_info["old"]
                    new_val = change_info["new"]
                    print(f"  {var_name}")
                    print(f"    Old: {self._format_value(old_val)}")
                    print(f"    New: {self._format_value(new_val)}")
                else:
                    # New variable
                    print(f"  {var_name}")
                    print(f"    Old: (new)")
                    print(f"    New: {self._format_value(change_info)}")
            print()
        else:
            print("No variable changes in this step.")
            print()
        
        # Display navigation menu
        print("-" * 50)
        print("[N] Next   [P] Previous   [Q] Quit")
        print("-" * 50)
    
    def run(self) -> None:
        """Run the interactive timeline viewer.
        
        Displays the first execution step and enters an interactive loop
        where users can navigate through the timeline using N/P/Q commands.
        
        If demo_mode is True, automatically displays all steps in sequence.
        """
        if not self.timeline_snapshots:
            print("No execution records found in database.")
            return
        
        if self.demo_mode:
            # Demo mode: auto-display all steps
            self._run_demo()
        else:
            # Interactive mode: user navigates with commands
            self._run_interactive()
    
    def _run_demo(self) -> None:
        """Auto-display all timeline steps in sequence (demo mode)."""
        for i, _ in enumerate(self.timeline_snapshots):
            self._display_step(i)
    
    def _run_interactive(self) -> None:
        """Run interactive mode where user navigates with N/P/Q commands."""
        self._display_step(0)
        
        while True:
            user_input = input("\nCommand: ").strip().upper()
            
            if user_input == "Q":
                print("\nExiting timeline viewer...")
                break
            elif user_input == "N":
                if self.current_step < len(self.timeline_snapshots) - 1:
                    self._display_step(self.current_step + 1)
                else:
                    print("\nAlready at the last step.")
                    self._display_step(self.current_step)
            elif user_input == "P":
                if self.current_step > 0:
                    self._display_step(self.current_step - 1)
                else:
                    print("\nAlready at the first step.")
                    self._display_step(self.current_step)
            else:
                print("\nInvalid command. Use [N] Next, [P] Previous, or [Q] Quit.")
                self._display_step(self.current_step)
