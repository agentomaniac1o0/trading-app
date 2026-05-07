from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/trading.db"
    initial_capital: float = 10000.0
    kucoin_api_key: str = ""
    kucoin_api_secret: str = ""
    kucoin_passphrase: str = ""
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:3000"]
    price_cache_ttl: int = 60
    import_trades_path: str = "../data/trades.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()