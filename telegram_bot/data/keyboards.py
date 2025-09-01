import json
from pathlib import Path


def get_keyboard(name: str, required: bool = False):
    path = Path(__file__).parent / "keyboards.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    kb = data.get(name, [])
    if required and not kb:
        raise Exception(
            f"Клавіатура '{name}' не налаштована. Зверніться до адміністратора!"
        )
    return kb
