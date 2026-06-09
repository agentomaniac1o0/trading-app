from pydantic import BaseModel, Field


class TradeCreate(BaseModel):
    asset: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=1, max_length=20)
    market: str = Field(..., min_length=1, max_length=50)
    direction: str = Field(..., pattern="^(LONG|SHORT)$")
    price_open: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)
    cost: float = Field(..., gt=0)
    stop_loss: float | None = None
    signal_source: str | None = None
    notes: str | None = None


class TradeClose(BaseModel):
    price_close: float = Field(..., gt=0)
    date_close: str | None = None
    quantity_close: float | None = None


class TradeResponse(BaseModel):
    id: str
    date_open: str
    asset: str
    symbol: str
    market: str
    direction: str
    price_open: float
    quantity: float
    cost: float
    stop_loss: float | None = None
    status: str
    date_close: str | None
    price_close: float | None
    pnl: float | None
    pnl_pct: float | None
    signal_source: str | None
    notes: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PortfolioSummary(BaseModel):
    initial_capital: float
    cash: float
    short_exposure: float
    net_available: float
    invested: float
    portfolio_value: float
    total_pnl: float
    total_pnl_pct: float
    open_positions: int
    closed_trades: int
    win_rate: float


class PriceResponse(BaseModel):
    symbol: str
    price: float
    currency: str = "USD"
    timestamp: str
    source: str


class AssetResult(BaseModel):
    name: str
    symbol: str
    market: str


class PriceHistoryPoint(BaseModel):
    date: str
    price: float


class TraderProfile(BaseModel):
    key: str
    name: str
    emoji: str
    title: str
    bio: str
    color: str
    avatar_url: str
    avatar_base64: str = ""
    traits: list[str] = []


class PortfolioJudgment(BaseModel):
    trader: str
    judgment: str
    reason: str


class TraderJudgmentCreate(BaseModel):
    symbol: str
    direction: str
    trader: str
    judgment: str
    reason: str


class TraderJudgmentResponse(BaseModel):
    id: str
    symbol: str
    direction: str
    trader: str
    judgment: str
    reason: str
    source: str
    created_at: str

    model_config = {"from_attributes": True}


class PortfolioReviewAsset(BaseModel):
    name: str
    symbol: str
    direction: str
    quantity: int
    live_price: float
    pnl_pct: float
    judgments: list[PortfolioJudgment]


class PortfolioReviewResponse(BaseModel):
    report_date: str
    report_time: str | None = None
    assets: list[PortfolioReviewAsset]


class HealthScore(BaseModel):
    score: int
    level: str
    vm_health: float
    service_health: float
    audit_health: float
    calculated_at: str


class MissioncontrolOverview(BaseModel):
    status: str
    last_report: str
    health_score: int
    disk_usage: dict[str, float]
    crew_status: str
    active_alerts: list[str]


class VmStatus(BaseModel):
    name: str
    status: str
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    uptime_days: int


class ServiceStatus(BaseModel):
    name: str
    online: bool
    port: int
    host: str = "pve-1"


class ProxmoxHost(BaseModel):
    cpu_percent: float
    ram_percent: float
    uptime: str
    kernel_version: str
    updates_pending: bool


class BackupStatus(BaseModel):
    vm_name: str
    last_backup: str
    success: bool
    detail: str = ""


class SysUpdate(BaseModel):
    system: str
    updates_pending: int
    reboot_needed: bool
    kernel: str
    auto_fixes: list[str]
    details: list[str] = []
    warnings: list[str] = []


class MissioncontrolSystem(BaseModel):
    host: ProxmoxHost
    vms: list[VmStatus]
    services: list[ServiceStatus]
    backups: list[BackupStatus]
    updates: list[SysUpdate] = []
    last_report: str = ""


class Finding(BaseModel):
    severity: str
    title: str
    description: str
    auto_fixed: bool


class OpenPort(BaseModel):
    port: int
    service: str
    expected: bool


class MissioncontrolCodeQuality(BaseModel):
    findings: list[Finding]
    open_ports: list[OpenPort]
    hardcoded_secrets: int
    bare_excepts: int
    auto_fix_results: list[str]
    last_report: str = ""


class LiveHeartbeat(BaseModel):
    system: str
    status: str


class LiveServiceCheck(BaseModel):
    service: str
    online: bool
    response_time_ms: int


class MissioncontrolLive(BaseModel):
    heartbeats: list[LiveHeartbeat]
    service_checks: list[LiveServiceCheck]
    timestamp: str


class LivePosition(BaseModel):
    id: str
    symbol: str
    asset: str
    direction: str
    price_open: float
    quantity: float
    cost: float
    price_current: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class LivePortfolioResponse(BaseModel):
    initial_capital: float
    cash: float
    short_exposure: float
    net_available: float
    invested_cost: float
    invested_market: float
    portfolio_value: float
    total_pnl: float
    total_pnl_pct: float
    unrealized_pnl: float
    realized_pnl: float
    open_positions: int
    closed_trades: int
    win_rate: float
    positions: list[LivePosition]


class GraphiphyStats(BaseModel):
    node_count: int
    edge_count: int
    community_count: int
    file_types: dict[str, int]


class GraphiphyGodNode(BaseModel):
    label: str
    degree: int
    community: int
    file_type: str


class GraphiphyNode(BaseModel):
    label: str
    file_type: str
    community: int
    source_file: str
    degree: int
    id: str = ""


class GraphiphyCommunity(BaseModel):
    id: int
    size: int
    top_labels: list[str]


class ReportListItem(BaseModel):
    filename: str
    date: str
    size_bytes: int
    title: str = ""  # Optional title field


class ReportDetail(BaseModel):
    filename: str
    date: str
    content: str
    format: str  # "markdown" or "json"


class HealthTrendPoint(BaseModel):
    date: str
    score: int


class LiveCriticalCount(BaseModel):
    heartbeat_critical: int
    services_offline: int
    total: int