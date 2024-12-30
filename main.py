import tkinter as tk
from tkinter import ttk
from input_frame import InputFrame
from view_frame import ViewFrame
from analysis_frame import AnalysisFrame

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

# Add frames (instances) to the notebook
notebook.add(input_frame_instance, text="Input")
notebook.add(view_frame_instance, text="View Entries")
notebook.add(analysis_frame_instance, text="Analysis")

# Connect the save_entry function to the save button
input_frame_instance.save_button.config(command=lambda: input_frame_instance.save_entry(view_frame_instance))

window.mainloop()