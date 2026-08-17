from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class MeetingResponse(BaseModel):
    id: int
    filename: str
    status: str
    transcript: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
