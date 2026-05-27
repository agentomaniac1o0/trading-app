import glob
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response

from app.schemas import (
    BackupStatus,
    Finding,
    GraphiphyCommunity,
    GraphiphyGodNode,
    GraphiphyNode,
    GraphiphyStats,
    HealthScore,
    HealthTrendPoint,
    LiveCriticalCount,
    LiveHeartbeat,
    LiveServiceCheck,
    MissioncontrolCodeQuality,
    MissioncontrolLive,
    MissioncontrolOverview,
    MissioncontrolSystem,
    OpenPort,
    ProxmoxHost,
    ReportDetail,
    ReportListItem,
    ServiceStatus,
    SysUpdate,
    VmStatus,
)

router = APIRouter(prefix="/missioncontrol", tags=["missioncontrol"])

# ── Home-Lab Pfade ─────────────────────────────────────────────────────
MONITORING_DIR = os.path.expanduser("~/agent-templates/monitoring")
REPORTS_DIR = os.path.join(MONITORING_DIR, "reports")
AUDIT_LOG = os.path.join(MONITORING_DIR, "security_audit_log.json")

# ── Production-Center Pfade (via SSH-Pull) ─────────────────────────────
PROD_MONITORING_DIR = os.path.expanduser("~/agent-templates/monitoring/production-center")
PROD_REPORTS_DIR = os.path.join(PROD_MONITORING_DIR, "reports")
PROD_AUDIT_LOG = os.path.join(PROD_MONITORING_DIR, "security_audit_log.json")
PROD_GRAPHIFY_DIR = os.path.join(PROD_MONITORING_DIR, "graphify-out")


def _build_overview(data: dict) -> MissioncontrolOverview:
    o = dict(data.get("overview", data))
    if "last_report" not in o:
        rd = data.get("report_date", "")
        rt = data.get("report_time", "00:00")
        o["last_report"] = f"{rd}T{rt}:00"
    return MissioncontrolOverview(**o)


def _reports_dir(location: str) -> str:
    return PROD_REPORTS_DIR if location == "production-center" else REPORTS_DIR


def _audit_log_path(location: str) -> str:
    return PROD_AUDIT_LOG if location == "production-center" else AUDIT_LOG


