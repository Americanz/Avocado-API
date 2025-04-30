from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import BackgroundTasks

from src.core.models.auth.otps.schemas import (
    RequestOTPSchema,
    VerifyOTPSchema,
)
from src.core.models.auth.otps.controller import otp_controller


# Створюємо маршрутизатор для кастомних авторизаційних ендпоінтів
router = APIRouter(
    tags=["otp"],
    responses={404: {"description": "Not found"}},
)


@router.post("/token", summary="Get access token")
async def login_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Отримати токен доступу"""
    return await otp_controller.login_token(form_data.username, form_data.password)


@router.post("/request-otp", summary="Request OTP for registration")
async def request_otp(
    data: RequestOTPSchema = Depends(), background_tasks: BackgroundTasks = None
):
    """Запит OTP для реєстрації"""
    return await otp_controller.request_otp(data, background_tasks)


@router.post("/verify-otp", summary="Verify OTP")
async def verify_otp_register(data: VerifyOTPSchema = Depends()):
    """Перевірка OTP для реєстрації"""
    return await otp_controller.verify_otp_register(data)


@router.post("/login-with-otp", summary="Login with OTP")
async def login_with_otp(email: str, otp: str):
    """Вхід за допомогою OTP"""
    return await otp_controller.login_with_otp(email, otp)


@router.post("/check-email", summary="Check if email exists")
async def check_email(email: str):
    """Перевірка наявності email у системі"""
    return await otp_controller.check_email(email)
