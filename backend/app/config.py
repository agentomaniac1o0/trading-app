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
    api_key: str = ""
    live_targets_home: str = (
        "pve-1:100.119.174.53,nextcloud:100.75.220.89,ai-agents:127.0.0.1,"
        "ghost-blog:192.168.0.172,image-gen:100.111.44.63"
    )
    live_targets_prod: str = (
        "proxmox-host:100.97.55.39,schaltzentrale:100.126.181.63,pbs:192.168.0.80"
    )
    live_tcp_home: str = (
        "SSH (pve-1):100.119.174.53:22,"
        "Nextcloud HTTPS:100.75.220.89:443,"
        "Proxmox Web:100.119.174.53:8006,"
        "Ghost Blog:192.168.0.172:80"
    )
    live_tcp_prod: str = (
        "SSH:100.126.181.63:22,Proxmox Web UI:192.168.0.20:8006"
    )
    known_services_str: str = (
        "Uvicorn (Backend):8000:VM 101 – AI Agents,"
        "Flatpak-Repo:8081:VM 101 – AI Agents,"
        "Mission Control:8502:VM 101 – AI Agents,"
        "Trading Dashboard:8501:VM 101 – AI Agents,"
        "MCP-Server:3000:VM 101 – AI Agents,"
        "CrewAI-Scheduler:0:VM 101 – AI Agents,"
        "Ghost Blog:80:LXC 102 – Ghost Blog"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()