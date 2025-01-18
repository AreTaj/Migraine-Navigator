import tkinter as tk
from tkinter import ttk
import os
from input import InputFrame
from view import ViewFrame
from analysis import AnalysisFrame
from prediction import PredictionFrame
from weather import fetch_weather_data

# Data file management functions
def get_data_file_path(filename):
    data_dir = "data"  # Assuming 'data' directory is on the same level as main.py 
    os.makedirs(data_dir, exist_ok=True)  # Create directory if it doesn't exist
    return os.path.join(data_dir, filename)
                        
# Create the main window
window = tk.Tk()
window.title("Migraine Log")

# Define specific data file paths using relative paths
migraine_log_path = get_data_file_path("migraine_log.csv")      # Path for migraine data
weather_data_path = get_data_file_path("weather_data.csv")      # Path for weather data
combined_data_path = get_data_file_path("combined_data.csv")    # Path for combined data
# (Add paths for other data files as needed)

# Create a Notebook widget for different screens
notebook = ttk.Notebook(window)
notebook.pack(fill="both", expand=True)

# Create instances of the screen classes
input_frame_instance = InputFrame(notebook, migraine_log_path)
view_frame_instance = ViewFrame(notebook, migraine_log_path)
analysis_frame_instance = AnalysisFrame(notebook, migraine_log_path)
prediction_frame_instance = PredictionFrame(notebook, combined_data_path)

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