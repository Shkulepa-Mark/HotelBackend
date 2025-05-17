from services.auth import login_user
from services.rooms import get_user_booking_history
from supabase import create_client
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # Логинимся, чтобы получить user_id
    email = "test@example.com"
    password = "testpassword123"
    try:
        login_result = login_user(supabase, email, password)
        if not login_result:
            print("Не удалось войти. Проверьте email или пароль.")
            exit()
        user_id = login_result['id']
        print("Успешный вход. ID пользователя:", user_id)
    except Exception as e:
        print(f"Ошибка при входе: {e}")
        exit()

    # Получаем историю бронирований пользователя
    try:
        booking_history = get_user_booking_history(supabase, user_id)
        if booking_history:
            print("История бронирований пользователя:")
            for booking in booking_history:
                print(f"ID бронирования: {booking['id']}")
                print(f"Дата заезда: {booking['check_in']}")
                print(f"Дата выезда: {booking['check_out']}")
                print(f"ID комнаты: {booking['room_id']}")
                print(f"ID пользователя: {booking['user_id']}")
                print("---")
        else:
            print("У пользователя нет истории бронирований.")
    except Exception as e:
        print(f"Ошибка при получении истории бронирований: {e}")