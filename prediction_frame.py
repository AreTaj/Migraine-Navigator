import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re
import joblib
import pandas as pd
import geocoder

class PredictionFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Load the trained model
        self.model = joblib.load('rf_model.pkl')

        # Create input fields
        self.date_label = tk.Label(self, text="Date:")
        self.date_entry = tk.Entry(self)

        self.time_label = tk.Label(self, text="Time:")
        self.time_entry = tk.Entry(self)

        self.fill_button = tk.Button(self, text="Fill Time/Date", command=self.fill_time_and_date)

        self.location_label = tk.Label(self, text="Location:")
        self.location_entry = tk.Entry(self)

        self.latitude_label = tk.Label(self, text="Latitude:")
        self.latitude_entry = tk.Entry(self)

        self.longitude_label = tk.Label(self, text="Longitude:")
        self.longitude_entry = tk.Entry(self)

        self.fill_location_button = tk.Button(self, text="Fill Location", command=self.fill_location)

        self.predict_button = tk.Button(self, text="Predict", command=self.predict_migraine)
        self.result_label = tk.Label(self, text="Prediction Result: ")

        # Grid the widgets
        self.grid_widgets()

    def grid_widgets(self):
        row = 0
        pady = 2
        sticky_w = tk.W
        sticky_ew = tk.EW

        self.date_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.date_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.time_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.time_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1
        
        self.fill_button.grid(row=row, column=0, columnspan=2, pady=(pady, 10))
        row += 1

        self.location_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.location_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.latitude_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.latitude_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.longitude_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.longitude_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.fill_location_button.grid(row=row, column=0, columnspan=2, pady=(pady, 10))
        row += 1

        self.predict_button.grid(row=row, column=0, columnspan=2, pady=(10, pady))
        row += 1

        self.result_label.grid(row=row, column=0, columnspan=2, pady=(10, pady))

        self.columnconfigure(1, weight=1) # Make column 1 expandable

    def fill_time_and_date(self):
        self.date_entry.delete(0, tk.END)   # Clear existing date in entry field
        self.time_entry.delete(0, tk.END)   # Clear existing time in entry field
        now = datetime.now()
        self.date_entry.insert(0, now.strftime("%Y-%m-%d"))
        self.time_entry.insert(0, now.strftime("%H:%M"))

    def fill_location(self):
        latlng, address = self.get_location_from_ip()
        if latlng:
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, address if address else "Location not found")
            self.latitude_entry.delete(0, tk.END)
            self.latitude_entry.insert(0, latlng[0])
            self.longitude_entry.delete(0, tk.END)
            self.longitude_entry.insert(0, latlng[1])
        else:
            messagebox.showerror("Error", "Unable to fetch location data.")

    def get_location_from_ip(self):
        """ Gets approximate user location from the user IP address."""
        g = geocoder.ip('me')
        if g.ok:
            return g.latlng, g.address
        else:
            print(f"Geocoding Error: {g.status_code}, {g.reason}")
            return None, None

    def predict_migraine(self):
        # Get input values
        date = self.date_entry.get()
        time = self.time_entry.get()
        location = self.location_entry.get()
        latitude = self.latitude_entry.get()
        longitude = self.longitude_entry.get()

        # Validate date
        date_regex = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(date_regex, date):
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date. Please enter a valid calendar date.")
            return

        # Validate time
        time_regex = r"^\d{2}:\d{2}$"
        if not re.match(time_regex, time):
            messagebox.showerror("Error", "Invalid time format. Please use HH:MM (24 hour time).")
            return

        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid time. Please enter a valid time.")
            return

        # Prepare data for prediction
        data = {
            'Date': date,
            'Time': time,
            'Location': location,
            'Latitude': latitude,
            'Longitude': longitude,
        }
        df = pd.DataFrame([data])

        # Make prediction
        prediction = self.model.predict(df)
        result = "Migraine" if prediction[0] == 1 else "No Migraine"

        # Display result
        self.result_label.config(text=f"Prediction Result: {result}")