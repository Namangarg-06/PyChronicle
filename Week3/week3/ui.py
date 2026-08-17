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
    
    def __init__(self, db_path: Path, demo_mode: bool = False, auto_mode: bool = False) -> None:
        """Initialize the timeline UI with database path.
        
        Args:
            db_path: Path to the SQLite database containing execution records.
            demo_mode: If True, auto-display all steps without waiting for input.
            auto_mode: If True, auto-display all steps in compact mode (no ANSI codes, no nav menu).
        """
        self.db_path = db_path
        self.records = fetch_execution_records(db_path)
        self.timeline_snapshots = self._build_timeline_snapshots()
        self.current_step = 0
        self.demo_mode = demo_mode
        self.auto_mode = auto_mode
        
    def _build_timeline_snapshots(self) -> List[Dict[str, Any]]:
        """Build timeline snapshots from execution records with delta information.
        
        Returns:
            List of snapshots, each containing record info, deltas, and timestamps.
        """
        snapshots: List[Dict[str, Any]] = []
        previous_state: Dict[str, Any] = {}
        
        for record in self.records:
            locals_json = record.get("locals_json", "{}")
            payload = json.loads(locals_json)
            
            # Reconstruct state by replaying deltas
            current_state = dict(previous_state)
            deltas_found = {}
            if isinstance(payload, dict) and payload.get("__pychronicle_payload__") == "delta":
                deltas_found = payload.get("changes", {})
                for key, value in deltas_found.items():
                    current_state[key] = value
            else:
                # Handle full state snapshot if not a delta
                current_state = payload
                deltas_found = {k: v for k, v in current_state.items() if previous_state.get(k) != v}
            
            snapshot = {
                "record": record,
                "deltas": deltas_found,
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
            for var_name, new_value in deltas.items():
                print(f"  {var_name} -> {self._format_value(new_value)}")
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
        
        If auto_mode is True, automatically displays all steps in compact mode.
        If demo_mode is True, automatically displays all steps in sequence.
        """
        if not self.timeline_snapshots:
            print("No execution records found in database.")
            return
        
        if self.auto_mode:
            # Auto mode: compact auto-display for pipeline execution
            self._run_auto()
        elif self.demo_mode:
            # Demo mode: full auto-display all steps
            self._run_demo()
        else:
            # Interactive mode: user navigates with commands
            self._run_interactive()
    
    def _display_step_auto(self, step_index: int) -> None:
        """Display a specific step in compact auto mode (no ANSI codes, no nav menu).
        
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
        
        # Compact display - no ANSI codes, no navigation menu
        total_steps = len(self.timeline_snapshots)
        print(f"--- Step {step_index + 1}/{total_steps} ---")
        print(f"Line: {record.get('line_number')} | Function: {record.get('function_name')}")
        print(f"Timestamp: {record.get('timestamp')}")
        
        if deltas:
            print("Variable Changes:")
            for var_name, new_value in deltas.items():
                print(f"  {var_name} -> {self._format_value(new_value)}")
        else:
            print("No variable changes in this step.")
        print()
    
    def _run_auto(self) -> None:
        """Auto-display all timeline steps in compact mode for pipeline execution.
        
        No ANSI escape codes, no navigation menu, no input() calls.
        Completes immediately without waiting for user input.
        """
        for i, _ in enumerate(self.timeline_snapshots):
            self._display_step_auto(i)
    
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
