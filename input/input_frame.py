from tkinter import (
    Frame, Label, Entry, Button, Scale, StringVar, Text, Radiobutton,  NORMAL, DISABLED, W, EW, END, HORIZONTAL, messagebox
)
from datetime import datetime
import re
import os
import csv
import geocoder

def get_location_from_ip():
    """ Gets approximate user location from the user IP address."""
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng, g.address
    else:
        print(f"Geocoding Error: {g.status_code}, {g.reason}")
        return None, None
    
def get_local_timezone():
    """Gets the system's local timezone."""
    try:
        # Preferred method (Python 3.9+): use zoneinfo
        import zoneinfo
        return zoneinfo.ZoneInfo(datetime.now().astimezone().tzinfo.key)
    except (ImportError, AttributeError):
        try:
            # Fallback for older Python versions or systems without zoneinfo
            import tzlocal
            return tzlocal.get_localzone()
        except ImportError:
            # Last resort: return None if tzlocal is not available
            print("Warning: tzlocal library not found.")
            return None

class InputFrame(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create input fields
        self.date_label = Label(self, text="Date:")
        self.date_entry = Entry(self)

        self.time_label = Label(self, text="Time:")
        self.time_entry = Entry(self)

        self.fill_button = Button(self, text="Fill Time/Date", command=self.fill_time_and_date)

        self.pain_level_label = Label(self, text="Pain Level (0-10):")
        self.pain_level_scale = Scale(self, from_=0, to=10, orient=HORIZONTAL)

        self.medication_label = Label(self, text="Medication:")
        self.medication_entry = Entry(self)
        self.dosage_label = Label(self, text="Dosage:")
        self.dosage_entry = Entry(self)

        # Sleep quality
        self.sleep_label = Label(self, text="Sleep Quality:")
        self.sleep_var = StringVar()
        self.sleep_var.set("fair")  # Default to 'fair'
        self.sleep_radio_frame = Frame(self)  # Create a frame for the radio buttons
        self.sleep_radio_poor = Radiobutton(self.sleep_radio_frame, text="Poor", variable=self.sleep_var, value="poor")
        self.sleep_radio_fair = Radiobutton(self.sleep_radio_frame, text="Fair", variable=self.sleep_var, value="fair")
        self.sleep_radio_good = Radiobutton(self.sleep_radio_frame, text="Good", variable=self.sleep_var, value="good")

        # Physical activity
        self.physical_activity_label = Label(self, text="Physical Activity:")
        self.physical_activity_var = StringVar()
        self.physical_activity_var.set("moderate")  # Default to 'moderate'
        self.physical_activity_frame = Frame(self)  # Create a frame
        self.physical_activity_radio_low = Radiobutton(self.physical_activity_frame, text="Low", variable=self.physical_activity_var, value="low")
        self.physical_activity_radio_moderate = Radiobutton(self.physical_activity_frame, text="Moderate", variable=self.physical_activity_var, value="moderate")
        self.physical_activity_radio_heavy = Radiobutton(self.physical_activity_frame, text="Heavy", variable=self.physical_activity_var, value="heavy")

        self.triggers_label = Label(self, text="Triggers:")
        self.triggers_entry = Text(self, height=5, width=30)

        self.notes_label = Label(self, text="Notes:")
        self.notes_entry = Text(self, height=5, width=30)

        # Location
        self.location_label = Label(self, text="Location:")
        self.location_var = StringVar()
        self.location_var.set("automatic")  # Default to automatic
        self.location_var.trace_add("write", self.toggle_location_entry) # Add trace

        self.location_radio_frame = Frame(self)  # Create a frame for the radio buttons
        self.location_automatic_radio = Radiobutton(self.location_radio_frame, text="Automatic", variable=self.location_var, value="automatic")
        self.location_manual_radio = Radiobutton(self.location_radio_frame, text="Manual", variable=self.location_var, value="manual")

        self.location_entry = Entry(self, state=DISABLED)  # Initially disabled

        self.save_button = Button(self, text="Save Entry", command=self.save_entry)

        # Grid the widgets
        self.grid_widgets()

    def grid_widgets(self):
        row = 0
        pady = 2
        sticky_w = W
        sticky_ew = EW

        self.date_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.date_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.time_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.time_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.fill_button.grid(row=row, column=0, columnspan=2, pady=(pady, 10))
        row += 1

        self.pain_level_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.pain_level_scale.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.medication_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.medication_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.dosage_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.dosage_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        # Sleep
        self.sleep_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.sleep_radio_frame.grid(row=row, column=1, columnspan=3, sticky=sticky_ew, pady=pady) # Occupy 3 columns
        self.sleep_radio_poor.grid(row=row, column=1, sticky=sticky_w, pady=pady)
        self.sleep_radio_fair.grid(row=row, column=2, sticky=sticky_w, pady=pady)
        self.sleep_radio_good.grid(row=row, column=3, sticky=sticky_w, pady=pady)
    
        row += 1

        # Physical activity
        self.physical_activity_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.physical_activity_frame.grid(row=row, column=1, columnspan=3, sticky=sticky_ew, pady=pady) # Occupy 3 columns
        self.physical_activity_radio_low.grid(row=row, column=1, sticky=sticky_w, pady=pady)
        self.physical_activity_radio_moderate.grid(row=row, column=2, sticky=sticky_w, pady=pady)
        self.physical_activity_radio_heavy.grid(row=row, column=3, sticky=sticky_w, pady=pady)
        row += 1

        self.triggers_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.triggers_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.notes_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.notes_entry.grid(row=row, column=1, sticky=sticky_ew, pady=pady)
        row += 1

        self.location_label.grid(row=row, column=0, sticky=sticky_w, pady=pady)
        self.location_radio_frame.grid(row=row, column=1, columnspan=2, sticky=sticky_ew, pady=pady) # Occupy 2 columns
        self.location_automatic_radio.grid(row=row, column=1, sticky=sticky_w, pady=pady)
        self.location_manual_radio.grid(row=row, column=2, sticky=sticky_w, pady=pady)
        row += 1
        self.location_entry.grid(row=row, column=0, columnspan=2, sticky=sticky_ew, pady=pady)
        row += 1

        self.save_button.grid(row=row, column=0, columnspan=2, pady=(10, pady))

        self.columnconfigure(1, weight=1) # Make column 1 expandable

    def toggle_location_entry(self, *args): # Toggle entry state
        if self.location_var.get() == "manual":
            self.location_entry.config(state=NORMAL)
        else:
            self.location_entry.config(state=DISABLED)
            self.location_entry.delete(0, END) # Clear field when switching to automatic

    def save_entry(self,view_frame):
        # Get location and timezone from input fields
        date = self.date_entry.get()
        time = self.time_entry.get()
        pain_level = self.pain_level_scale.get()
        medication = self.medication_entry.get()
        dosage = self.dosage_entry.get()
        sleep = self.sleep_var.get()
        physical_activity = self.physical_activity_var.get()
        triggers = self.triggers_entry.get("1.0", "end-1c")
        notes = self.notes_entry.get("1.0", "end-1c")

        # Location: Instead of .get(), get location from system
        if self.location_var.get() == "automatic":
            latlng, address = get_location_from_ip()
            location_data = {
                'Location': address if address else "Location not found",
                'Latitude': latlng[0] if latlng else None,
                'Longitude': latlng[1] if latlng else None,
            }
        else:
            location_data = {'Location': self.location_entry.get(), 'Latitude': None, 'Longitude': None}

        # Timezone: Instead of .get(), get timezone from system
        local_tz = get_local_timezone()
        if local_tz is None:
            timezone_name = "UTC"
        else:
            try:
                timezone_name = local_tz.key
            except AttributeError:
                timezone_name = str(local_tz)   

        # --- Date validation ---
        date_regex = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(date_regex, date):
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        try: # additional validation; checks if date is valid calendar date.
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date. Please enter a valid calendar date.")
            return

        # --- Time validation ---
        time_regex = r"^\d{2}:\d{2}$"
        if not re.match(time_regex, time):
            messagebox.showerror("Error", "Invalid time format. Please use HH:MM (24 hour time).")
            return
        
        try: # additional validation; checks if time is valid time.
            datetime.strptime(time, "%H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid time. Please enter a valid time.")
            return
        
        data = {
                'Date': date, 
                'Time': time, 
                'Pain Level': pain_level, 
                'Medication': medication, 
                'Dosage': dosage, 
                'Sleep': sleep,
                'Physical Activity': physical_activity,                
                'Triggers': triggers, 
                'Notes': notes, 
                **location_data,    # Use dictionary unpacking to add location data
                'Timezone': timezone_name
            }
        print(f"Data to be written: {data}")  # Print data dictionary        
        filename = 'migraine_log.csv' # store filename in variable for clarity
        try:
            with open(filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = reader.fieldnames
        except FileNotFoundError:
            fieldnames = data.keys()

        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if os.stat(filename).st_size == 0:
                writer.writeheader()
            writer.writerow(data)

        # After saving, update the view frame
        view_frame.update_entries()

        # Clear the form
        self.date_entry.delete(0, END)
        self.time_entry.delete(0, END)
        self.pain_level_scale.set(1)
        self.medication_entry.delete(0, END)
        self.dosage_entry.delete(0, END)
        self.sleep_var.set("fair")
        self.physical_activity_var.set("moderate")        
        self.triggers_entry.delete("1.0", "end-1c")
        self.notes_entry.delete("1.0", "end-1c")

    def fill_time_and_date(self):
        self.date_entry.delete(0, END)   # Clear existing date in entry field
        self.time_entry.delete(0, END)   # Clear existing time in entry field
        now = datetime.now()
        self.date_entry.insert(0, now.strftime("%Y-%m-%d"))
        self.time_entry.insert(0, now.strftime("%H:%M"))
