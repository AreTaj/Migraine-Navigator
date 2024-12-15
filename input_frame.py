import tkinter as tk
from tkinter import ttk
import pandas as pd
import datetime
import os

class InputFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create input fields
        self.date_label = tk.Label(self, text="Date:")
        self.date_entry = tk.Entry(self)

        self.time_label = tk.Label(self, text="Time:")
        self.time_entry = tk.Entry(self)

        self.fill_button = tk.Button(self, text="Fill Time/Date", command=self.fill_time_and_date)

        self.pain_level_label = tk.Label(self, text="Pain Level (1-10):")
        self.pain_level_scale = tk.Scale(self, from_=1, to=10, orient=tk.HORIZONTAL)

        self.medication_label = tk.Label(self, text="Medication:")
        self.medication_entry = tk.Entry(self)
        self.dosage_label = tk.Label(self, text="Dosage:")
        self.dosage_entry = tk.Entry(self)

        self.triggers_label = tk.Label(self, text="Triggers:")
        self.triggers_entry = tk.Text(self, height=5, width=30)

        self.notes_label = tk.Label(self, text="Notes:")
        self.notes_entry = tk.Text(self, height=5, width=30)

        self.save_button = tk.Button(self, text="Save Entry", command=self.save_entry)

        # Pack the widgets
        self.pack_widgets()

    def pack_widgets(self):
        self.date_label.pack()
        self.date_entry.pack()
        self.time_label.pack()
        self.time_entry.pack()
        self.fill_button.pack()
        self.pain_level_label.pack()
        self.pain_level_scale.pack()
        self.medication_label.pack()
        self.medication_entry.pack()
        self.dosage_label.pack()
        self.dosage_entry.pack()
        self.triggers_label.pack()
        self.triggers_entry.pack()
        self.notes_label.pack()
        self.notes_entry.pack()
        self.save_button.pack()

    def save_entry(self,view_frame):
        date = self.date_entry.get()
        time = self.time_entry.get()
        pain_level = self.pain_level_scale.get()
        medication = self.medication_entry.get()
        dosage = self.dosage_entry.get()
        triggers = self.triggers_entry.get("1.0", "end-1c")
        notes = self.notes_entry.get("1.0", "end-1c")

        data = {'Date': date, 'Time': time, 'Pain Level': pain_level, 'Medication': medication, 'Dosage': dosage, 'Triggers': triggers, 'Notes': notes}
        df = pd.DataFrame([data])
        df.to_csv('migraine_log.csv', mode='a', header=False, index=False)

        # After saving, update the view frame
        view_frame.update_entries()

        # Clear the form
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.pain_level_scale.set(1)
        self.medication_entry.delete(0, tk.END)
        self.dosage_entry.delete(0, tk.END)
        self.triggers_entry.delete("1.0", "end-1c")
        self.notes_entry.delete("1.0", "end-1c")

    def fill_time_and_date(self):
        now = datetime.datetime.now()
        self.date_entry.insert(0, now.strftime("%Y-%m-%d"))
        self.time_entry.insert(0, now.strftime("%H:%M"))
