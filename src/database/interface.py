from abc import ABC, abstractmethod


class DatabaseInterface(ABC):
    @abstractmethod
    def get_tracked_products(self, chat_id: str) -> list[dict]:
        ...

    @abstractmethod
    def get_all_tracked_products(self) -> dict[str, list[dict]]:
        ...

    @abstractmethod
    def add_tracked_product(self, chat_id: str, product: str, alert_price: int) -> None:
        ...

    @abstractmethod
    def remove_tracked_product(self, chat_id: str, product: str) -> None:
        ...
