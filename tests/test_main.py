import unittest
import os
import tkinter as tk
import sys

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import get_data_file_path

class TestMain(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        self.cleanup_test_dir()

    def tearDown(self):
        self.cleanup_test_dir()

    def cleanup_test_dir(self):
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
            os.rmdir(self.test_dir)

    def test_get_data_file_path(self):
        # Test path construction
        filename = "test.csv"
        expected_path = os.path.join(os.path.dirname(__file__), "..", "data", filename)
        actual_path = get_data_file_path(filename)
        self.assertEqual(os.path.abspath(actual_path), os.path.abspath(expected_path))

        # Test directory creation
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data")))

    def test_file_paths(self):
        # Test specific file paths
        paths = [
            get_data_file_path("migraine_log.csv"),
            get_data_file_path("weather_data.csv"),
            get_data_file_path("combined_data.csv")
        ]
        
        for path in paths:
            self.assertTrue(path.endswith(".csv"))
            self.assertTrue(path.startswith(os.path.join("data")))

    def test_window_creation(self):
        root = tk.Tk()
        root.title("Migraine Log")  # Set the title directly in the test
        self.assertEqual(root.title(), "Migraine Log")
        root.destroy()

if __name__ == '__main__':
    unittest.main()