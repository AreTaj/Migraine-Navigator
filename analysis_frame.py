import tkinter as tk
# from tkinter import (
#     Frame, Label, Entry, Button, Scale, StringVar, Text, Radiobutton,  NORMAL, DISABLED, W, EW, END, HORIZONTAL
# )
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
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

    def plot_migraines_per_month(self, ax, data, year):
        width = 0.5

        monthly_counts = data[data['Date'].dt.year == year].groupby(data['Date'].dt.to_period('M')).size()
        if not monthly_counts.empty:
            monthly_counts.index = monthly_counts.index.strftime('%B')
            ax.bar(monthly_counts.index, monthly_counts.values, width=width, align='center')
            ax.set_ylabel("Count")
            ax.set_title(f"Migraines per Month for Year {year}")
            ax.tick_params(axis='x', rotation=30)
            for label in ax.get_xticklabels():
                label.set_ha('right')
            for i, v in enumerate(monthly_counts.values):
                ax.text(i, v, str(v), ha='center', va='bottom')
            # ax.set_xlim([monthly_counts.index[0], monthly_counts.index[-1]])
        else:
            ax.text(0.5, 0.5, "No data for current year", ha='center', va='center', transform=ax.transAxes)
        
    def plot_migraines_per_year(self, ax, data):
        width = 0.5

        if not data.empty:
            ax.bar(data.index, data.values, width=width)
            ax.set_ylabel("Count")
            ax.set_title("Migraines per Year")
            min_year = data.index.min()
            max_year = data.index.max()
            if min_year != max_year:
                ax.set_xlim([min_year - 0.5, max_year + 0.5])
            else:
                ax.set_xlim([min_year - 0.25, min_year + 0.25])
            ax.set_xticks(range(min_year, max_year + 1))
            for i, v in enumerate(data.values):
                ax.text(i, v, str(v), ha='center', va='bottom')
        else:
            ax.text(0.5, 0.5, "No yearly data available", ha='center', va='center', transform=ax.transAxes)

    def plot_medication_usage(self, ax, data):
        if not data.empty:
            ax.bar(data.index, data.values)
            ax.set_ylabel("Count")
            ax.set_title("Medication Usage")
            ax.set_xticks(data.index)
            ax.set_xticklabels(data.index, rotation=30)
            for i, v in enumerate(data.values):
                ax.text(i, v, str(v), ha='center', va='bottom')
        else:
            ax.axis('off')  # Hide the axes if no data
            ax.text(0.5, 0.5, "No medication data available", ha='center', va='center', transform=ax.transAxes)

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

        fig = plt.figure(figsize=(8, 12))  # Create the figure with desired size
        gs = gridspec.GridSpec(3, 1, height_ratios=[2, 2, 1],hspace=1)  # Create a 3-row, 1-column gridspec

        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        ax3 = plt.subplot(gs[2])

        try:
            self.data['Pain Level'] = pd.to_numeric(self.data['Pain Level'], errors='coerce')
        except:
            pass
        migraines_with_pain = self.data[self.data['Pain Level'] > 0]

        current_year = datetime.now().year
        yearly_counts = migraines_with_pain.groupby(migraines_with_pain['Date'].dt.year).size()
        medication_counts = self.data['Medication'].value_counts()

        self.plot_migraines_per_month(ax1, migraines_with_pain, current_year)
        self.plot_migraines_per_year(ax2, yearly_counts)
        self.plot_medication_usage(ax3, medication_counts)

        fig.subplots_adjust(left=0.1, bottom=0.15, right=0.9, top=0.9)  # Adjust spacing manually

        if self.analysis_result:
            self.analysis_result.get_tk_widget().destroy()

        self.analysis_result = FigureCanvasTkAgg(fig, self.canvas_frame)
        self.analysis_result.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.analysis_content.config(text="Monthly and yearly migraine counts displayed.")

if __name__ == "__main__":
    root = tk.Tk()
    AnalysisFrame(root).pack(fill=tk.BOTH, expand=True) # Make the frame expandable
    root.mainloop()