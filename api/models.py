from pydantic import BaseModel
from typing import Optional, Union

class MigraineEntry(BaseModel):
    id: Optional[int] = None
    Date: str
    Time: str
    Pain_Level: int  # Mapped from 'Pain Level'
    Medication: Optional[str] = ""
    Dosage: Optional[str] = ""
    Sleep: Union[str, int] # Can be "Good"/"Fair"/"Poor" or 0/1/2
    Physical_Activity: Union[str, int] # Can be "Low"/"Moderate"/"Heavy" or 0/1/2
    Triggers: Optional[str] = ""
    Notes: Optional[str] = ""
    Location: Optional[str] = ""
    Latitude: Optional[float] = None
    Longitude: Optional[float] = None
    Timezone: Optional[str] = ""
