"""
Menu manager module for Telegram bot.

Manages menu rendering, navigation, and button handling.
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Callable
from aiogram import types
from aiogram.types import Message, ReplyKeyboardMarkup

from .state import NavigationState
from telegram_bot.data.bot_texts import get_text
from telegram_bot.states.phone_state import PhoneState

logger = logging.getLogger("telegram_bot.navigation")


class MenuManager:
    """
    Manages menu rendering, navigation between menus, and button handling.

    Features:
    - Menu registration and rendering
    - Navigation tracking
    - Dynamic button filtering
    - Multi-level menu support
    - Back button handling
    """

    def __init__(self, keyboards_path: str = None):
        """
        Initialize the menu manager.

        Args:
            keyboards_path: Path to the keyboards JSON file
        """
        self.keyboards_path = keyboards_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "keyboards.json"
        )
        self._keyboards = self._load_keyboards()
        self._button_handlers = {}
        self._role_checkers = {}

    def _load_keyboards(self) -> dict:
        """Load keyboards from JSON file."""
        try:
            with open(self.keyboards_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading keyboards: {e}")
            return {}

    def register_button_handler(self, handler_name: str, handler_func: Callable):
        """Register a button handler function."""
        self._button_handlers[handler_name] = handler_func

    def register_role_checker(self, role_name: str, checker_func: Callable):
        """Register a role checker function."""
        self._role_checkers[role_name] = checker_func

    def get_keyboard_markup(
        self, menu_name: str, user_id: int = None, filter_roles: bool = True
    ) -> ReplyKeyboardMarkup:
        """
        Build a keyboard markup for a specific menu.

        Args:
            menu_name: Menu identifier
            user_id: User ID for role-based filtering
            filter_roles: Whether to filter buttons by user roles

        Returns:
            ReplyKeyboardMarkup with buttons for the menu
        """
        # Отримаємо кнопки відповідно до меню
        buttons = self.get_keyboard_buttons(menu_name, user_id, filter_roles)

        # Якщо це головне меню (main) і користувач є адміністратором, додаємо кнопку адміна
        if menu_name == "main" and user_id and self._has_admin_role(user_id):
            admin_buttons = [
                btn
                for btn in self.get_keyboard_buttons("admin", user_id)
                if btn.get("handler") == "admin_panel"
            ]
            buttons.extend(admin_buttons)

        # Якщо у користувача є телефон, не показуємо кнопку поділитись номером
        if user_id and self.check_phone_required(user_id):
            buttons = [
                btn for btn in buttons if btn.get("text") != "Поділитись номером"
            ]

        # Transform buttons to aiogram format
        rows = []
        current_row = []
        max_buttons_per_row = 3  # Default max buttons per row

        # Process buttons and organize them into rows
        for btn in buttons:
            button_text = btn["text"]
            if len(current_row) >= max_buttons_per_row:
                rows.append(current_row)
                current_row = []

            # Check if this is a "back" button, they usually go in their own row
            if button_text.startswith("⬅️ 77"):
                if current_row:
                    rows.append(current_row)
                    current_row = []
                rows.append([types.KeyboardButton(text=button_text)])
            else:
                current_row.append(types.KeyboardButton(text=button_text))

        # Add any remaining buttons
        if current_row:
            rows.append(current_row)

        return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    def get_keyboard_buttons(
        self, menu_name: str, user_id: int = None, filter_roles: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get buttons for a specific menu, filtered by roles if needed.

        Args:
            menu_name: Menu identifier
            user_id: User ID for role-based filtering
            filter_roles: Whether to filter buttons by user roles

        Returns:
            List of button configurations
        """
        keyboard_buttons = self._keyboards.get(menu_name, [])

        # Filter by role if needed
        if filter_roles and user_id:
            filtered_buttons = []
            for btn in keyboard_buttons:
                # Skip disabled buttons
                if not btn.get("enabled", True):
                    continue

                # Check role requirements if any
                required_role = btn.get("requires_role")
                if required_role:
                    checker = self._role_checkers.get(required_role)
                    if not checker or not checker(user_id):
                        continue

                filtered_buttons.append(btn)
            return filtered_buttons

        # Otherwise just return enabled buttons
        return [btn for btn in keyboard_buttons if btn.get("enabled", True)]

    async def navigate_to(
        self,
        message: Message,
        menu_name: str,
        text: str = None,
        parent_menu: str = None,
        user_id: int = None,
    ) -> None:
        """
        Navigate to a specific menu and send the menu message.

        Args:
            message: Telegram message for reply
            menu_name: Target menu name
            text: Optional message text
            parent_menu: Optional parent menu name for back functionality
            user_id: User ID for navigation tracking
        """
        if user_id is None:
            user_id = message.from_user.id

        # Update navigation state
        NavigationState.set_current_menu(user_id, menu_name, parent_menu)

        # Build keyboard markup
        keyboard = self.get_keyboard_markup(menu_name, user_id)

        # Use default text if none provided
        if text is None:
            text = get_text(f"menu_{menu_name}") or f"Menu {menu_name}"

        # Send message with keyboard
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    async def handle_button(self, message: Message) -> bool:
        """
        Find and execute handler for button text from message.

        Args:
            message: Telegram message with button text

        Returns:
            True if a handler was found and executed, False otherwise
        """
        user_id = message.from_user.id
        button_text = message.text
        current_menu = NavigationState.get_current_menu(user_id)

        # Look for button in current menu first
        buttons = self.get_keyboard_buttons(current_menu, user_id)

        # If not found in current menu, check main and admin menus
        if not buttons:
            buttons = self.get_keyboard_buttons("main", user_id)
            # Add admin buttons if appropriate
            if self._has_admin_role(user_id):
                buttons += self.get_keyboard_buttons("admin", user_id)

        # Find matching button
        for btn in buttons:
            if btn["text"] == button_text and btn.get("handler"):
                handler_name = btn["handler"]
                handler = self._button_handlers.get(handler_name)

                if handler:
                    try:
                        # Check for silent parameter on back buttons
                        silent = btn.get("silent", False)

                        # Add context info to the handler call
                        await handler(message, silent=silent, navigation=self)

                        # Видаляємо повідомлення користувача з текстом кнопки, щоб чат був чистішим
                        try:
                            await message.delete()
                        except Exception as e:
                            logger.warning(f"Could not delete message: {e}")

                        return True
                    except Exception as e:
                        logger.error(f"Error in button handler '{handler_name}': {e}")
                        await message.answer("Error processing button command.")
                        return True
                else:
                    logger.warning(
                        f"Handler '{handler_name}' not found for button '{button_text}'"
                    )

        return False

    async def go_back(self, message: Message, silent: bool = False) -> None:
        """
        Navigate back to previous menu.

        Args:
            message: Telegram message
            silent: Whether to use minimal message for navigation
        """
        user_id = message.from_user.id
        previous_menu = NavigationState.go_back(user_id)

        # Build keyboard for previous menu
        keyboard = self.get_keyboard_markup(previous_menu, user_id)

        # Use minimal message if silent
        if silent:
            await message.answer("◀️", reply_markup=keyboard)
        else:
            menu_text = get_text(f"menu_{previous_menu}") or f"Menu {previous_menu}"
            await message.answer(menu_text, reply_markup=keyboard, parse_mode="HTML")

    def _has_admin_role(self, user_id: int) -> bool:
        """Check if user has admin role."""
        from telegram_bot.handlers.common.permissions import get_admin_ids

        return str(user_id) in get_admin_ids()

    def check_phone_required(self, user_id: int) -> bool:
        """
        Check if phone number is required for user.

        Returns:
            False if phone is required but not provided, True otherwise
        """
        # Check cached phone state first
        has_phone = PhoneState.get(user_id)
        if has_phone:
            return True  # If not in cache, check database
        from telegram_bot.services.supabase import supabase_bonuses_service

        try:
            user = (
                supabase_bonuses_service.client.table("bot_users")
                .select("phone")
                .eq("user_id", user_id)
                .execute()
            )
            if user.data and user.data[0].get("phone"):
                PhoneState.set(user_id, True)
                return True
            else:
                PhoneState.set(user_id, False)
                return False
        except Exception as e:
            logger.error(f"Error checking phone in database: {e}")
            return False
