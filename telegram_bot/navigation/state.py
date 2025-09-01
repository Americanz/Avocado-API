"""
Module for managing navigation state in the Telegram bot.

This module provides a simple cache mechanism for tracking user navigation state.
"""


class NavigationState:
    """
    Manages navigation state for users.

    Tracks current menu level, parent menu, and navigation history for each user.
    """

    _menu_states = (
        {}
    )  # user_id -> {"current": current_menu, "parent": parent_menu, "history": [...]}

    @classmethod
    def set_current_menu(cls, user_id: int, menu_name: str, parent_menu: str = None):
        """
        Set the current menu for a user and update navigation history.

        Args:
            user_id: Telegram user ID
            menu_name: Current menu identifier
            parent_menu: Parent menu identifier
        """
        if user_id not in cls._menu_states:
            cls._menu_states[user_id] = {
                "current": menu_name,
                "parent": parent_menu,
                "history": [],
            }
        else:
            # Add current to history before changing
            current = cls._menu_states[user_id]["current"]
            if current and current != menu_name:
                history = cls._menu_states[user_id]["history"]
                # Avoid duplicates in history
                if not history or history[-1] != current:
                    history.append(current)
                # Keep history at reasonable size
                if len(history) > 10:
                    history = history[-10:]
                cls._menu_states[user_id]["history"] = history

            # Update current menu and parent
            cls._menu_states[user_id]["current"] = menu_name
            if parent_menu:
                cls._menu_states[user_id]["parent"] = parent_menu

    @classmethod
    def get_current_menu(cls, user_id: int) -> str:
        """Get current menu for a user."""
        if user_id in cls._menu_states:
            return cls._menu_states[user_id]["current"]
        return "main"  # Default to main menu

    @classmethod
    def get_parent_menu(cls, user_id: int) -> str:
        """Get parent menu for a user."""
        if user_id in cls._menu_states:
            return cls._menu_states[user_id]["parent"]
        return None

    @classmethod
    def go_back(cls, user_id: int) -> str:
        """
        Go back to the previous menu and return its name.

        Returns:
            The previous menu name or "main" if history is empty
        """
        if user_id not in cls._menu_states:
            return "main"

        history = cls._menu_states[user_id]["history"]
        if history:
            previous_menu = history.pop()
            cls._menu_states[user_id]["current"] = previous_menu
            return previous_menu
        else:
            # If history is empty, fallback to parent or main
            parent = cls._menu_states[user_id].get("parent")
            if parent:
                cls._menu_states[user_id]["current"] = parent
                return parent
            else:
                cls._menu_states[user_id]["current"] = "main"
                return "main"

    @classmethod
    def clear(cls, user_id: int):
        """Clear navigation state for a user."""
        if user_id in cls._menu_states:
            del cls._menu_states[user_id]
