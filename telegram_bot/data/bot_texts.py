import json
from pathlib import Path


def get_text(name: str):
    path = Path(__file__).parent / "bot_texts.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get(name, None)
