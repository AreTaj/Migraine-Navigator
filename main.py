import tkinter as tk
from tkinter import ttk
import input_frame
import view_frame
import analysis_frame

# Create the main window
window = tk.Tk()
window.title("Migraine Log")

# Create a Notebook widget for different screens
notebook = ttk.Notebook(window)
notebook.pack(fill="both", expand=True)

# Create instances of the screen classes
input_frame_instance = input_frame.InputFrame(notebook)
view_frame_instance = view_frame.ViewFrame(notebook)
#analysis_frame_instance = analysis_frame.AnalysisFrame(notebook)       #temporarily disabled

# Add frames (instances) to the notebook
notebook.add(input_frame_instance, text="Input")
notebook.add(view_frame_instance, text="View Entries")
#notebook.add(analysis_frame_instance, text="Analysis")

# Connect the save_entry function to the save button
input_frame_instance.save_button.config(command=lambda: input_frame_instance.save_entry(view_frame_instance))

window.mainloop()