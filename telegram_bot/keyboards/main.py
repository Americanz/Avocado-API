from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мій баланс")],
        [KeyboardButton(text="Історія бонусів")],
    ],
    resize_keyboard=True,
)
