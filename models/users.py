from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    surname: constr(min_length=1, max_length=50)
    name: constr(min_length=1, max_length=50)
    patronymic: Optional[constr(max_length=50)] = None
    email: EmailStr
    password_data: Optional[str] = None
    password: constr(min_length=8)

class UserCreate(UserBase):
    confirm_password: constr(min_length=8)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True