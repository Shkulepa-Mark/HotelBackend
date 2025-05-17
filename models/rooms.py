from pydantic import BaseModel, constr
from typing import Optional
from datetime import datetime

class RoomBase(BaseModel):
    ble_device_id: constr(min_length=1)
    is_available: bool = True
    name: constr(min_length=1, max_length=100)

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True