from pydantic import BaseModel
from typing import Optional, Union, List

class Medication(BaseModel):
    id: Optional[int] = None
    name: str
    display_name: Optional[str] = ""
    default_dosage: Optional[str] = ""
    frequency: Optional[str] = "as_needed" # as_needed, daily, periodic
    period_days: Optional[int] = None      # For periodic meds

class SelectedMedication(BaseModel):
    name: str
    dosage: str

class MigraineEntry(BaseModel):
    id: Optional[int] = None
    Date: str
    Time: str
    Pain_Level: int  # Mapped from 'Pain Level'
    Medication: Optional[str] = "" # Legacy
    Dosage: Optional[str] = ""     # Legacy
    Medications: Optional[List[SelectedMedication]] = [] # New structured list
    # Sleep Quality: 1 (Poor) to 3 (Good). Represents the night BEFORE the entry date.
    Sleep: Union[str, int] # Can be "Good"/"Fair"/"Poor" or 0/1/2
    Physical_Activity: Union[str, int] # Can be "Low"/"Moderate"/"Heavy" or 0/1/2
    Triggers: Optional[str] = ""
    Notes: Optional[str] = ""
    Location: Optional[str] = ""
    Latitude: Optional[float] = None
    Longitude: Optional[float] = None
    Timezone: Optional[str] = ""
