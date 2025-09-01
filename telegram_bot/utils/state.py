# Простий state-кеш для зберігання статусу телефону користувача на час сесії
class PhoneState:
    _has_phone = {}

    @classmethod
    def set(cls, user_id: int, has_phone: bool):
        cls._has_phone[user_id] = has_phone

    @classmethod
    def get(cls, user_id: int) -> bool:
        return cls._has_phone.get(user_id, False)

    @classmethod
    def clear(cls, user_id: int):
        if user_id in cls._has_phone:
            del cls._has_phone[user_id]