def _latest_report_path(location: str = "home-lab") -> str | None:
    base = _reports_dir(location)
    if not os.path.isdir(base):
        return None
    for ext in (".json", ".md"):
        pattern = os.path.join(base, f"report_*{ext}")
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
        if "⚠" in line and ("warnung" in line.lower() or "wichtig" in line.lower()):
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
    critical_count = (
        text.lower().count("kritisch") - text.lower().count("nicht kritisch")
        + text.count("🔴")
    )
    score -= min(critical_count * 5, 30)
    warning_count = text.count("⚠")
    score -= min(warning_count * 2, 15)
    offline_services = text.lower().count("inaktiv") + text.lower().count("gestoppt")
    score -= min(offline_services * 3, 10)
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

    # Host RAM: "RAM Gesamt | 31,1 GB" + "RAM Verfügbar | 13,3 GB"
    m_ram_total = re.search(r"RAM Gesamt\s*\|\s*([\d.,]+)\s*GB", text)
    m_ram_avail = re.search(r"RAM Verfügbar\s*\|\s*([\d.,]+)\s*GB", text)
    if m_ram_total and m_ram_avail:
        total = float(m_ram_total.group(1).replace(",", "."))
        avail = float(m_ram_avail.group(1).replace(",", "."))
        host["ram_percent"] = round(((total - avail) / total) * 100, 1) if total > 0 else 0

    # Host CPU: "CPU Auslastung | X %" or "CPU usage X%"
    m_cpu = re.search(r"CPU (?:Auslastung|usage)\s*\|\s*([\d.,]+)\s*%", text)
    if m_cpu:
        host["cpu_percent"] = float(m_cpu.group(1).replace(",", "."))

    # Uptime
    m_uptime = re.search(r"Uptime\s*\|\s*(.+)", text)
    if m_uptime:
        host["uptime"] = m_uptime.group(1).strip()

    # Kernel
    m_kernel = re.search(r"Kernel\s*\|\s*(.+)", text)
    if m_kernel:
        host["kernel_version"] = m_kernel.group(1).strip()

    # Updates pending
    host["updates_pending"] = "Updates verfügbar" in text or "updates pending" in text.lower()

    # VMs – parse table format: | VM ID | Name | Status | CPU | RAM | Disk |
    vms = []
    vm_section = False
    for line in text.splitlines():
        line = line.strip()
        if not vm_section and any(kw in line.lower() for kw in ("vms/lxc", "virtual machines", "vm status")):
            vm_section = True
            continue
        if vm_section and not line.startswith("|"):
            if line and "|" not in line:
                vm_section = False
            continue
        if vm_section and line.startswith("|") and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 5 and not parts[0].lower().startswith(("vm", "name", "id")):
                try:
                    vms.append({
                        "name": parts[1] if len(parts) > 1 else parts[0],
                        "status": parts[2] if len(parts) > 2 else "unknown",
                        "cpu_percent": _parse_float(parts[3]) if len(parts) > 3 else 0,
                        "ram_percent": _parse_float(parts[4]) if len(parts) > 4 else 0,
                        "disk_percent": _parse_float(parts[5]) if len(parts) > 5 else 0,
                        "uptime_days": 0,
                    })
                except (ValueError, IndexError):
                    pass

    # Services
    services = []
    svc_section = False
    for line in text.splitlines():
        line = line.strip()
        if not svc_section and any(kw in line.lower() for kw in ("services", "dienste")):
            svc_section = True
            continue
        if svc_section and not line.startswith("|"):
            if line and "|" not in line:
                svc_section = False
            continue
        if svc_section and line.startswith("|") and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3 and not parts[0].lower().startswith(("service", "name")):
                online = any(w in parts[2].lower() for w in ("online", "active", "✅", "laufend"))
                try:
                    port = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                except ValueError:
                    port = 0
                services.append({"name": parts[0], "online": online, "port": port})

    # Backups
    backups = []
    bkp_section = False
    for line in text.splitlines():
        line = line.strip()
        if not bkp_section and any(kw in line.lower() for kw in ("backup", "sicherung")):
            bkp_section = True
            continue
        if bkp_section and not line.startswith("|"):
            if line and "|" not in line:
                bkp_section = False
            continue
        if bkp_section and line.startswith("|") and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3 and not parts[0].lower().startswith(("vm", "name")):
                success = all(w not in parts[2].lower() for w in ("fehlgeschlagen", "failed", "❌"))
                backups.append({
                    "vm_name": parts[0],
                    "last_backup": parts[1] if len(parts) > 1 else "",
                    "success": success,
                })

    return {
        "host": host,
        "vms": vms,
        "services": services,
        "backups": backups,
    }


def _parse_float(val: str) -> float:
    val = re.sub(r"[^\d.,-]", "", val)
    try:
        return float(val.replace(",", "."))
    except ValueError:
        return 0.0


def _parse_code_quality() -> dict:
    findings = []
    open_ports = []
    audit_log = os.path.expanduser("~/agent-templates/monitoring/security_audit_log.json")
    if os.path.exists(audit_log):
        try:
            with open(audit_log, encoding="utf-8") as f:
                data = json.load(f)
            for fg in data.get("findings", []):
                findings.append({
                    "severity": fg.get("severity", "low").lower(),
                    "title": (fg.get("detail") or fg.get("title") or fg.get("description", ""))[:80],
                    "description": fg.get("detail") or fg.get("description", ""),
                    "auto_fixed": fg.get("auto_fixed", False),
                })
        except (json.JSONDecodeError, Exception):
            pass
    return {
        "findings": findings,
        "open_ports": open_ports,
        "hardcoded_secrets": sum(1 for f in findings if any(kw in (f.get("title","")+f.get("description","")).lower() for kw in ["hardcoded","secret","credential","api_key","passwort"])),
        "bare_excepts": sum(1 for f in findings if any(kw in (f.get("title","")+f.get("description","")).lower() for kw in ["bare except","silent fail","except","timeout","try/finally","finally"])),
        "auto_fix_results": [f["title"][:60] for f in findings if f.get("auto_fixed")],
    }


