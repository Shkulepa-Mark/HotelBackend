import asyncio
import websockets
import device_pb2
import sys
import os
import logging
from datetime import datetime
from supabase import Client
from config import supabase
from services.auth import login_user, register_user
from services.rooms import get_available_rooms, book_room, cancel_booking, get_user_active_bookings, \
    get_user_booking_history
from models.users import UserCreate
from models.booking import BookingCreate

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Множество для хранения подключенных клиентов
connected_clients = set()


async def handle_websocket(websocket, path):
    # Добавляем клиента в множество
    connected_clients.add(websocket)
    logger.info(f"New client connected: {path}")

    try:
        async for message in websocket:
            # Парсим бинарное сообщение (Protocol Buffers)
            cmd = device_pb2.DeviceCommand()
            try:
                cmd.ParseFromString(message)
            except Exception as e:
                logger.error(f"Failed to parse message: {str(e)}")
                response = device_pb2.Response()
                response.status = "error"
                response.message = "Invalid message format"
                await websocket.send(response.SerializeToString())
                continue

            action = cmd.action
            logger.info(f"Received action: {action}")
            response = device_pb2.Response()

            try:
                if action == "login":
                    user = login_user(supabase, cmd.email, cmd.password)
                    if user:
                        response.status = "success"
                        response.message = "Успешный вход"
                        response.user_id = user["id"]
                    else:
                        response.status = "error"
                        response.message = "Неверные учетные данные"

                elif action == "register":
                    if cmd.password != cmd.confirm_password:
                        response.status = "error"
                        response.message = "Пароли не совпадают"
                    else:
                        user_data = UserCreate(
                            surname=cmd.surname,
                            name=cmd.name,
                            patronymic=cmd.patronymic,
                            email=cmd.email,
                            password_data=cmd.password_data,
                            password=cmd.password,
                            confirm_password=cmd.confirm_password
                        )
                        user = register_user(supabase, user_data)
                        if user:
                            response.status = "success"
                            response.message = "Пользователь зарегистрирован"
                            response.user_id = user["id"]
                        else:
                            response.status = "error"
                            response.message = "Ошибка регистрации"

                elif action == "get_available_rooms":
                    rooms = get_available_rooms(supabase)
                    response.status = "success"
                    for room in rooms:
                        room_data = response.rooms.add()
                        room_data.id = room.id
                        room_data.ble_device_id = room.ble_device_id
                        room_data.is_available = room.is_available
                        room_data.name = room.name
                        room_data.created_at = room.created_at.isoformat()

                elif action == "book_room":
                    try:
                        check_in = datetime.fromisoformat(cmd.booking.check_in)
                        check_out = datetime.fromisoformat(cmd.booking.check_out)
                    except ValueError:
                        response.status = "error"
                        response.message = "Неверный формат даты"
                        await websocket.send(response.SerializeToString())
                        continue

                    if check_in >= check_out:
                        response.status = "error"
                        response.message = "Дата въезда должна быть раньше выезда"
                    elif cmd.user_id == 0:
                        response.status = "error"
                        response.message = "Требуется авторизация"
                    else:
                        booking_data = BookingCreate(
                            check_in=check_in,
                            check_out=check_out,
                            room_id=cmd.booking.room_id,
                            user_id=cmd.user_id
                        )
                        success = book_room(supabase, booking_data, cmd.user_id)
                        response.status = "success" if success else "error"
                        response.message = "Комната забронирована" if success else "Ошибка бронирования"
                        if success:
                            # Уведомляем всех клиентов об обновлении
                            notify = device_pb2.Response()
                            notify.status = "success"
                            notify.message = "Room status updated"
                            for client in connected_clients:
                                if client != websocket and client.open:
                                    try:
                                        await client.send(notify.SerializeToString())
                                    except Exception:
                                        pass

                elif action == "cancel_booking":
                    if cmd.user_id == 0:
                        response.status = "error"
                        response.message = "Требуется авторизация"
                    else:
                        success = cancel_booking(supabase, cmd.booking_id, cmd.user_id)
                        response.status = "success" if success else "error"
                        response.message = "Бронирование отменено" if success else "Ошибка отмены"
                        if success:
                            # Уведомляем всех клиентов
                            notify = device_pb2.Response()
                            notify.status = "success"
                            notify.message = "Room status updated"
                            for client in connected_clients:
                                if client != websocket and client.open:
                                    try:
                                        await client.send(notify.SerializeToString())
                                    except Exception:
                                        pass

                elif action == "get_active_bookings":
                    if cmd.user_id == 0:
                        response.status = "error"
                        response.message = "Требуется авторизация"
                    else:
                        bookings = get_user_active_bookings(supabase, cmd.user_id)
                        response.status = "success"
                        for booking in bookings:
                            booking_data = response.bookings.add()
                            booking_data.check_in = booking["check_in"]
                            booking_data.check_out = booking["check_out"]
                            booking_data.room_id = booking["room_id"]
                            booking_data.user_id = booking["user_id"]

                elif action == "get_booking_history":
                    if cmd.user_id == 0:
                        response.status = "error"
                        response.message = "Требуется авторизация"
                    else:
                        history = get_user_booking_history(supabase, cmd.user_id)
                        response.status = "success"
                        for booking in history:
                            booking_data = response.bookings.add()
                            booking_data.check_in = booking["check_in"]
                            booking_data.check_out = booking["check_out"]
                            booking_data.room_id = booking["room_id"]
                            booking_data.user_id = booking["user_id"]

                else:
                    response.status = "error"
                    response.message = "Неизвестное действие"

            except Exception as e:
                logger.error(f"Error processing action {action}: {str(e)}")
                response.status = "error"
                response.message = f"Ошибка сервера: {str(e)}"

            # Отправляем ответ
            try:
                await websocket.send(response.SerializeToString())
            except Exception as e:
                logger.error(f"Failed to send response: {str(e)}")

    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        # Удаляем клиента из множества
        connected_clients.discard(websocket)


async def main():
    port = int(os.environ.get("PORT", 8765))  # Render назначает порт через PORT
    host = "0.0.0.0"  # Доступен извне
    async with websockets.serve(handle_websocket, host, port):
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        await asyncio.Future()  # Бесконечное ожидание


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")