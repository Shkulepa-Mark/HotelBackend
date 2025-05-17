from pydantic import BaseModel
from datetime import datetime

class BookingBase(BaseModel):
    check_in: datetime
    check_out: datetime
    room_id: int
    user_id: int

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True