import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from models.users import UserCreate
from supabase import Client
import bcrypt

def register_user(supabase: Client, user_data: UserCreate):
    hashed_password = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt())
    user = {
        "surname": user_data.surname,
        "name": user_data.name,
        "patronymic": user_data.patronymic,
        "email": user_data.email,
        "password_data": user_data.password_data,
        "password": hashed_password.decode()
    }
    response = supabase.table("users").insert(user).execute()
    return response.data[0] if response.data else None

def login_user(supabase: Client, email: str, password: str):
    response = supabase.table("users").select("*").eq("email", email).execute()
    if response.data and bcrypt.checkpw(password.encode(), response.data[0]["password"].encode()):
        return response.data[0]
    return None