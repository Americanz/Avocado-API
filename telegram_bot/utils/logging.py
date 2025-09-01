"""
Утиліта для логування дій користувачів
"""
import logging
from telegram_bot.config import settings
from aiogram.types import Message, CallbackQuery, User

logger = logging.getLogger(__name__)


def log_user_action(action_type: str, user: User, details: str = "", **kwargs):
    """
    Логування дій користувача з можливістю включення/виключення
    
    Args:
        action_type: Тип дії (command, button, message, etc.)
        user: Об'єкт користувача Telegram
        details: Додаткові деталі
        **kwargs: Додаткові параметри для логування
    """
    if not settings.LOG_USER_ACTIONS:
        return
    
    # Базова інформація про користувача
    user_info = f"{user.id}"
    if user.username:
        user_info += f" (@{user.username})"
    if user.first_name:
        user_info += f" [{user.first_name}"
        if user.last_name:
            user_info += f" {user.last_name}"
        user_info += "]"
    
    # Формуємо повідомлення залежно від типу дії
    if action_type == "command" and settings.LOG_COMMANDS:
        logger.info(f"🔧 Команда {details} від {user_info}")
    elif action_type == "button" and settings.LOG_BUTTON_CLICKS:
        logger.info(f"🔘 Кнопка '{details}' від {user_info}")
    elif action_type == "message" and settings.LOG_MESSAGES:
        logger.info(f"💬 Повідомлення '{details}' від {user_info}")
    elif action_type == "callback" and settings.LOG_BUTTON_CLICKS:
        logger.info(f"⚡ Callback '{details}' від {user_info}")
    elif action_type == "fsm" and settings.VERBOSE_LOGGING:
        logger.info(f"🔄 FSM '{details}' від {user_info}")
    elif action_type == "admin" and settings.LOG_USER_ACTIONS:
        logger.info(f"👑 Адмін дія '{details}' від {user_info}")
    elif action_type == "error":
        logger.error(f"❌ Помилка '{details}' від {user_info}")
    
    # Додаткове детальне логування
    if settings.VERBOSE_LOGGING and kwargs:
        for key, value in kwargs.items():
            logger.debug(f"   {key}: {value}")


def log_command(message: Message, command: str):
    """Логування команди"""
    log_user_action("command", message.from_user, command, message_id=message.message_id)


def log_button_click(message: Message, button_text: str, handler_name: str = ""):
    """Логування натискання кнопки"""
    details = button_text
    if handler_name and settings.VERBOSE_LOGGING:
        details += f" (handler: {handler_name})"
    log_user_action("button", message.from_user, details, 
                   message_id=message.message_id, handler=handler_name)


def log_callback_query(query: CallbackQuery, callback_data: str):
    """Логування callback запиту"""
    log_user_action("callback", query.from_user, callback_data, 
                   query_id=query.id)


def log_message(message: Message, content: str = ""):
    """Логування повідомлення користувача"""
    if not content:
        content = message.text or "[не текст]"
    log_user_action("message", message.from_user, content[:50] + "..." if len(content) > 50 else content,
                   message_id=message.message_id, chat_id=message.chat.id)


def log_fsm_state(message: Message, state: str, action: str = ""):
    """Логування зміни FSM стану"""
    details = f"{state}"
    if action:
        details += f" ({action})"
    log_user_action("fsm", message.from_user, details,
                   message_id=message.message_id)


def log_admin_action(message: Message, action: str, target: str = ""):
    """Логування дій адміністратора"""
    details = action
    if target:
        details += f" -> {target}"
    log_user_action("admin", message.from_user, details,
                   message_id=message.message_id)


def log_error(user: User, error: str, context: str = ""):
    """Логування помилок"""
    details = error
    if context:
        details = f"{context}: {error}"
    log_user_action("error", user, details)


def get_logging_status():
    """Отримати поточний статус налаштувань логування"""
    return {
        "user_actions": settings.LOG_USER_ACTIONS,
        "button_clicks": settings.LOG_BUTTON_CLICKS,
        "commands": settings.LOG_COMMANDS,
        "messages": settings.LOG_MESSAGES,
        "verbose": settings.VERBOSE_LOGGING,
    }
