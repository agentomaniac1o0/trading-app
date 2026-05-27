import glob
import json
import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas import (
    BackupStatus,
    Finding,
    HealthScore,
    LiveHeartbeat,
    LiveServiceCheck,
    MissioncontrolCodeQuality,
    MissioncontrolLive,
    MissioncontrolOverview,
    MissioncontrolSystem,
    OpenPort,
    ProxmoxHost,
    ServiceStatus,
    VmStatus,
)

router = APIRouter(prefix="/missioncontrol", tags=["missioncontrol"])

MONITORING_DIR = os.path.expanduser("~/agent-templates/monitoring")
REPORTS_DIR = os.path.join(MONITORING_DIR, "reports")
AUDIT_LOG = os.path.join(MONITORING_DIR, "security_audit_log.json")


def _latest_report_path() -> str | None:
    for ext in (".json", ".md"):
        pattern = os.path.join(REPORTS_DIR, f"report_*{ext}")
        files = glob.glob(pattern)
        if files:
            files.sort(key=os.path.getmtime, reverse=True)
            return files[0]
    return None


def _parse_markdown_report(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        text = f.read()

    status = "warning"
    if "status: ✅" in text.lower() or "alle systeme online" in text.lower():
        status = "ok"
    if "kritisch" in text.lower() or "status: 🔴" in text.lower():
        status = "critical"

    date_match = (
        _re_first(r"(\d{2}\.\d{2}\.\d{4})", text)
        or _re_first(r"(\d{4}-\d{2}-\d{2})", text)
        or os.path.basename(path).split("_", 1)[1].rsplit(".", 1)[0]
    )

    disk_usage: dict[str, float] = {}
    for line in text.splitlines():
        m = _re_search(
            r"\|\s*\*?\*?(VM \d+|LXC \d+)\s*[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*(\d+)%",
            line,
        )
        if m:
            disk_usage[m.group(1)] = float(m.group(2))

    alerts: list[str] = []
    for line in text.splitlines():
        if "⚠️" in line and ("warnung" in line.lower() or "wichtig" in line.lower()):
            alerts.append(line.strip().lstrip("|•- \u2022"))

    report_date = _parse_report_date(path)

    return {
        "status": status,
        "last_report": report_date,
        "health_score": _compute_score_from_text(text),
        "disk_usage": disk_usage,
        "crew_status": "completed",
        "active_alerts": alerts[-10:] if alerts else [],
    }


def _parse_report_date(path: str) -> str:
    basename = os.path.basename(path)
    m = _re_first(r"(\d{4}-\d{2}-\d{2})", basename)
    if m:
        date_str = m
        time_str = "08:00"
        tm = _re_first(r"(\d{2}:\d{2})", basename)
        if tm:
            time_str = tm
        return f"{date_str}T{time_str}:00"
    return datetime.now(timezone.utc).isoformat()


def _compute_score_from_text(text: str) -> int:
    score = 100
    if "kritisch" in text.lower():
        score -= 20
    if "⚠️" in text:
        score -= 5 * text.count("⚠️")
    if "offline" in text.lower() or "inaktiv" in text.lower():
        score -= 10
    return max(0, min(100, score))


def _parse_system_from_md(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        text = f.read()

    host = {
        "cpu_percent": 0.0,
        "ram_percent": 0.0,
        "uptime": "",
        "kernel_version": "",
        "updates_pending": False,
    }

    m_ram = _re_search(r"RAM Verwendet\s*\|\s*([\d.]+) GB\s*\|\s*([\d.]+) GB", text)
    if m_ram:
        used = float(m_ram.group(1))
        total = float(m_ram.group(2))
        host["ram_percent"] = round(used / total * 100, 1) if total > 0 else 0.0

    m_uptime = _re_search(r"Uptime\s*\|\s*(.+?)$", text, re.MULTILINE)
    if m_uptime:
        host["uptime"] = m_uptime.group(1).strip()

    m_kernel = _re_search(r"Kernel\s*\|\s*(.+?)$", text, re.MULTILINE)
    if m_kernel:
        host["kernel_version"] = m_kernel.group(1).strip()

    host["updates_pending"] = (
        "update verfügbar" in text.lower()
        or "ausstehende updates" in text.lower()
    )

    vms = []
    for line in text.splitlines():
        m = _re_search(
            r"\|\s*(\d+)\s*\|\s*([A-Za-z0-9\-\s()]+?)\s*\|\s*(✅|❌|⚠️)?\s*(\w+)",
            line,
        )
        if m:
            name = f"VM {m.group(1)}: {m.group(2).strip()}"
            status = "running"
            if m.group(3) == "❌":
                status = "stopped"
            vms.append(
                {
                    "name": name,
                    "status": status,
                    "cpu_percent": 0.0,
                    "ram_percent": 0.0,
                    "disk_percent": 0.0,
                    "uptime_days": 0,
                }
            )

    services = []
    service_section = False
    for line in text.splitlines():
        if "dienst" in line.lower() and "status" in line.lower():
            service_section = True
            continue
        if service_section and line.startswith("##"):
            service_section = False
        if service_section:
            m_svc = _re_search(r"\|\s*(\w[\w\s\-\.]+)\s*\|\s*(✅|❌)\s*(\w+)", line)
            if m_svc:
                services.append(
                    {
                        "name": m_svc.group(1).strip(),
                        "online": m_svc.group(2) == "✅",
                        "port": 0,
                    }
                )

    backups = []
    backup_section = False
    for line in text.splitlines():
        if "backup" in line.lower():
            backup_section = True
            continue
        if backup_section and line.startswith("##"):
            backup_section = False
        if backup_section:
            m_bkp = _re_search(
                r"\|\s*(VM \d+|LXC \d+)\s*[^|]*\|\s*(\d{2}\.\d{2}\.\d{4})\s*\|\s*(\d+)\s*Tage?\s*\|\s*(✅|⚠️)",
                line,
            )
            if m_bkp:
                try:
                    date_str = m_bkp.group(2)
                    dt = datetime.strptime(date_str, "%d.%m.%Y")
                    backups.append(
                        {
                            "vm_name": m_bkp.group(1),
                            "last_backup": dt.isoformat(),
                            "success": m_bkp.group(4) == "✅",
                        }
                    )
                except ValueError:
                    pass

    return {
        "host": host,
        "vms": vms,
        "services": services,
        "backups": backups,
    }


def _parse_code_quality() -> dict:
    findings: list[dict] = []
    open_ports: list[dict] = []
    hardcoded_secrets = 0
    bare_excepts = 0
    auto_fix_results: list[str] = []

    if os.path.exists(AUDIT_LOG):
        with open(AUDIT_LOG, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except (json.JSONDecodeError, Exception):
                data = []

            if isinstance(data, list):
                data = data[-1] if data else {}

            for finding in data.get("findings", []):
                ft = finding.get("type", "")
                if ft == "hardcoded_secret":
                    hardcoded_secrets += 1
                elif ft == "bare_except":
                    bare_excepts += 1
                elif "port" in ft or "interface" in ft:
                    open_ports.append(
                        {
                            "port": finding.get("port", 0),
                            "service": finding.get("process", finding.get("detail", "")),
                            "expected": False,
                        }
                    )
                findings.append(
                    {
                        "severity": finding.get("severity", "info"),
                        "title": finding.get("detail", finding.get("type", "")),
                        "description": finding.get("fix", ""),
                        "auto_fixed": finding.get("auto_fixed", False),
                    }
                )

    return {
        "findings": findings,
        "open_ports": open_ports,
        "hardcoded_secrets": hardcoded_secrets,
        "bare_excepts": bare_excepts,
        "auto_fix_results": auto_fix_results,
    }


@router.get("/{location}/overview", response_model=MissioncontrolOverview)
async def get_overview(location: str):
    if location != "home-lab":
        return MissioncontrolOverview(
            status="pending",
            last_report=datetime.now(timezone.utc).isoformat(),
            health_score=0,
            disk_usage={},
            crew_status="not_configured",
            active_alerts=[],
        )

    path = _latest_report_path()
    if not path:
        return MissioncontrolOverview(
            status="unknown",
            last_report=datetime.now(timezone.utc).isoformat(),
            health_score=0,
            disk_usage={},
            crew_status="no_report",
            active_alerts=[],
        )

    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return MissioncontrolOverview(**data.get("overview", data))

    return MissioncontrolOverview(**_parse_markdown_report(path))


@router.get("/{location}/system", response_model=MissioncontrolSystem)
async def get_system(location: str):
    if location != "home-lab":
        return MissioncontrolSystem(
            host=ProxmoxHost(
                cpu_percent=0, ram_percent=0, uptime="", kernel_version="", updates_pending=False
            ),
            vms=[],
            services=[],
            backups=[],
        )

    path = _latest_report_path()
    if not path:
        return MissioncontrolSystem(
            host=ProxmoxHost(
                cpu_percent=0, ram_percent=0, uptime="", kernel_version="", updates_pending=False
            ),
            vms=[],
            services=[],
            backups=[],
        )

    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return MissioncontrolSystem(**data.get("system", data))

    return MissioncontrolSystem(**_parse_system_from_md(path))


@router.get("/{location}/code-quality", response_model=MissioncontrolCodeQuality)
async def get_code_quality(location: str):
    if location != "home-lab":
        return MissioncontrolCodeQuality(
            findings=[], open_ports=[], hardcoded_secrets=0, bare_excepts=0, auto_fix_results=[]
        )

    return MissioncontrolCodeQuality(**_parse_code_quality())


@router.get("/{location}/live", response_model=MissioncontrolLive)
async def get_live(location: str):
    return MissioncontrolLive(
        heartbeats=[
            LiveHeartbeat(system="pve-1", status="ok"),
            LiveHeartbeat(system="nextcloud", status="ok"),
            LiveHeartbeat(system="ai-agents", status="ok"),
            LiveHeartbeat(system="ghost-blog", status="ok"),
            LiveHeartbeat(system="image-gen", status="ok"),
        ],
        service_checks=[],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{location}/health", response_model=HealthScore)
async def get_health(location: str):
    if location != "home-lab":
        return HealthScore(
            score=0,
            level="offline",
            vm_health=0.0,
            service_health=0.0,
            audit_health=0.0,
            calculated_at=datetime.now(timezone.utc).isoformat(),
        )

    path = _latest_report_path()
    text = ""
    if path:
        with open(path, encoding="utf-8") as f:
            text = f.read()

    score = _compute_score_from_text(text) if text else 0
    level = "good"
    if score < 50:
        level = "critical"
    elif score < 80:
        level = "warning"

    return HealthScore(
        score=score,
        level=level,
        vm_health=100.0 if "alle systeme online" in text.lower() else 50.0,
        service_health=100.0 if "✅ active" in text else 60.0,
        audit_health=50.0,
        calculated_at=datetime.now(timezone.utc).isoformat(),
    )


def _re_first(pattern: str, text: str):
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _re_search(pattern: str, text: str, flags=0):
    return re.search(pattern, text, flags)
