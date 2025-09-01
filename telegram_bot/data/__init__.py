import json
import os

DATA_DIR = os.path.dirname(__file__)


def get_text(key: str) -> str:
    with open(os.path.join(DATA_DIR, "bot_texts.json"), encoding="utf-8") as f:
        texts = json.load(f)
    return texts.get(key, "")


def get_keyboard(key: str) -> list:
    with open(os.path.join(DATA_DIR, "keyboards.json"), encoding="utf-8") as f:
        keyboards = json.load(f)
    return keyboards.get(key, [])
