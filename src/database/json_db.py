import json
import os
from pathlib import Path

from src.database.interface import DatabaseInterface

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "database.json"


class JsonDatabase(DatabaseInterface):
    def __init__(self, path: str | Path = DB_PATH):
        self.path = Path(path)
        self._ensure_file()

    def _ensure_file(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict):
        self.path.write_text(json.dumps(data, indent=4), encoding="utf-8")

    def get_tracked_products(self, chat_id: str) -> list[dict]:
        data = self._read()
        return data.get(chat_id, [])

    def get_all_tracked_products(self) -> dict[str, list[dict]]:
        return self._read()

    def add_tracked_product(self, chat_id: str, product: str, alert_price: int) -> None:
        data = self._read()
        user_products = data.setdefault(chat_id, [])
        for entry in user_products:
            if entry["product"] == product:
                entry["alert_price"] = alert_price
                break
        else:
            user_products.append({"product": product, "alert_price": alert_price})
        self._write(data)

    def remove_tracked_product(self, chat_id: str, product: str) -> None:
        data = self._read()
        user_products = data.get(chat_id, [])
        data[chat_id] = [p for p in user_products if p["product"] != product]
        self._write(data)
