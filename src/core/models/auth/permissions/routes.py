from fastapi import APIRouter, Depends, HTTPException

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import BackgroundTasks

from .schemas import RequestOTPSchema, VerifyOTPSchema
from .controller import permissions_controller


router = APIRouter(
    prefix="/auth",
    tags=["auth", "permissions", "otp"],
    responses={404: {"description": "Not found"}},
)


@router.post("/token", summary="Get access token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Отримати токен доступу"""
    return await permissions_controller.login(form_data.username, form_data.password)


@router.get("/health")
async def health_check():
    """Перевірка статусу системи"""
    return await permissions_controller.health_check()


@router.post("/request-otp", summary="Request OTP for registration")
async def request_otp(
    data: RequestOTPSchema = Depends(), background_tasks: BackgroundTasks = None
):
    """Запит OTP для реєстрації"""
    return await permissions_controller.request_otp(data, background_tasks)


@router.post("/verify-otp", summary="Verify OTP")
async def verify_otp_register(data: VerifyOTPSchema = Depends()):
    """Перевірка OTP для реєстрації"""
    return await permissions_controller.verify_otp_register(data)


@router.post("/login-with-otp", summary="Login with OTP")
async def login_with_otp(email: str, otp: str):
    """Вхід за допомогою OTP"""
    return await permissions_controller.login_with_otp(email, otp)


@router.post("/check-email", summary="Check if email exists")
async def check_email(email: str):
    """Перевірка наявності email у системі"""
    return await permissions_controller.check_email(email)
