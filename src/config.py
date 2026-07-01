from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_token: str = ""
    chat_id: str = ""
    gemini_api_key: str = ""
    db_name: str = "price_sniper_bot"
    db_user: str = "postgres"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
