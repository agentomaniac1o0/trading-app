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
        "proxmox-host:192.168.0.20,schaltzentrale:100.126.181.63,pbs:192.168.0.80,"
        "website:192.168.0.148,n8n:192.168.0.162,watchdog:192.168.0.149"
    )
    live_tcp_home: str = (
        "SSH (pve-1):100.119.174.53:22,"
        "Nextcloud HTTPS:100.75.220.89:443,"
        "Proxmox Web:100.119.174.53:8006,"
        "Ghost Blog:192.168.0.172:80,"
        "Trading Backend:100.103.32.107:8000,"
        "Flatpak Repo:100.103.32.107:8081,"
        "SSH (ai-agents):100.103.32.107:22,"
        "ComfyUI (LXC 103):100.111.44.63:8188,"
        "Hermes SSH:192.168.0.144:22"
    )
    live_tcp_prod: str = (
        "SSH (Schaltzentrale):100.126.181.63:22,"
        "Proxmox Web UI:192.168.0.20:8006,"
        "Proxmox SSH:192.168.0.20:22,"
        "CronMaster:192.168.0.20:3000,"
        "PBS Web UI:192.168.0.80:8007,"
        "PBS SSH:192.168.0.80:22,"
        "Website HTTP:192.168.0.148:80,"
        "Website SSH:192.168.0.148:22,"
        "n8n Web UI:192.168.0.162:5678,"
        "n8n SSH:192.168.0.162:22,"
        "Watchdog SSH:192.168.0.149:22"
    )
    known_services_str: str = (
        "Uvicorn (Backend):8000:VM 101 – AI Agents,"
        "Flatpak-Repo:8081:VM 101 – AI Agents,"
        "Mission Control:8502:VM 101 – AI Agents,"
        "Trading Dashboard:8501:VM 101 – AI Agents,"
        "MCP-Server:3000:VM 101 – AI Agents,"
        "CrewAI-Scheduler:0:VM 101 – AI Agents,"
        "Ghost Blog:80:LXC 102 – Ghost Blog,"
        "ComfyUI:8188:LXC 103 – Image-Gen,"
        "MariaDB:3306:VM 100 – Nextcloud,"
        "Redis:6379:VM 100 – Nextcloud,"
        "Hermes Gateway:0:LXC 105 – Hermes,"
        "Proxmox Web UI:8006:Proxmox Host,"
        "Proxmox SSH:22:Proxmox Host,"
        "CronMaster:3000:Proxmox Host,"
        "PBS Web UI:8007:PBS (CT 101),"
        "PBS SSH:22:PBS (CT 101),"
        "Website HTTP:80:LXC 102 – Website,"
        "Website SSH:22:LXC 102 – Website,"
        "n8n Web UI:5678:LXC 110 – n8n,"
        "n8n SSH:22:LXC 110 – n8n,"
        "Watchdog:22:RPi 4 – Watchdog,"
        "Schaltzentrale SSH:22:VM 100 – Schaltzentrale,"
        "Tailscale:0:VM 100 – Schaltzentrale,"
        "CrewAI (Monitoring):0:VM 100 – Schaltzentrale"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
