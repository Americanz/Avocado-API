# from src.core.models.auth.users.controller import user_controller
# from src.core.models.auth.users.schemas import UserCreate


# import asyncio

# async def process_user_creation_queue():
#     """Worker для обробки черги створення користувачів"""
#     while True:
#         try:
#             conn = connections.get("default")

#             # Отримуємо необроблені записи
#             rows = await conn.execute_query("""
#                 SELECT id, email, user_name, password, nick_name
#                 FROM user_creation_queue
#                 WHERE processed_at IS NULL
#                 LIMIT 10
#             """)

#             for row in rows:
#                 try:
#                     # Створюємо користувача
#                     user_data = UserCreate(
#                         user_name=row['user_name'],
#                         user_email=row['email'],
#                         password=row['password'],
#                         nick_name=row['nick_name']
#                     )
#                     await user_controller.create(user_data)

#                     # Позначаємо як оброблений
#                     await conn.execute_query("""
#                         UPDATE user_creation_queue
#                         SET processed_at = CURRENT_TIMESTAMP
#                         WHERE id = ?
#                     """, [row['id']])

#                     logger.info(f"User created for {row['email']}")

#                 except Exception as e:
#                     logger.error(f"Error creating user for {row['email']}: {str(e)}")

#         except Exception as e:
#             logger.error(f"Error in user creation worker: {str(e)}")

#         await asyncio.sleep(10)  # Перевіряємо кожні 10 секунд
