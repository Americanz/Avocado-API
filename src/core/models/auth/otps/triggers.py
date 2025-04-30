# from src.core.db.trigger.base_trigger import BaseTrigger
# from tortoise.models import Q
# from datetime import datetime, timedelta
# from src.modules.auth.roles.controller import role_controller
# from loguru import logger
# from .model import OTP

# class OTPCleanupTrigger(BaseTrigger):
#     name = "otp_cleanup"
#     model = OTP

#     async def execute(self) -> None:
#         """Очищення старих OTP записів"""
#         try:
#             deleted_count = await self.model.filter(
#                 Q(expires_at__lt=datetime.now()) |
#                 (Q(is_used=True) & Q(create_time__lt=datetime.now() - timedelta(hours=24)))
#             ).delete()

#             logger.info(f"Cleaned up {deleted_count} expired OTP records")

#         except Exception as e:
#             logger.error(f"Error cleaning up OTP records: {str(e)}")
#             raise

# class UserCreationTrigger(BaseTrigger):
#     name = "user_creation"
#     model = OTP

#     async def execute(self) -> None:
#         """Створення користувачів з верифікованих OTP"""
#         from src.modules.auth.users.controller import user_controller
#         from src.modules.auth.users.schemas import UserCreate

#         try:
#             verified_otps = await self.model.filter(
#                 is_used=True
#             ).filter(
#                 Q(processed_at__isnull=True)
#             )

#             for otp in verified_otps:
#                 role = await role_controller.get_by_code("R_USER")
#                 try:
#                     user_data = UserCreate(
#                         user_name=otp.email,
#                         user_email=otp.email,
#                         nick_name=otp.email,
#                         password=otp.code
#                     )
#                     user = await user_controller.create(user_data)

#                     if role:
#                         await user.roles.add(role)

#                     otp.processed_at = datetime.now()
#                     await otp.save()

#                     logger.info(f"Created user for {otp.email}")

#                 except Exception as e:
#                     logger.error(f"Error creating user for OTP {otp.id}: {str(e)}")

#         except Exception as e:
#             logger.error(f"Error processing user creation: {str(e)}")
#             raise
