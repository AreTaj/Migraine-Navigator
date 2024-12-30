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

        self.analysis_content = tk.Label(self, text="Select a graph to display:", wraplength=400)
        self.analysis_content.pack(pady=(0, 10))  # Add bottom padding

        # Create dropdown menus for graph selection
        self.graph_options = [
            "Migraine Days per Month",
            "Migraine Days per Year",
            "Medication Usage"
        ]
        self.selected_graph = tk.StringVar(self)
        self.selected_graph.set(self.graph_options[0])  # Set default selection
        self.graph_dropdown = ttk.Combobox(self, values=self.graph_options, textvariable=self.selected_graph)
        self.graph_dropdown.pack(pady=(0, 10))

        # Checkbox for displaying two graphs side-by-side
        self.show_two_graphs = tk.BooleanVar(self)
        self.show_two_graphs_check = tk.Checkbutton(
            self, text="Show Two Graphs", variable=self.show_two_graphs, command=self.update_display
        )
        self.show_two_graphs_check.pack(pady=(0, 10))

        # Second dropdown menu (enabled only when checkbox is selected)
        self.graph_options_2 = self.graph_options.copy()  # Copy options for second dropdown
        self.selected_graph_2 = tk.StringVar(self)
        self.selected_graph_2.set(self.graph_options_2[1])  # Set default selection (different from first)
        self.graph_dropdown_2 = ttk.Combobox(self, values=self.graph_options_2, textvariable=self.selected_graph_2, state="disabled")
        self.graph_dropdown_2.pack(pady=(0, 10))

        self.analyze_button = tk.Button(self, text="Analyze", command=self.perform_analysis)
        self.analyze_button.pack(pady=(0, 10))

        self.canvas_frame = tk.Frame(self)  # Frame to hold the canvas
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.analysis_result = None
        self.data = None
        
    def update_display(self):
        """
        Enable/disable the second graph dropdown menu based on the checkbox selection.
        """
        if self.show_two_graphs.get():
            self.graph_dropdown_2.config(state="normal")
        else:
            self.graph_dropdown_2.config(state="disabled")

    def plot_migraines_monthly(self, ax, data, year):
        width = 0.5

        monthly_counts = data[data['Date'].dt.year == year].groupby(data['Date'].dt.to_period('M')).size()
        if not monthly_counts.empty:
            monthly_counts.index = monthly_counts.index.strftime('%B')
            ax.bar(monthly_counts.index, monthly_counts.values, width=width, align='center')
            ax.set_ylabel("Count")
            ax.set_title(f"Migraine Days per Month for Year {year}")
            ax.tick_params(axis='x', rotation=30)
            for label in ax.get_xticklabels():
                label.set_ha('right')
            for i, v in enumerate(monthly_counts.values):
                ax.text(i, v, str(v), ha='center', va='bottom')
            # ax.set_xlim([monthly_counts.index[0], monthly_counts.index[-1]])
        else:
            ax.text(0.5, 0.5, "No data for current year", ha='center', va='center', transform=ax.transAxes)
        
    def plot_migraines_yearly(self, ax, data):
        width = 0.5

        if not data.empty:
            ax.bar(data.index, data.values, width=width)
            ax.set_ylabel("Count")
            ax.set_title("Migraine Days per Year")
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

        try:
            self.data['Pain Level'] = pd.to_numeric(self.data['Pain Level'], errors='coerce')
        except:
            pass

        migraines_with_pain = self.data[self.data['Pain Level'] > 0]    # Filter out entries with no pain level

        current_year = datetime.now().year
        yearly_counts = migraines_with_pain.groupby(migraines_with_pain['Date'].dt.year).size()
        medication_counts = self.data['Medication'].value_counts()

        graph_functions = {
            "Migraine Days per Month": (self.plot_migraines_monthly, migraines_with_pain, current_year),
            "Migraine Days per Year": (self.plot_migraines_yearly, yearly_counts),
            "Medication Usage": (self.plot_medication_usage, medication_counts),
            # Add more graphs here: "Graph Name": (self.plot_function, data, *args)
        }

        selected_graphs = [self.selected_graph.get()]
        if self.show_two_graphs.get():
            selected_graphs.append(self.selected_graph_2.get())

        num_graphs = len(selected_graphs)
        fig, axes = plt.subplots(1, num_graphs, figsize=(8 * num_graphs, 6))  # Dynamic figsize
        if num_graphs == 1:
          axes = [axes]

        for i, graph_name in enumerate(selected_graphs):
            try:
                func_data = graph_functions[graph_name]
                plot_function = func_data[0]
                data = func_data[1]
                args = func_data[2:]    # This handles cases with or without arguments
                plot_function(axes[i], data, *args)
            except KeyError:
                print(f"Error: Graph function not found for '{graph_name}'")
                return

        fig.subplots_adjust(left=0.1, bottom=0.2, right=0.95, top=0.9)

        if self.analysis_result:
            self.analysis_result.get_tk_widget().destroy()

        self.analysis_result = FigureCanvasTkAgg(fig, self.canvas_frame)
        self.analysis_result.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        #self.analysis_content.config(text="Monthly and yearly migraine counts displayed.")

if __name__ == "__main__":
    root = tk.Tk()
    AnalysisFrame(root).pack(fill=tk.BOTH, expand=True) # Make the frame expandable
    root.mainloop()