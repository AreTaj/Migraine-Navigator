import tkinter as tk
from tkinter import ttk
import pandas as pd
from services.entry_service import EntryService

class ViewFrame(tk.Frame):
    def __init__(self, parent, data_file_path):
        super().__init__(parent)
        self.data_file_path = data_file_path # Store data_file_path as an instance variable        
        self.filename = self.data_file_path # Use instance variable    

        # Create a label for the title
        self.title_label = tk.Label(self, text="View Migraine Entries")
        self.title_label.pack()

        # Create a Treeview widget
        self.entries_treeview = ttk.Treeview(self, columns=("Date", "Time", "Pain Level", "Medication", "Dosage", "Sleep", "Physical Activity", "Triggers", "Notes", "Location"))#, "Timezone"))

        # Create columns
        self.entries_treeview.column("#0", width=30)
        self.entries_treeview.column("Date", width=90)
        self.entries_treeview.column("Time", width=60)
        self.entries_treeview.column("Pain Level", width=80)
        self.entries_treeview.column("Medication", width=100)
        self.entries_treeview.column("Dosage", width=80)
        self.entries_treeview.column("Sleep", width=80)
        self.entries_treeview.column("Physical Activity", width=120)        
        self.entries_treeview.column("Triggers", width=200)
        self.entries_treeview.column("Notes", width=300)
        self.entries_treeview.column("Location", width=150) 
        #self.entries_treeview.column("Timezone", width=120) 

        # Create headings
        self.entries_treeview.heading("#0", text="Entry")
        self.entries_treeview.heading("Date", text="Date")
        self.entries_treeview.heading("Time", text="Time")
        self.entries_treeview.heading("Pain Level", text="Pain Level")
        self.entries_treeview.heading("Medication", text="Medication")
        self.entries_treeview.heading("Dosage", text="Dosage")
        self.entries_treeview.heading("Sleep", text="Sleep")
        self.entries_treeview.heading("Physical Activity", text="Physical Activity")          
        self.entries_treeview.heading("Triggers", text="Triggers")
        self.entries_treeview.heading("Notes", text="Notes")
        #self.entries_treeview.heading("Timezone", text="Timezone")
        self.entries_treeview.heading("Location", text="Location")

        self.entries_treeview.pack(fill="both", expand=True)

        # Load entries from CSV on initialization
        self.load_entries()

    def load_entries(self):
        try:
            # Replaced direct SQL logic with Service call
            # Now using the dynamic path passed from main.py
            data = EntryService.get_entries_from_db(self.data_file_path)
    
            data = data.fillna("")
            
            # Sort the DataFrame by 'Date' and 'Time' in descending order
            data = data.sort_values(by=['Date', 'Time'], ascending=False)

            # Ensure numeric columns are actually numeric (handle string '0', '1', etc.)
            data['Sleep'] = pd.to_numeric(data['Sleep'], errors='coerce')
            data['Physical Activity'] = pd.to_numeric(data['Physical Activity'], errors='coerce')

            # Map sleep values to descriptive labels
            sleep_mapping = {0: "Poor", 1: "Fair", 2: "Good"}
            data['Sleep'] = data['Sleep'].map(sleep_mapping) 

            # Map physical activity values to descriptive labels
            physical_activity_mapping = {0: "Low", 1: "Moderate", 2: "Heavy"}
            data['Physical Activity'] = data['Physical Activity'].map(physical_activity_mapping) 

            # Clear the Treeview
            self.entries_treeview.delete(*self.entries_treeview.get_children())

            # Insert each row into the Treeview
            for index, row in data.iterrows():
                self.entries_treeview.insert("", tk.END, values=row.to_list())
                #self.entries_treeview.insert("", tk.END, values=(row["Date"], row["Time"], row["Pain Level"], row["Medication"], row["Dosage"], row["Triggers"], row["Notes"], row["Location"], row["Timezone"]))

        except FileNotFoundError:
            # Handle case where CSV file doesn't exist
            self.entries_treeview.insert("", tk.END, values=("No entries found."))

    def update_entries(self):
        # Clear the Treeview and reload entries
        self.entries_treeview.delete(*self.entries_treeview.get_children())
        self.load_entries()