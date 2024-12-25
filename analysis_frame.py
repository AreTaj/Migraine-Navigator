""" 
Ideas:

- bar charts for migraines per month, year
- medication usage

"""

import tkinter as tk
# from tkinter import (
#     Frame, Label, Entry, Button, Scale, StringVar, Text, Radiobutton,  NORMAL, DISABLED, W, EW, END, HORIZONTAL
# )
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalysisFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Label for title
        self.title_label = tk.Label(self, text="Analysis")
        self.title_label.pack(pady=10)

        # Placeholder for analysis content
        self.analysis_content = tk.Label(self, text="Select data and analysis type")
        self.analysis_content.pack()

        # Button to trigger analysis (initially disabled)
        self.analyze_button = tk.Button(self, text="Analyze", state=tk.DISABLED, command=self.perform_analysis)
        self.analyze_button.pack(pady=10)

        # Placeholder for displaying analysis results (could be a figure or text)
        self.analysis_result = None

    def perform_analysis(self):
        # This function will be filled later with specific analysis logic
        # Based on user selection (dropdown, radio buttons etc.)
        # it will process data and generate results

        # Example: Generate a sample plot
        x = [1, 2, 3, 4, 5]
        y = [2, 5, 7, 1, 3]
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set(xlabel='X', ylabel='Y', title='Sample Plot')

        # Create a canvas to display the plot within the frame
        self.analysis_result = FigureCanvasTkAgg(fig, self)
        self.analysis_result.get_tk_widget().pack()

        # (Optional) Update the analysis content label with summary text
        self.analysis_content.config(text="Sample plot generated. More analysis options coming soon!")

# This allows for data exchange between frames (details later)
    def update_data(self, data):
        # This function will be called from other frames (e.g., ViewFrame)
        # to provide the analysis frame with data for processing
        self.data = data
        self.analyze_button.config(state=tk.NORMAL)  # Enable analysis button if data is received

if __name__ == "__main__":
    root = tk.Tk()
    AnalysisFrame(root).pack()
    root.mainloop()