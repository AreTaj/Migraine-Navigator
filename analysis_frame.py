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
import os
import pandas as pd
from datetime import datetime

class AnalysisFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.title_label = tk.Label(self, text="Migraine Analysis", font=("Arial", 16))
        self.title_label.pack(pady=(10, 0))  # Add top padding

        self.analysis_content = tk.Label(self, text="Click 'Analyze' to generate charts.", wraplength=400) # Added wraplength
        self.analysis_content.pack(pady=(0, 10))  # Add bottom padding

        self.analyze_button = tk.Button(self, text="Analyze", command=self.perform_analysis)
        self.analyze_button.pack(pady=(0, 10))

        self.canvas_frame = tk.Frame(self) # Frame to hold the canvas
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.analysis_result = None
        self.data = None

    def perform_analysis(self):
        filename = 'migraine_log.csv'
        if not os.path.exists(filename):
            self.analysis_content.config(text=f"Data file '{filename}' not found.")
            return

        try:
            self.data = pd.read_csv(filename)
            if self.data.empty:
                self.analysis_content.config(text="No data found in the CSV file.")
                return
        except pd.errors.ParserError:
            self.analysis_content.config(text=f"Error parsing '{filename}'. Check the file format.")
            return

        try:
            self.data['Date'] = pd.to_datetime(self.data['Date'], format='%Y-%m-%d')
        except (ValueError, TypeError):
            self.analysis_content.config(text="Invalid date format in data. Please use YYYY-MM-DD.")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6))
        width = 0.5 # Bar width

        # Filter out entries with pain level 0
        try:
            self.data['Pain Level'] = pd.to_numeric(self.data['Pain Level'], errors='coerce')  # Try conversion with coerce for non-numeric values
        except:
            # Handle non-numeric values (optional)
            pass
        migraines_with_pain = self.data[self.data['Pain Level'] > 0]

        # Migraines per month for current year only
        current_year = datetime.now().year
        monthly_counts = migraines_with_pain[migraines_with_pain['Date'].dt.year == current_year].groupby(migraines_with_pain['Date'].dt.to_period('M')).size()
        if not monthly_counts.empty: # Check if there is data to avoid errors
            monthly_counts.index = monthly_counts.index.strftime('%Y-%m')
            ax1.bar(monthly_counts.index, monthly_counts.values, width=width, align='center')
            ax1.set_xlabel("Month")
            ax1.set_ylabel("Number of Migraines")
            ax1.set_title(f"Migraines per Month for Year {current_year}")
            ax1.tick_params(axis='x', rotation=45)#, ha='right') # ha for horizontal alignment
            labels = ax1.get_xticklabels()
            for label in labels:
                label.set_ha('right')  # Set horizontal alignment for each label separately
            #ax1.set_xlim([monthly_counts.index[0], monthly_counts.index[-1]]) #Setting x-axis limits

        else:
            ax1.text(0.5, 0.5, "No data for current year", ha='center', va='center', transform=ax1.transAxes)

        # Migraines per year
        yearly_counts = migraines_with_pain.groupby(migraines_with_pain['Date'].dt.year).size()
        if not yearly_counts.empty: # Check if there is data to avoid errors
            ax2.bar(yearly_counts.index, yearly_counts.values, width=width)
            ax2.set_xlabel("Year")
            ax2.set_ylabel("Number of Migraines")
            ax2.set_title("Migraines per Year")
            min_year = yearly_counts.index.min() # Get min and max years from data
            max_year = yearly_counts.index.max()
            if min_year != max_year:
                ax2.set_xlim([min_year - 0.5, max_year + 0.5])  # Set x-axis limits with padding (existing code)
            else:
                # Handle case with only one year of data (e.g., set a small range around the year)
                ax2.set_xlim([min_year - 0.25, min_year + 0.25])            
            #ax2.set_xlim([yearly_counts.index[0], yearly_counts.index[-1]]) #Setting x-axis limits
            ax2.set_xticks(range(min_year, max_year + 1)) # Ensure integer ticks
        else:
            ax2.text(0.5, 0.5, "No yearly data available", ha='center', va='center', transform=ax2.transAxes)

        plt.tight_layout()

        if self.analysis_result:
            self.analysis_result.get_tk_widget().destroy()

        self.analysis_result = FigureCanvasTkAgg(fig, self.canvas_frame) # Put canvas in the frame
        self.analysis_result.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.analysis_content.config(text="Monthly and yearly migraine counts displayed.")

if __name__ == "__main__":
    root = tk.Tk()
    AnalysisFrame(root).pack(fill=tk.BOTH, expand=True) # Make the frame expandable
    root.mainloop()