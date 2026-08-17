import os
import argparse
from parser import parse_assignments
from pathlib import Path
from db import init_db, insert_variable_state, get_all_variable_states, DB_NAME

def main():
    parser = argparse.ArgumentParser(description="PyChronicle AST-Parser and SQLite Storage (Week 1)")
    parser.add_argument("file", nargs="?", default="sample.py", help="Python file to parse (defaults to sample.py)")
    parser.add_argument("--db", default=DB_NAME, help=f"SQLite database file path (defaults to {DB_NAME})")
    args = parser.parse_args()

    # Step 0: Ensure target file exists
    target_file_path = Path(args.file)
    if not target_file_path.exists():
        # Check if the file exists relative to the current script's directory
        alternative_path = Path(__file__).parent / args.file
        if alternative_path.exists():
            target_file_path = alternative_path
        else:
            print(f"Error: Target file '{args.file}' does not exist at '{target_file_path}' or '{alternative_path}'.")
            return

    # Step 1: Initialize database
    print(f"Initializing SQLite database at: {args.db}")
    init_db(args.db)

    # Step 2: Parse AST
    print(f"Parsing AST for file: {target_file_path}") # Corrected variable name
    try: # Pass the resolved Path object
        assignments = parse_assignments(str(target_file_path))
    except Exception as e:
        print(f"Error parsing file: {e}")
        return
        
    print(f"Found {len(assignments)} assignments:")
    for a in assignments:
        print(f"  Line {a['line_number']}: {a['variable_name']} = {a['value']}")

    # Step 3: Store in database
    print("\nStoring assignments in database...")
    for a in assignments:
        insert_variable_state(
            line_number=a['line_number'],
            variable_name=a['variable_name'],
            serialized_value=a['value'],
            db_path=args.db
        )

    # Step 4: Verify storage
    print("\nVerifying database records:")
    try:
        records = get_all_variable_states(args.db)
        for r in records:
            print(f"  ID: {r['id']} | Timestamp: {r['timestamp']} | Line: {r['line_number']} | Var: {r['variable_name']} | Value: {r['serialized_value']}")
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    main()
