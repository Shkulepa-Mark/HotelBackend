from supabase import Client
from datetime import datetime
from models.rooms import Room
from models.booking import BookingCreate

def get_available_rooms(supabase: Client):
    response = supabase.table("rooms").select("*").eq("is_available", True).execute()
    return [Room(**room) for room in response.data] if response.data else []

def book_room(supabase: Client, booking_data: BookingCreate, user_id: int):
    if booking_data.check_in >= booking_data.check_out:
        return False
    booking = {
        "check_in": booking_data.check_in.isoformat(),
        "check_out": booking_data.check_out.isoformat(),
        "room_id": booking_data.room_id,
        "user_id": user_id
    }
    response = supabase.table("bookings").insert(booking).execute()
    if response.data:
        supabase.table("rooms").update({"is_available": False}).eq("id", booking_data.room_id).execute()
        return True
    return False

def cancel_booking(supabase: Client, booking_id: int, user_id: int):
    response = supabase.table("bookings").select("room_id").eq("id", booking_id).eq("user_id", user_id).execute()
    if response.data:
        supabase.table("bookings").delete().eq("id", booking_id).execute()
        supabase.table("rooms").update({"is_available": True}).eq("id", response.data[0]["room_id"]).execute()
        return True
    return False

def get_user_active_bookings(supabase: Client, user_id: int):
    current_time = datetime.now().isoformat()
    response = supabase.table("bookings").select("*").eq("user_id", user_id).gte("check_out", current_time).execute()
    return response.data if response.data else []

def get_user_booking_history(supabase: Client, user_id: int):
    response = supabase.table("bookings").select("*").eq("user_id", user_id).execute()
    return response.data if response.data else []