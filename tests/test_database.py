import json
import tempfile
from pathlib import Path

from src.database.json_db import JsonDatabase


def test_add_and_get_tracked_product():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test_db.json"
        db = JsonDatabase(path)

        db.add_tracked_product("123", "iPhone 15 Pro", 900000)
        products = db.get_tracked_products("123")

        assert len(products) == 1
        assert products[0]["product"] == "iPhone 15 Pro"
        assert products[0]["alert_price"] == 900000


def test_remove_tracked_product():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test_db.json"
        db = JsonDatabase(path)

        db.add_tracked_product("123", "iPhone", 900000)
        db.add_tracked_product("123", "Samsung", 500000)
        db.remove_tracked_product("123", "iPhone")

        products = db.get_tracked_products("123")
        assert len(products) == 1
        assert products[0]["product"] == "Samsung"
