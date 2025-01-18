import tkinter as tk
from tkinter import ttk
from input.input_frame import InputFrame
from view.view_frame import ViewFrame
from analysis.analysis_frame import AnalysisFrame
from prediction.prediction_frame import PredictionFrame
from weather import fetch_weather_data

# Create the main window
window = tk.Tk()
window.title("Migraine Log")

# Create a Notebook widget for different screens
notebook = ttk.Notebook(window)
notebook.pack(fill="both", expand=True)

# Create instances of the screen classes
input_frame_instance = InputFrame(notebook)
view_frame_instance = ViewFrame(notebook)
analysis_frame_instance = AnalysisFrame(notebook)
prediction_frame_instance = PredictionFrame(notebook)

# Add frames (instances) to the notebook
notebook.add(input_frame_instance, text="Input")
notebook.add(view_frame_instance, text="View Entries")
notebook.add(analysis_frame_instance, text="Analysis")
notebook.add(prediction_frame_instance, text="Prediction")

# Connect the save_entry function to the save button
input_frame_instance.save_button.config(command=lambda: input_frame_instance.save_entry(view_frame_instance))

# Fetch and save weather data
fetch_weather_data()

window.mainloop()



""" import os
import csv

APPNAME = "MigraineTracker"  # Use your application's name

def get_data_file_path():
    #Returns the path to the migraine log CSV file.
    data_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APPNAME)
    os.makedirs(data_dir, exist_ok=True)  # Create directory if it doesn't exist
    return os.path.join(data_dir, "migraine_log.csv")

def create_csv_if_not_exists(filepath):
    #Creates the CSV file with headers if it doesn't exist.
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Date", "Time", "Duration", "Severity", "Symptoms", "Triggers", "Medications", "Notes"])  # Example headers

# Example usage:
file_path = get_data_file_path()
create_csv_if_not_exists(file_path)

# Now use 'file_path' for all your CSV operations
# Example to write data:
with open(file_path, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["2024-07-27", "10:00", "2", "7", "Nausea, Visual Aura", "Stress", "Ibuprofen", "Felt better after resting."])

# Example to read data:
with open(file_path, 'r', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        print(row) 
"""