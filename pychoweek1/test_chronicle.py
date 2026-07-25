import os
import sys
import unittest
import sqlite3

# Ensure we can import modules from the current directory (week1)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser import parse_assignments
from db import init_db, insert_variable_state, get_all_variable_states

class TestWeek1(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_pychronicle.db"
        self.test_py = "test_sample.py"
        
        # Create a test python sample script
        with open(self.test_py, "w", encoding="utf-8") as f:
            f.write("a = 10\n")
            f.write("b = 'hello'\n")
            f.write("c: float = 3.14\n")
            f.write("d = a + 5\n")
            
        # Initialize SQLite database
        init_db(self.test_db)
        
    def tearDown(self):
        # Clean up files created during testing
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.test_py):
            os.remove(self.test_py)
            
    def test_parser(self):
        assignments = parse_assignments(self.test_py)
        
        # Verify total assignments extracted (a, b, c, d)
        self.assertEqual(len(assignments), 4)
        
        # Verify first assignment: a = 10
        self.assertEqual(assignments[0]["variable_name"], "a")
        self.assertEqual(assignments[0]["value"], "10")
        self.assertEqual(assignments[0]["line_number"], 1)
        
        # Verify string assignment: b = 'hello'
        self.assertEqual(assignments[1]["variable_name"], "b")
        # In Python AST, the unparsed string could be 'hello' or "hello" depending on Python version/formatting
        self.assertIn("hello", assignments[1]["value"])
        self.assertEqual(assignments[1]["line_number"], 2)

        # Verify annotated assignment: c: float = 3.14
        self.assertEqual(assignments[2]["variable_name"], "c")
        self.assertEqual(assignments[2]["value"], "3.14")
        self.assertEqual(assignments[2]["line_number"], 3)
        
        # Verify complex assignment: d = a + 5
        self.assertEqual(assignments[3]["variable_name"], "d")
        self.assertEqual(assignments[3]["value"].replace(" ", ""), "a+5")
        self.assertEqual(assignments[3]["line_number"], 4)

    def test_db_storage(self):
        # Insert test records
        insert_variable_state(line_number=1, variable_name="a", serialized_value="10", db_path=self.test_db)
        insert_variable_state(line_number=3, variable_name="c", serialized_value="3.14", db_path=self.test_db)
        
        # Verify database contents
        records = get_all_variable_states(self.test_db)
        self.assertEqual(len(records), 2)
        
        # Verify record 1
        self.assertEqual(records[0]["line_number"], 1)
        self.assertEqual(records[0]["variable_name"], "a")
        self.assertEqual(records[0]["serialized_value"], "10")
        self.assertIsNotNone(records[0]["timestamp"])
        
        # Verify record 2
        self.assertEqual(records[1]["line_number"], 3)
        self.assertEqual(records[1]["variable_name"], "c")
        self.assertEqual(records[1]["serialized_value"], "3.14")
        self.assertIsNotNone(records[1]["timestamp"])

if __name__ == "__main__":
    unittest.main()