def _parse_code_quality_prod() -> dict:
    if not os.path.exists(PROD_AUDIT_LOG):
        return {"findings": [], "open_ports": [], "hardcoded_secrets": 0, "bare_excepts": 0, "auto_fix_results": []}
    try:
        with open(PROD_AUDIT_LOG, encoding="utf-8") as f:
            data = json.load(f)
        findings = []
        for fg in data.get("findings", []):
            findings.append({
                "severity": fg.get("severity", "low").lower(),
                "title": (fg.get("detail") or fg.get("title") or fg.get("description", ""))[:80],
                "description": fg.get("detail") or fg.get("description", ""),
                "auto_fixed": fg.get("auto_fixed", False),
            })
        return {
            "findings": findings,
            "open_ports": [],
            "hardcoded_secrets": sum(1 for f in findings if any(kw in (f.get("title","")+f.get("description","")).lower() for kw in ["hardcoded","secret","credential","api_key","passwort"])),
            "bare_excepts": sum(1 for f in findings if any(kw in (f.get("title","")+f.get("description","")).lower() for kw in ["bare except","silent fail","except","timeout","try/finally","finally"])),
            "auto_fix_results": [f["title"][:60] for f in findings if f.get("auto_fixed")] + data.get("auto_fix_results", []),
        }
    except (json.JSONDecodeError, Exception):
        return {"findings": [], "open_ports": [], "hardcoded_secrets": 0, "bare_excepts": 0, "auto_fix_results": []}


# ── Overview ────────────────────────────────────────────────────────────

