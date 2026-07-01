from src.database.interface import DatabaseInterface


class PostgresDatabase(DatabaseInterface):
    def get_tracked_products(self, chat_id: str) -> list[dict]:
        raise NotImplementedError

    def get_all_tracked_products(self) -> dict[str, list[dict]]:
        raise NotImplementedError

    def add_tracked_product(self, chat_id: str, product: str, alert_price: int) -> None:
        raise NotImplementedError

    def remove_tracked_product(self, chat_id: str, product: str) -> None:
        raise NotImplementedError