@router.get("/{location}/overview", response_model=MissioncontrolOverview)
async def get_overview(location: str):
    if location == "production-center":
        path = _latest_report_path(location)
        if not path:
            return MissioncontrolOverview(
                status="pending", last_report=datetime.now(timezone.utc).isoformat(),
                health_score=0, disk_usage={}, crew_status="no_report", active_alerts=[],
            )
        if path.endswith(".json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return _build_overview(data)

    if location != "home-lab":
        return MissioncontrolOverview(
            status="pending", last_report=datetime.now(timezone.utc).isoformat(),
            health_score=0, disk_usage={}, crew_status="not_configured", active_alerts=[],
        )

    path = _latest_report_path(location)
    if not path:
        return MissioncontrolOverview(
            status="unknown", last_report=datetime.now(timezone.utc).isoformat(),
            health_score=0, disk_usage={}, crew_status="no_report", active_alerts=[],
        )

    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return _build_overview(data)

    return MissioncontrolOverview(**_parse_markdown_report(path))


# ── System ──────────────────────────────────────────────────────────────

@router.get("/{location}/system", response_model=MissioncontrolSystem)
async def get_system(location: str):
    if location == "production-center":
        path = _latest_report_path(location)
        if not path:
            return _empty_system()
        if path.endswith(".json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return _build_system_response(data.get("system", data), data.get("overview", {}))
        return MissioncontrolSystem(**_parse_system_from_md(path))

    if location != "home-lab":
        return _empty_system()

    path = _latest_report_path(location)
    if not path:
        return _empty_system()

    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return _build_system_response(data.get("system", data), data.get("overview", {}))

    return MissioncontrolSystem(**_parse_system_from_md(path))


def _empty_system():
    return MissioncontrolSystem(
        host=ProxmoxHost(cpu_percent=0, ram_percent=0, uptime="", kernel_version="", updates_pending=False),
        vms=[], services=[], backups=[],
    )


def _build_system_response(system_data: dict, overview: dict) -> MissioncontrolSystem:
    host_data = system_data.get("host", {})
    vms_data = system_data.get("vms", [])
    svc_data = system_data.get("services", [])
    bkp_data = system_data.get("backups", [])

    host = ProxmoxHost(
        cpu_percent=host_data.get("cpu_percent", 0),
        ram_percent=host_data.get("ram_percent", 0),
        uptime=host_data.get("uptime", ""),
        kernel_version=host_data.get("kernel_version", ""),
        updates_pending=host_data.get("updates_pending", False),
    )

    vms = [
        VmStatus(
            name=v.get("name", ""),
            status=v.get("status", "unknown"),
            cpu_percent=v.get("cpu_percent", 0),
            ram_percent=v.get("ram_percent", 0),
            disk_percent=v.get("disk_percent", 0),
            uptime_days=int(v.get("uptime_days", 0)),
        )
        for v in vms_data
    ]

    services = [
        ServiceStatus(
            name=s.get("name", ""),
            online=s.get("online", True),
            port=s.get("port", 0),
        )
        for s in svc_data
    ]

    backups = [
        BackupStatus(
            vm_name=b.get("vm_name", ""),
            last_backup=b.get("last_backup", ""),
            success=b.get("success", False),
            detail=b.get("detail", ""),
        )
        for b in bkp_data
    ]

    updates_data = system_data.get("updates", [])
    sys_updates = [
        SysUpdate(
            system=u.get("system", ""),
            updates_pending=u.get("updates_pending", 0),
            reboot_needed=u.get("reboot_needed", False),
            kernel=u.get("kernel", ""),
            auto_fixes=u.get("auto_fixes", []),
            details=u.get("details", []),
            warnings=u.get("warnings", []),
        )
        for u in updates_data
    ]

    return MissioncontrolSystem(host=host, vms=vms, services=services, backups=backups, updates=sys_updates)


# ── Code Quality ────────────────────────────────────────────────────────

@router.get("/{location}/code-quality", response_model=MissioncontrolCodeQuality)
async def get_code_quality(location: str):
    if location == "production-center":
        data = _parse_code_quality_prod()
        return MissioncontrolCodeQuality(**data)

    if location != "home-lab":
        return MissioncontrolCodeQuality(
            findings=[], open_ports=[], hardcoded_secrets=0, bare_excepts=0, auto_fix_results=[]
        )

    data = _parse_code_quality()
    return MissioncontrolCodeQuality(**data)


# ── Live ────────────────────────────────────────────────────────────────

@router.get("/{location}/live", response_model=MissioncontrolLive)
async def get_live(location: str):
    import asyncio as _aio

    if location == "production-center":
        targets = [
            ("production-center", "100.126.181.63"),
            ("PBS", "192.168.0.80"),
        ]
    else:
        targets = [
            ("pve-1", "100.119.174.53"),
            ("nextcloud", "100.75.220.89"),
            ("ai-agents", "127.0.0.1"),
            ("ghost-blog", "192.168.0.172"),
            ("image-gen", "100.111.44.63"),
        ]

    async def _ping(name: str, host: str) -> LiveHeartbeat:
        try:
            proc = await _aio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "2", host,
                stdout=_aio.subprocess.DEVNULL,
                stderr=_aio.subprocess.DEVNULL,
            )
            rc = await _aio.wait_for(proc.wait(), timeout=3)
            ok = rc == 0
        except Exception:
            ok = False
        return LiveHeartbeat(system=name, status="ok" if ok else "critical")

    heartbeats = await _aio.gather(*[_ping(n, h) for n, h in targets])

    service_checks = _live_service_checks(location)

    return MissioncontrolLive(
        heartbeats=list(heartbeats),
        service_checks=service_checks,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _live_service_checks(location: str) -> list[LiveServiceCheck]:
    results = _tcp_service_checks(location)

    if location == "home-lab":
        internal = _report_service_status()
        for svc in internal:
            if not any(r.service == svc.service for r in results):
                results.append(svc)

    if location == "production-center":
        # Production-Center-spezifische TCP-Checks
        prod_checks = [
            ("Mission Control", "100.126.181.63", 8503),
            ("SSH (Schaltzentrale)", "100.126.181.63", 22),
        ]
        for name, host, port in prod_checks:
            ok, _ = _tcp_check(host, port)
            if not any(r.service == name for r in results):
                results.append(LiveServiceCheck(service=name, online=ok, port=port, response_time_ms=0))

    return results


def _tcp_service_checks(location: str = "home-lab") -> list[LiveServiceCheck]:
    import asyncio
    import socket
    import time

    checks: list[tuple[str, str, int]] = []
    if location == "production-center":
        checks = [
            ("SSH", "100.126.181.63", 22),
            ("Mission Control", "100.126.181.63", 8503),
        ]
    else:
        checks = [
            ("SSH (pve-1)", "100.119.174.53", 22),
            ("Nextcloud HTTPS", "100.75.220.89", 443),
            ("Proxmox Web", "100.119.174.53", 8006),
            ("Ghost Blog", "192.168.0.172", 2368),
        ]

    results = []
    for name, host, port in checks:
        ok, ms = _tcp_check(host, port)
        results.append(LiveServiceCheck(service=name, online=ok, port=port, response_time_ms=ms))
    return results


def _report_service_status() -> list[LiveServiceCheck]:
    path = _latest_report_path("home-lab")
    if not path or not path.endswith(".json"):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        services = data.get("system", {}).get("services", [])
        return [
            LiveServiceCheck(
                service=s.get("name", ""),
                online=s.get("online", True),
                port=s.get("port", 0),
                response_time_ms=0,
            )
            for s in services
        ]
    except Exception:
        return []


def _tcp_check(host: str, port: int, timeout: float = 2.0) -> tuple[bool, int]:
    import socket
    import time
    try:
        start = time.monotonic()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        elapsed = int((time.monotonic() - start) * 1000)
        s.close()
        return True, elapsed
    except Exception:
        return False, 0


# ── Health ──────────────────────────────────────────────────────────────

@router.get("/{location}/health", response_model=HealthScore)
async def get_health(location: str):
    if location == "production-center":
        path = _latest_report_path(location)
        if not path:
            return HealthScore(
                score=0, level="offline", vm_health=0.0, service_health=0.0,
                audit_health=0.0, calculated_at=datetime.now(timezone.utc).isoformat(),
            )
        if path.endswith(".json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            health = data.get("health", {})
            return HealthScore(
                score=health.get("score", 0),
                level=health.get("level", "offline"),
                vm_health=health.get("vm_health", 0.0),
                service_health=health.get("service_health", 0.0),
                audit_health=health.get("audit_health", 0.0),
                calculated_at=health.get("calculated_at", datetime.now(timezone.utc).isoformat()),
            )
        return HealthScore(
            score=0, level="offline", vm_health=0.0, service_health=0.0,
            audit_health=0.0, calculated_at=datetime.now(timezone.utc).isoformat(),
        )

    if location != "home-lab":
        return HealthScore(
            score=0, level="offline", vm_health=0.0, service_health=0.0,
            audit_health=0.0, calculated_at=datetime.now(timezone.utc).isoformat(),
        )

    path = _latest_report_path(location)
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
        score=score, level=level,
        vm_health=100.0 if "alle systeme online" in text.lower() else 50.0,
        service_health=100.0 if "✅ active" in text else 60.0,
        audit_health=50.0,
        calculated_at=datetime.now(timezone.utc).isoformat(),
    )


def _extract_vm_num(name: str) -> str:
    for vid in ["100", "101", "102", "103", "104"]:
        if re.search(rf"\b{vid}\b", name):
            return vid
    return ""


def _re_search(pattern: str, text: str, flags=0):
    return re.search(pattern, text, flags)


def _re_first(pattern: str, text: str, flags=0) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


# ── Graphiphy: graph.json loader / cache ───────────────────────────────

GRAPHIFY_DIR = os.environ.get("GRAPHIFY_OUT_DIR", os.path.expanduser("~/graphify-out"))


def _graphify_dir(location: str) -> str:
    """Return the graphify-out directory for a given location."""
    if location == "production-center":
        return PROD_GRAPHIFY_DIR
    return GRAPHIFY_DIR


def _graph_path(location: str, filename: str) -> str:
    return os.path.join(_graphify_dir(location), filename)


_graph_caches: dict[str, dict] = {}
_graph_mtimes: dict[str, float] = {}


def _load_graph(location: str = "home-lab") -> dict:
    global _graph_caches, _graph_mtimes
    gpath = _graph_path(location, "graph.json")
    if not os.path.exists(gpath):
        return {"nodes": [], "links": []}
    mtime = os.path.getmtime(gpath)
    if location in _graph_caches and mtime <= _graph_mtimes.get(location, 0):
        return _graph_caches[location]
    with open(gpath, encoding="utf-8") as f:
        _graph_caches[location] = json.load(f)
    _graph_mtimes[location] = mtime
    return _graph_caches[location]


def _build_degree_index(nodes: list[dict], links: list[dict]) -> dict[str, int]:
    deg: dict[str, int] = Counter()
    for n in nodes:
        deg[n["id"]] = 0
    for l in links:
        s = l.get("source", "")
        t = l.get("target", "")
        if isinstance(s, str):
            deg[s] += 1
        if isinstance(t, str):
            deg[t] += 1
    return deg


def _build_community_index(nodes: list[dict]) -> dict[int, list[dict]]:
    idx: dict[int, list[dict]] = {}
    for n in nodes:
        c = n.get("community")
        if c is not None:
            idx.setdefault(c, []).append(n)
    return idx


_stats_caches: dict[str, tuple] = {}
_stats_mtimes: dict[str, float] = {}


def _get_graph_stats(location: str = "home-lab"):
    global _stats_caches, _stats_mtimes
    gpath = _graph_path(location, "graph.json")
    mtime = os.path.getmtime(gpath) if os.path.exists(gpath) else 0
    if location in _stats_caches and mtime <= _stats_mtimes.get(location, 0):
        return _stats_caches[location]
    graph = _load_graph(location)
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    communities = set()
    ftypes: dict[str, int] = Counter()
    for n in nodes:
        ftypes[n.get("file_type", "unknown")] += 1
        c = n.get("community")
        if c is not None:
            communities.add(c)
    deg = _build_degree_index(nodes, links)
    _stats_caches[location] = (
        GraphiphyStats(
            node_count=len(nodes),
            edge_count=len(links),
            community_count=len(communities),
            file_types=dict(ftypes),
        ),
        deg,
        _build_community_index(nodes),
    )
    _stats_mtimes[location] = mtime
    return _stats_caches[location]


# ── Graphiphy Endpoints ─────────────────────────────────────────────────

@router.get("/{location}/graphiphy/stats", response_model=GraphiphyStats)
async def get_graphiphy_stats(location: str):
    stats, _, _ = _get_graph_stats(location)
    return stats


@router.get("/{location}/graphiphy/god-nodes", response_model=list[GraphiphyGodNode])
async def get_graphiphy_god_nodes(location: str, top_n: int = 20):
    _, deg, _ = _get_graph_stats(location)
    if not deg:
        return []
    graph = _load_graph(location)
    node_map = {n["id"]: n for n in graph.get("nodes", [])}
    sorted_deg = sorted(deg.items(), key=lambda x: x[1], reverse=True)[:top_n]
    result = []
    for nid, d in sorted_deg:
        nd = node_map.get(nid, {})
        result.append(GraphiphyGodNode(
            label=nd.get("label", nid),
            degree=d,
            community=nd.get("community", -1),
            file_type=nd.get("file_type", "unknown"),
        ))
    return result


@router.get("/{location}/graphiphy/communities", response_model=list[GraphiphyCommunity])
async def get_graphiphy_communities(location: str, limit: int = 50, offset: int = 0):
    _, _, comm_idx = _get_graph_stats(location)
    if not comm_idx:
        return []
    sized = sorted(comm_idx.items(), key=lambda x: len(x[1]), reverse=True)
    page = sized[offset:offset + limit]
    result = []
    for cid, nodes in page:
        top_labels = [n["label"] for n in nodes[:5]]
        result.append(GraphiphyCommunity(id=cid, size=len(nodes), top_labels=top_labels))
    return result


@router.get("/{location}/graphiphy/community/{community_id}", response_model=list[GraphiphyNode])
async def get_graphiphy_community(location: str, community_id: int):
    _, deg, comm_idx = _get_graph_stats(location)
    nodes = comm_idx.get(community_id, [])
    if not nodes:
        raise HTTPException(status_code=404, detail="Community not found")
    result = []
    for n in nodes:
        result.append(GraphiphyNode(
            label=n.get("label", ""),
            file_type=n.get("file_type", "unknown"),
            community=n.get("community", -1),
            source_file=n.get("source_file", ""),
            degree=deg.get(n.get("id", ""), 0),
            id=n.get("id", ""),
        ))
    return result


@router.get("/{location}/graphiphy/search", response_model=list[GraphiphyNode])
async def search_graphiphy(location: str, q: str = "", limit: int = 20):
    if not q:
        return []
    graph = _load_graph(location)
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    deg = _build_degree_index(nodes, links)
    q_lower = q.lower()
    terms = q_lower.split()
    scored = []
    for n in nodes:
        label = n.get("label", "").lower()
        score = sum(1 for t in terms if t in label)
        if score > 0:
            scored.append((score, n))
    scored.sort(key=lambda x: x[0], reverse=True)
    result = []
    for _, n in scored[:limit]:
        result.append(GraphiphyNode(
            label=n.get("label", ""),
            file_type=n.get("file_type", "unknown"),
            community=n.get("community", -1),
            source_file=n.get("source_file", ""),
            degree=deg.get(n.get("id", ""), 0),
            id=n.get("id", ""),
        ))
    return result


# ── Graphiphy Viz (HTML) ────────────────────────────────────────────────

@router.get("/{location}/graphiphy/viz")
async def get_graphiphy_viz(location: str):
    html_path = _graph_path(location, "graph.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="graph.html not generated yet.")
    with open(html_path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.post("/{location}/graphiphy/viz/refresh")
async def refresh_graphiphy_viz(location: str):
    gdir = _graphify_dir(location)
    gpath = _graph_path(location, "graph.json")
    if not os.path.exists(gpath):
        raise HTTPException(status_code=404, detail="No graph.json found.")
    results = {"html": False, "png": False, "update_ok": False}
    try:
        result = subprocess.run(
            ["graphify", "update", gdir],
            capture_output=True, text=True, timeout=120,
        )
        results["update_ok"] = result.returncode == 0
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["graphify", "cluster-only", gdir],
            capture_output=True, text=True, timeout=120,
        )
        results["html"] = os.path.exists(_graph_path(location, "graph.html"))
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass

    try:
        results["png"] = _generate_graph_png(location)
    except HTTPException:
        pass

    return {"success": any(results.values()), "details": results}


@router.get("/{location}/graphiphy/svg")
async def get_graphiphy_svg(location: str):
    svg_path = _graph_path(location, "graph.svg")
    if not os.path.exists(svg_path):
        raise HTTPException(status_code=404, detail="graph.svg not generated yet.")
    with open(svg_path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), media_type="image/svg+xml")


@router.get("/{location}/graphiphy/png")
async def get_graphiphy_png(location: str):
    png_path = _graph_path(location, "graph.png")
    if not os.path.exists(png_path) or _graph_needs_png_refresh(location):
        _generate_graph_png(location)
    if not os.path.exists(png_path):
        raise HTTPException(status_code=404, detail="graph.png could not be generated.")
    with open(png_path, "rb") as f:
        return Response(content=f.read(), media_type="image/png")


_png_mtimes: dict[str, float] = {}


def _graph_needs_png_refresh(location: str) -> bool:
    global _png_mtimes
    gpath = _graph_path(location, "graph.json")
    if not os.path.exists(gpath):
        return False
    json_mtime = os.path.getmtime(gpath)
    if _png_mtimes.get(location, 0) >= json_mtime:
        return False
    _png_mtimes[location] = json_mtime
    return True


def _generate_graph_png(location: str) -> bool:
    global _png_mtimes
    try:
        import networkx as nx
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Missing dependency for PNG generation: {e}. Run: pip install networkx matplotlib",
        )

    gpath = _graph_path(location, "graph.json")
    png_path = _graph_path(location, "graph.png")
    if not os.path.exists(gpath):
        return False
    with open(gpath, encoding="utf-8") as f:
        d = json.load(f)

    comms = defaultdict(list)
    for n in d.get("nodes", []):
        c = n.get("community")
        if c is not None:
            comms[c].append(n)

    sized = sorted(comms.items(), key=lambda x: len(x[1]), reverse=True)
    top_comms = dict(sized[:120])

    node_to_community = {}
    for cid, members in top_comms.items():
        for n in members:
            node_to_community[n["id"]] = cid

    meta = nx.Graph()
    for cid, members in top_comms.items():
        top_label = members[0]["label"] if members else f"C{cid}"
        meta.add_node(str(cid), label=top_label[:20])

    edge_counts = Counter()
    for l in d.get("links", []):
        s = l.get("source", "")
        t = l.get("target", "")
        cu = node_to_community.get(s)
        cv = node_to_community.get(t)
        if cu is not None and cv is not None and cu != cv:
            edge_counts[(min(cu, cv), max(cu, cv))] += 1

    for (cu, cv), w in edge_counts.items():
        if w >= 5:
            meta.add_edge(str(cu), str(cv), weight=w)

    fig, ax = plt.subplots(figsize=(24, 18), dpi=200, facecolor="#0D1117")
    ax.set_facecolor("#0D1117")
    pos = nx.spring_layout(meta, k=3, iterations=50, seed=42)

    node_sizes = [200 + meta.degree(n) * 30 for n in meta.nodes()]
    colors = [plt.cm.viridis(i / max(1, len(meta.nodes())))
              for i in range(len(meta.nodes()))]

    nx.draw_networkx_nodes(meta, pos, node_size=node_sizes, node_color=colors,
                           alpha=0.85, edgecolors="#ffffff30", linewidths=0.5, ax=ax)
    nx.draw_networkx_edges(meta, pos, alpha=0.15, edge_color="#3498DB",
                           width=0.75, ax=ax)
    nx.draw_networkx_labels(meta, pos,
                            labels={n: meta.nodes[n]["label"] for n in meta.nodes()},
                            font_size=7, font_color="#c0c0c0", ax=ax)
    ax.set_axis_off()
    plt.tight_layout(pad=1)
    plt.savefig(png_path, dpi=200, bbox_inches="tight",
                facecolor="#0D1117", edgecolor="none")
    plt.close()

    _png_mtimes[location] = os.path.getmtime(gpath)
    return True


# ── Reports (raw monitoring reports) ────────────────────────────────────

@router.get("/{location}/reports", response_model=list[ReportListItem])
async def list_reports(location: str, limit: int = 5):
    base = _reports_dir(location)
    if not os.path.isdir(base):
        return []
    all_files = sorted(
        [f for f in os.listdir(base) if f.startswith("report_")],
        reverse=True,
    )
    # Dedup by date, prefer .md
    seen_dates = set()
    files = []
    for f in all_files:
        date_part = f.replace("report_", "").replace(".md", "").replace(".json", "")
        if date_part not in seen_dates:
            seen_dates.add(date_part)
            files.append(f)
    files = files[:limit]
    result = []
    for f in files:
        path = os.path.join(base, f)
        mtime = os.path.getmtime(path)
        date_str = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        result.append(ReportListItem(filename=f, date=date_str, size_bytes=os.path.getsize(path)))
    return result


@router.get("/{location}/reports/{filename}", response_model=ReportDetail)
async def get_report(location: str, filename: str):
    base = _reports_dir(location)
    path = os.path.join(base, filename)
    if not os.path.exists(path) or not path.startswith(base):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    fmt = "json" if filename.endswith(".json") else "markdown"
    mtime = os.path.getmtime(path)
    date_str = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    return ReportDetail(filename=filename, date=date_str, content=content, format=fmt)


# ── Health Trend + Critical Count ───────────────────────────────────────

@router.get("/{location}/health-trend", response_model=list[HealthTrendPoint])
async def get_health_trend(location: str):
    base = _reports_dir(location)
    if not os.path.isdir(base):
        return []
    files = sorted(
        [f for f in os.listdir(base) if f.startswith("report_") and (f.endswith(".md") or f.endswith(".json"))],
        reverse=True,
    )[:14]
    points = []
    for f in files:
        path = os.path.join(base, f)
        if f.endswith(".json"):
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            score = data.get("health", {}).get("score", 0)
        else:
            with open(path, encoding="utf-8") as fh:
                score = _compute_score_from_text(fh.read())
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", f)
        date_str = date_match.group(1) if date_match else f.replace("report_", "").replace(".md", "").replace(".json", "")
        points.append(HealthTrendPoint(date=date_str, score=score))
    return list(reversed(points))


@router.get("/{location}/live/critical-count", response_model=LiveCriticalCount)
async def get_critical_count(location: str):
    live = await get_live(location)
    hb_crit = sum(1 for h in live.heartbeats if h.status == "critical")
    svc_off = sum(1 for s in live.service_checks if not s.online)
    return LiveCriticalCount(heartbeat_critical=hb_crit, services_offline=svc_off, total=hb_crit + svc_off)
