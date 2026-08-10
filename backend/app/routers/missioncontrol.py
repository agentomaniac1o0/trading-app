import glob
import json
import os
import re
import subprocess
import logging
import time as _time
from collections import Counter, defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response

from app.config import settings
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
    ServiceHistoryPoint,
    ServiceHistoryResponse,
    ServiceHistorySeries,
    ServiceStatus,
    SysUpdate,
    VmStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/missioncontrol", tags=["missioncontrol"])

# ── Home-Lab Pfade ─────────────────────────────────────────────────────
# LXC 104 layout: ~/trading-app/backend/data/monitoring/
# Monitoring-Crew läuft auf VM 101 und rsync'd Reports + audit/quality logs
# täglich nach LXC 104 (siehe agent-templates/monitoring/sync_to_lxc104.sh).
# Override via env (für Tests/Dev auf VM 101 ohne LXC 104): MONITORING_DIR.
_DATA_BASE = os.path.expanduser("~/trading-app/backend/data")
MONITORING_DIR = os.getenv("MONITORING_DIR", os.path.join(_DATA_BASE, "monitoring"))
REPORTS_DIR = os.path.join(MONITORING_DIR, "reports")
AUDIT_LOG = os.path.join(MONITORING_DIR, "security_audit_log.json")
CODE_QUALITY_LOG = os.path.join(MONITORING_DIR, "code_quality_log.json")
SECURITY_FIX_LOG = os.path.join(MONITORING_DIR, "security_fix_log.json")

# ── Production-Center Pfade (via SSH-Pull für health_check.json) ────────
# Reports/audit/graphify werden ebenfalls via rsync von VM 101 nach
# LXC 104 gesynct — liegen unter data/monitoring/production-center/.
PROD_MONITORING_DIR = os.path.join(MONITORING_DIR, "production-center")
PROD_REPORTS_DIR = os.path.join(PROD_MONITORING_DIR, "reports")
PROD_AUDIT_LOG = os.path.join(PROD_MONITORING_DIR, "security_audit_log.json")
PROD_GRAPHIFY_DIR = os.path.join(PROD_MONITORING_DIR, "graphify-out")

# ── Production-Center Health Check (via SSH von VM 100) ────────────────
_PROD_HEALTH_CACHE: dict | None = None
_PROD_HEALTH_CACHE_TS: float = 0
_PROD_HEALTH_TTL = 300  # 5 Minuten


def _fetch_prod_health_json() -> dict | None:
    """Liest health_check.json von VM 100 via SSH (5-Min-Cache)."""
    global _PROD_HEALTH_CACHE, _PROD_HEALTH_CACHE_TS
    now = _time.monotonic()
    if _PROD_HEALTH_CACHE is not None and (now - _PROD_HEALTH_CACHE_TS) < _PROD_HEALTH_TTL:
        return _PROD_HEALTH_CACHE
    try:
        result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
             "-i", os.path.expanduser("~/.ssh/id_ed25519_production"),
             "production-center", "cat ~/monitoring/health_check.json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            _PROD_HEALTH_CACHE = data
            _PROD_HEALTH_CACHE_TS = now
            return data
        logger.debug("prod health SSH failed: rc=%s stderr=%s", result.returncode, result.stderr[:200])
    except Exception as e:
        logger.warning("prod health fetch failed: %s", e)
    return None


def _parse_targets(cfg_str: str) -> list[tuple[str, str]]:
    """Parse 'name:host,name:host' from config."""
    result = []
    for entry in cfg_str.split(","):
        entry = entry.strip()
        if ":" in entry:
            name, host = entry.split(":", 1)
            result.append((name.strip(), host.strip()))
    return result


def _parse_tcp_checks(cfg_str: str) -> list[tuple[str, str, int]]:
    """Parse 'name:host:port,name:host:port' from config."""
    result = []
    for entry in cfg_str.split(","):
        entry = entry.strip()
        parts = entry.split(":")
        if len(parts) >= 3:
            name = parts[0].strip()
            host = parts[1].strip()
            try:
                port = int(parts[2].strip())
                result.append((name, host, port))
            except ValueError:
                logger.warning("Invalid port number in tcp_checks config")
    return result


def _parse_known_services(cfg_str: str) -> list[dict]:
    """Parse 'name:port:host,name:port:host' from config."""
    result = []
    for entry in cfg_str.split(","):
        entry = entry.strip()
        if ":" not in entry:
            continue
        parts = entry.split(":")
        if len(parts) >= 3:
            name = parts[0].strip()
            try:
                port = int(parts[1].strip())
                host = parts[2].strip()
                result.append({"name": name, "online": True, "port": port, "host": host})
            except ValueError:
                logger.warning("Invalid port number in known_services config")
    return result


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
            for f in files:
                if os.path.getsize(f) > 200:
                    return f
    return None


def _extract_report_title(path: str) -> str:
    """Extract title from a report file (first H1 line for .md, date for .json)."""
    try:
        if path.endswith(".json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            date = data.get("report_date", "")
            location = data.get("location", "")
            if location:
                return f"Monitoring Report {location} - {date}"
            return f"Monitoring Report - {date}"
        if path.endswith(".md"):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# ") and not line.startswith("## "):
                        return line.lstrip("# ").strip()
                    if line and not line.startswith("#"):
                        break
    except Exception as e:
        logger.warning("Report title extraction failed: %s", e)
    return ""


def _report_mtime(path: str) -> str:
    return datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).isoformat()


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


def _parse_host_from_text(text: str) -> dict:
    """Extract Proxmox host status from report text (RAM, CPU, uptime, kernel)."""
    host = {
        "cpu_percent": 0.0,
        "ram_percent": 0.0,
        "uptime": "",
        "kernel_version": "",
        "updates_pending": False,
    }

    # Host RAM: new format "RAM (Gesamt/Verfügbar) | 31,1 GB / 17,3 GB verfügbar"
    #            old format "RAM Gesamt | 31,1 GB" + "RAM Verfügbar | 13,3 GB"
    m_ram_combined = re.search(r"RAM\s*\(?.+?\)?\s*\|\s*([\d.,]+)\s*GB\s*/\s*\*?\*?([\d.,]+)\s*GB", text)
    if m_ram_combined:
        total = float(m_ram_combined.group(1).replace(",", "."))
        avail = float(m_ram_combined.group(2).replace(",", "."))
        host["ram_percent"] = round((total - avail) / total * 100, 1) if total > 0 else 0.0
    else:
        m_ram_total = re.search(r"RAM Gesamt\s*\|\s*([\d.,]+)\s*GB", text)
        m_ram_avail = re.search(r"RAM (?:Verfügbar|Verfügbar)\s*\|\s*([\d.,]+)\s*GB", text)
        if m_ram_total and m_ram_avail:
            total = float(m_ram_total.group(1).replace(",", "."))
            avail = float(m_ram_avail.group(1).replace(",", "."))
            host["ram_percent"] = round((total - avail) / total * 100, 1) if total > 0 else 0.0

    # Host CPU
    m_load = re.search(r"\*?\*?Load(?: Average)?\*?\*?\s*\|\s*([\d.,]+)\s*/\s*[\d.,]+\s*/\s*[\d.,]+", text)
    if m_load:
        host["cpu_percent"] = float(m_load.group(1).replace(",", ".")) * 15

    # Host uptime
    m_uptime = re.search(r"\|\s*\*?\*?Uptime\*?\*?\s*\|\s*([^|\n]+)", text)
    if m_uptime:
        host["uptime"] = m_uptime.group(1).strip()

    # Host kernel
    m_kernel = re.search(r"\|\s*\*?\*?Kernel\*?\*?\s*\|\s*(?:Linux\s+)?([^|\n]+)", text)
    if m_kernel:
        host["kernel_version"] = m_kernel.group(1).strip()

    host["updates_pending"] = (
        "⚠️" in text and ("update verfügbar" in text.lower() or "ausstehende updates" in text.lower())
    )
    return host


def _parse_vms_from_text(text: str) -> list[dict]:
    """Parse VM/LXC table from report text, including disk percentage patching."""
    vms = []
    in_vm_table = False
    for line in text.splitlines():
        stripped = line.strip()
        header_lower = stripped.lower()
        if (
            ("vm-id" in header_lower or "vm/container" in header_lower or "vm_id" in header_lower
             or re.search(r'^\|\s*vm\s*\|', stripped, re.IGNORECASE))
            and ("name" in header_lower)
            and ("status" in header_lower)
        ):
            in_vm_table = True
            continue
        if in_vm_table and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) < 4:
                continue
            first_col = cols[0].replace("*", "").replace("_", "").strip()
            if not re.match(r"^\d+$", first_col):
                continue
            vm_id = first_col
            name = cols[1] if len(cols) > 1 else ""
            status_raw = cols[2] if len(cols) > 2 else ""
            status = "running" if ("✅" in status_raw or "✔" in status_raw or "🟢" in status_raw) and "offline" not in status_raw.lower() and "inaktiv" not in status_raw.lower() and "gestoppt" not in status_raw.lower() else "stopped"

            last_col = cols[-1]
            uptime_days = 0
            m_u = re.search(r"(\d+)\s*Tage?", last_col)
            if m_u:
                uptime_days = int(m_u.group(1))

            cpu_pct = 0.0
            ram_pct = 0.0
            for c in cols:
                c_clean = c.replace(",", ".").replace(" ", "")
                m_cpu = re.search(r"([\d.]+)%", c_clean)
                if m_cpu:
                    val = float(m_cpu.group(1))
                    if cpu_pct == 0.0:
                        cpu_pct = val
                    else:
                        ram_pct = val
            ram_pct = 0.0
            if len(cols) >= 6:
                ram_alloc_str = cols[4].replace(",", ".").replace("GB", "").replace(" ", "")
                ram_used_str = cols[5].replace(",", ".").replace("GB", "").replace(" ", "")
                try:
                    ram_alloc_f = float(ram_alloc_str)
                    ram_used_f = float(ram_used_str)
                    ram_pct = round(ram_used_f / ram_alloc_f * 100, 1)
                except (ValueError, ZeroDivisionError):
                    logger.debug("RAM percentage parse failed")
            if ram_pct == 0.0:
                for c in cols[4:]:
                    c_clean = c.replace(",", ".").replace(" ", "").rstrip("%")
                    m = re.search(r"([\d.]+)%", c_clean)
                    if m:
                        ram_pct = float(m.group(1))
                        break

            is_lxc = int(vm_id) >= 102
            prefix = "LXC" if is_lxc else "VM"
            vm_name = f"{prefix} {vm_id}: {name}"

            vms.append({
                "name": vm_name,
                "status": status,
                "cpu_percent": cpu_pct,
                "ram_percent": ram_pct,
                "disk_percent": 0.0,
                "uptime_days": uptime_days,
            })
        elif in_vm_table and not stripped.startswith("|") and stripped and not stripped.startswith("*"):
            in_vm_table = False

    # Patch disk percentages from storage section
    disk_map = _parse_disk_map_from_text(text)
    for vm in vms:
        vm_id = re.search(r"(\d+)", vm["name"].split(":")[0])
        vm_num = vm_id.group(1) if vm_id else ""
        for key, pct in disk_map.items():
            key_num = re.search(r"(\d+)", key)
            key_n = key_num.group(1) if key_num else ""
            if key.lower() in vm["name"].lower() or (vm_num and key_n and vm_num == key_n):
                vm["disk_percent"] = pct
                break
    return vms


def _parse_disk_map_from_text(text: str) -> dict[str, float]:
    """Extract disk percentage map from storage section."""
    disk_map = {}
    current_key = None
    for line in text.splitlines():
        for pat in [r"\*?\*?(VM \d+|LXC \d+)", r"(LXC \d+.*?)\]"]:
            m = re.search(pat, line)
            if m:
                current_key = m.group(1).replace("**", "").strip()
                break
        pct_m = re.search(r"\|\s*\*?\*?(\d+)\s*%\*?\*?\s*\|", line)
        if pct_m and current_key:
            pct = float(pct_m.group(1))
            mnt = re.search(r"\|\s*/\s*\|", line)
            if mnt and current_key not in disk_map:
                disk_map[current_key] = pct
            elif current_key not in disk_map:
                disk_map[current_key] = pct
    return disk_map


def _parse_services_from_text(text: str) -> list[dict]:
    """Extract services from 'DIENSTE' section of report."""
    services = []
    in_svc_section = False
    svc_host = "pve-1"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("##") and ("## 3." in stripped or ("dienst" in stripped.lower() and "status" in stripped.lower())):
            in_svc_section = True
            host_m = re.search(r'\((VM \d+|LXC \d+|pve-\d+).*?[–\-]\s*(.+?)\)', stripped)
            if host_m:
                svc_host = f"{host_m.group(1)} – {host_m.group(2).strip()}"
            elif re.search(r'\((VM \d+|LXC \d+|pve-\d+)\)', stripped):
                svc_host = re.search(r'\((VM \d+|LXC \d+|pve-\d+)\)', stripped).group(1)
            continue
        if in_svc_section:
            if stripped.startswith("##") and "dienst" not in stripped.lower():
                in_svc_section = False
                continue
            cols = stripped.split("|")[1:-1]
            if len(cols) >= 2:
                svc_name = cols[0].strip().lstrip("*").strip()
                status_raw = cols[1].strip()
                if svc_name in ("Dienst", "Priorität", "---", "") or "---" in svc_name:
                    continue
                if svc_name and any(c.isalpha() for c in svc_name) and len(svc_name) > 2:
                    online = ("✅" in status_raw or "🟢" in status_raw) and "inaktiv" not in status_raw.lower()
                    if not online and len(cols) >= 3:
                        version = cols[2].strip()
                        if version and version != "–" and not version.lower().startswith("n/a"):
                            online = True
                    port = {"Apache": 443, "MariaDB": 3306, "Redis": 6379, "Nginx": 443,
                            "FastSD": 7860, "ComfyUI": 8188, "Ghost": 2368,
                            "Uvicorn": 8000, "Flatpak-Repo": 8081, "Mission Control": 8502,
                            "Trading Dashboard": 8501, "MCP-Server": 3000,
                            "Tailscale": 0, "CrewAI": 0}.get(svc_name, 0)
                    if not any(s["name"] == svc_name for s in services):
                        services.append({
                            "name": svc_name,
                            "online": online,
                            "port": port,
                            "host": svc_host,
                        })

    for svc_entry in _parse_known_services(settings.known_services_str):
        if not any(s["name"] == svc_entry["name"] for s in services):
            services.append(svc_entry)
    return services


def _parse_backups_from_text(text: str) -> list[dict]:
    """Extract backup status from BACKUPS section."""
    backups = []
    in_bkp_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if "## 7." in stripped or ("backup" in stripped.lower() and "letztes" in stripped.lower()):
            in_bkp_section = True
            continue
        if in_bkp_section:
            if stripped.startswith("##") and "backup" not in stripped.lower() and "## 8" not in stripped:
                in_bkp_section = False
                continue
            bkp_cols = [c.strip() for c in stripped.split("|")[1:-1] if c.strip()]
            if len(bkp_cols) >= 4 and re.match(r"VM \d+|LXC \d+", bkp_cols[0]):
                vm_name = bkp_cols[0]
                date_str = bkp_cols[1] if len(bkp_cols) > 1 else ""
                status_str = bkp_cols[3] if len(bkp_cols) > 3 else ""
                try:
                    dt = datetime.strptime(date_str, "%d.%m.%Y")
                    backups.append({
                        "vm_name": vm_name,
                        "last_backup": dt.isoformat(),
                        "success": "✅" in status_str and "⚠️" not in status_str,
                    })
                except (ValueError, IndexError):
                    logger.debug("Backup date parse failed")
    return backups


def _parse_updates_enriched_from_text(text: str) -> tuple[list[dict], dict[str, str], dict[str, list], dict[str, list]]:
    """Extract updates table, kernel map, fix/warn maps from report."""
    updates = []
    in_upd_section = False
    for line in text.splitlines():
        stripped = line.strip()
        low = stripped.lower()
        if "ausstehende updates" in low and "reboot" in low:
            in_upd_section = True
            continue
        if in_upd_section:
            if not stripped.startswith("|"):
                in_upd_section = False
                continue
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 3 and any(c.isalpha() for c in cols[0]) and "system" not in low and "----" not in stripped:
                updates.append({
                    "system": cols[0],
                    "updates_pending": 0 if "keine" in cols[1].lower() else 1,
                    "reboot_needed": "ja" in cols[2].lower() or "⚠" in cols[2],
                    "kernel": "",
                    "auto_fixes": [],
                })

    kernel_map = _parse_kernel_map_from_text(text)
    fix_map, warn_map = _parse_fixes_from_text(text)

    for u in updates:
        vid = _extract_vm_num(u["system"])
        u["kernel"] = kernel_map.get(vid, "")
        u["auto_fixes"] = fix_map.get(vid, [])
        u["warnings"] = warn_map.get(vid, [])
        u["details"] = fix_map.get(vid, []) + warn_map.get(vid, [])
    return updates, kernel_map, fix_map, warn_map


def _parse_kernel_map_from_text(text: str) -> dict[str, str]:
    """Extract kernel version map from section 6b."""
    kernel_map = {}
    in_kern_section = False
    for line in text.splitlines():
        s = line.strip()
        if "6b." in s.lower() or "kernel-version" in s.lower():
            in_kern_section = True
            continue
        if in_kern_section and s.startswith("## ") and "kernel" not in s.lower():
            in_kern_section = False
        if in_kern_section and s.startswith("|"):
            cols = [c.strip() for c in s.split("|")[1:-1]]
            if len(cols) >= 3 and re.match(r"VM \d+|LXC \d+", cols[0], re.IGNORECASE):
                vid = _extract_vm_num(cols[0])
                if cols[1] == "?" or cols[2] == "?":
                    k_info = cols[1] if cols[1] != "?" else cols[2]
                elif cols[1] != cols[2]:
                    k_info = f"{cols[1]} → {cols[2]}"
                else:
                    k_info = cols[1]
                kernel_map[vid] = k_info
    return kernel_map


def _parse_fixes_from_text(text: str) -> tuple[dict[str, list], dict[str, list]]:
    """Extract auto-fix and warning maps from report."""
    fix_map: dict[str, list] = {}
    warn_map: dict[str, list] = {}
    in_fix = False
    for line in text.splitlines():
        s = line.strip()
        if "fixes (automatisch)" in s.lower() or "durchgeführte fixes" in s.lower():
            in_fix = True
            continue
        if in_fix and (s.startswith("##") or s.startswith("###") or "verbleibende" in s.lower()):
            in_fix = False
        if in_fix and "✅" in s:
            detail = re.sub(r"^[-✅\s]+", "", s).strip()
            vid = _extract_vm_num(detail) or "101"
            fix_map.setdefault(vid, []).append(detail)
    in_warn = False
    for line in text.splitlines():
        s = line.strip()
        if "verbleibende warnungen" in s.lower():
            in_warn = True
            continue
        if in_warn and s.startswith("##"):
            in_warn = False
        if in_warn and "⚠️" in s:
            detail = re.sub(r"^[-⚠️\s]+", "", s).strip()
            vid = _extract_vm_num(detail)
            warn_map.setdefault(vid, []).append(detail)
    return fix_map, warn_map


def _parse_system_from_md(path: str) -> dict:
    """Parse full system status from monitoring markdown report."""
    with open(path, encoding="utf-8") as f:
        text = f.read()

    host = _parse_host_from_text(text)
    vms = _parse_vms_from_text(text)
    services = _parse_services_from_text(text)
    backups = _parse_backups_from_text(text)
    updates, _kernel_map, _fix_map, _warn_map = _parse_updates_enriched_from_text(text)

    return {
        "host": host,
        "vms": vms,
        "services": services,
        "backups": backups,
        "updates": updates,
    }


def _parse_code_quality() -> dict:
    findings: list[dict] = []
    open_ports: list[dict] = []
    hardcoded_secrets = 0
    bare_excepts = 0
    auto_fix_results: list[str] = []
    last_report = ""

    # report_time aus dem neuesten Report-JSON holen
    latest = _latest_report_path("home-lab")
    if latest and latest.endswith(".json"):
        try:
            with open(latest, encoding="utf-8") as f:
                top = json.load(f)
            rd = top.get("report_date", "")
            rt = top.get("report_time", "00:00")
            if rd:
                last_report = f"{rd}T{rt}:00"
        except Exception as e:
            logger.warning("Code quality report time parse failed: %s", e)

    # ── 1. security_audit_log.json (letzter Eintrag) ────────────────────
    audit_timestamp = ""
    if os.path.exists(AUDIT_LOG):
        with open(AUDIT_LOG, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Audit log JSON parse failed: %s", e)
                data = []

            if isinstance(data, list):
                data = data[-1] if data else {}

            audit_timestamp = data.get("timestamp", "")
            for finding in data.get("findings", []):
                ft = finding.get("type", "")
                if ft == "hardcoded_secret":
                    hardcoded_secrets += 1
                elif ft == "bare_except":
                    bare_excepts += 1
                elif "port" in (ft or "") or "interface" in (ft or ""):
                    open_ports.append(
                        {
                            "port": finding.get("port", 0),
                            "service": finding.get("process", finding.get("detail", "")),
                            "expected": finding.get("expected", False),
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

    # ── 2. code_quality_log.json (Subagent-Findings) ────────────────────
    if os.path.exists(CODE_QUALITY_LOG):
        with open(CODE_QUALITY_LOG, encoding="utf-8") as f:
            try:
                cq_entries = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Code quality log JSON parse failed: %s", e)
                cq_entries = []

            for entry in cq_entries:
                svc = entry.get("service", "")
                ts = entry.get("timestamp", "")
                summary = entry.get("summary", "")
                files = entry.get("files", [])
                # Skip test entries and entries older than 30 days
                if "Test-Eintrag" in summary:
                    continue
                if entry.get("fixed", False):
                    continue
                if ts:
                    try:
                        entry_date = datetime.fromisoformat(ts)
                        if (datetime.now() - entry_date).days > 30:
                            continue
                    except (ValueError, TypeError):
                        pass
                # Skip entries with no findings (all issues resolved)
                if entry.get("critical", 0) == 0 and entry.get("high", 0) == 0 and entry.get("medium", 0) == 0 and entry.get("low", 0) == 0:
                    continue
                severity = "high" if entry.get("critical", 0) > 0 or entry.get("high", 0) > 0 else "medium"
                findings.append(
                    {
                        "severity": severity,
                        "title": f"[{svc}] {ts[:10]} – {summary[:100]}",
                        "description": f"Dateien: {', '.join(files[:5])} | Critical={entry.get('critical',0)} High={entry.get('high',0)} Medium={entry.get('medium',0)}",
                        "auto_fixed": False,
                    }
                )

    # ── 3. security_fix_log.json (Auto-Fix-Ergebnisse) ──────────────────
    if os.path.exists(SECURITY_FIX_LOG):
        with open(SECURITY_FIX_LOG, encoding="utf-8") as f:
            try:
                fix_entries = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Security fix log JSON parse failed: %s", e)
                fix_entries = []

            # Nur die letzten 10 Fixes als findings anzeigen
            for entry in fix_entries[-10:]:
                action = entry.get("action", "")
                # Skip duplicate "verify=False ist intern" messages
                if "verify=False ist intern" in action:
                    if not auto_fix_results:
                        auto_fix_results.append(
                            "SSL verify=False in Überwachungs-Scripts → intern, kein Fix nötig"
                        )
                    continue
                ts = entry.get("timestamp", "")
                auto_fix_results.append(f"[{ts[:10]}] {action[:120]}")
                findings.append(
                    {
                        "severity": "low",
                        "title": f"[Auto-Fix] {entry.get('file', '')}",
                        "description": action[:200],
                        "auto_fixed": True,
                    }
                )

    # Fallback last_report auf audit timestamp wenn kein Report vorhanden
    if not last_report and audit_timestamp:
        last_report = audit_timestamp

    return {
        "findings": findings,
        "open_ports": open_ports,
        "hardcoded_secrets": hardcoded_secrets,
        "bare_excepts": bare_excepts,
        "auto_fix_results": auto_fix_results,
        "last_report": last_report,
    }


def _parse_code_quality_prod() -> dict:
    findings: list[dict] = []
    open_ports: list[dict] = []
    hardcoded_secrets = 0
    bare_excepts = 0
    auto_fix_results: list[str] = []
    last_report = ""

    if not os.path.exists(PROD_AUDIT_LOG):
        return {
            "findings": [], "open_ports": [], "hardcoded_secrets": 0,
            "bare_excepts": 0, "auto_fix_results": [], "last_report": "",
        }

    with open(PROD_AUDIT_LOG, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Prod audit log JSON parse failed: %s", e)
            return {
                "findings": [], "open_ports": [], "hardcoded_secrets": 0,
                "bare_excepts": 0, "auto_fix_results": [], "last_report": "",
            }

    if isinstance(data, list):
        data = data[-1] if data else {}

    last_report = data.get("timestamp", "")

    for fg in data.get("findings", []):
        sev = str(fg.get("severity", "low")).lower()
        detail = fg.get("detail") or fg.get("title") or fg.get("description", "")
        system = ""
        # Extract system name from detail (e.g. "Proxmox Host:", "Schaltzentrale (VM 100):")
        if ": " in detail:
            system = detail.split(": ")[0].strip()

        # Classify finding types for metrics
        dl = detail.lower()
        if any(kw in dl for kw in ["hardcoded", "secret", "credential", "api_key", "passwort"]):
            hardcoded_secrets += 1
        if any(kw in dl for kw in ["bare except", "silent fail", "except: pass"]):
            bare_excepts += 1
        # Only findings from _check_open_ports
        is_port_finding = re.search(r"Port\s*\d+.*bekannter", detail) or re.search(r"Unerwarteter.*Port", detail)
        if is_port_finding:
            port_num = 0
            port_match = re.search(r"(?:Port|port)[:\s]*(\d+)", detail)
            if port_match:
                port_num = int(port_match[1])
            open_ports.append({
                "port": port_num,
                "service": system or detail[:60],
                "expected": fg.get("expected", False),
            })

        findings.append({
            "severity": sev,
            "title": f"{system}: {detail}" if system else detail[:100],
            "description": fg.get("fix") or fg.get("detail", ""),
            "auto_fixed": fg.get("auto_fixed", False),
        })

    for fix in data.get("auto_fix_results", []):
        auto_fix_results.append(str(fix)[:120])

    return {
        "findings": findings,
        "open_ports": open_ports,
        "hardcoded_secrets": hardcoded_secrets,
        "bare_excepts": bare_excepts,
        "auto_fix_results": auto_fix_results,
        "last_report": last_report,
    }


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
            return _build_system_response(data.get("system", data), data.get("overview", {}), top=data)
        parsed = _parse_system_from_md(path)
        return MissioncontrolSystem(**parsed, last_report=_report_mtime(path))

    if location != "home-lab":
        return _empty_system()

    path = _latest_report_path(location)
    if not path:
        return _empty_system()

    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return _build_system_response(data.get("system", data), data.get("overview", {}), top=data)

    parsed = _parse_system_from_md(path)
    return MissioncontrolSystem(**parsed, last_report=_report_mtime(path))


def _empty_system():
    return MissioncontrolSystem(
        host=ProxmoxHost(cpu_percent=0, ram_percent=0, uptime="", kernel_version="", updates_pending=False),
        vms=[], services=[], backups=[],
        last_report="",
    )


def _build_system_response(system_data: dict, overview: dict, top: dict | None = None) -> MissioncontrolSystem:
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
            host=s.get("host", "pve-1"),
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

    report_dt = overview.get("last_report", "")
    if not report_dt:
        rd = overview.get("report_date", "") or (top or {}).get("report_date", "")
        rt = overview.get("report_time", "00:00") or (top or {}).get("report_time", "00:00")
        report_dt = f"{rd}T{rt}:00" if rd else ""
    return MissioncontrolSystem(host=host, vms=vms, services=services, backups=backups, updates=sys_updates, last_report=report_dt)


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
        health = _fetch_prod_health_json()
        if health:
            heartbeats = [
                LiveHeartbeat(system=h.get("system", ""), status=h.get("status", "critical"))
                for h in health.get("heartbeats", [])
            ]
            service_checks = [
                LiveServiceCheck(
                    service=s.get("service", ""),
                    online=s.get("online", False),
                    response_time_ms=s.get("response_time_ms", 0),
                )
                for s in health.get("service_checks", [])
            ]
            return MissioncontrolLive(
                heartbeats=heartbeats,
                service_checks=service_checks,
                timestamp=health.get("timestamp", datetime.now(timezone.utc).isoformat()),
            )
        # Fallback: eigene Checks wenn health_check.json nicht verfügbar
        targets = _parse_targets(settings.live_targets_prod)
    else:
        targets = _parse_targets(settings.live_targets_home)

    async def _ping(name: str, host: str) -> LiveHeartbeat:
        try:
            proc = await _aio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "2", host,
                stdout=_aio.subprocess.DEVNULL,
                stderr=_aio.subprocess.DEVNULL,
            )
            rc = await _aio.wait_for(proc.wait(), timeout=3)
            ok = rc == 0
        except Exception as e:
            logger.debug("Ping %s (%s) failed: %s", name, host, e)
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
            # Check if this service is already covered by a TCP check
            # (substring match to handle naming differences like "SSH" vs "SSH (ai-agents)")
            already_covered = any(
                r.service == svc.service
                or r.service.lower().startswith(svc.service.lower() + " ")
                or svc.service.lower().startswith(r.service.lower() + " ")
                or svc.service.lower() in r.service.lower()
                or r.service.lower() in svc.service.lower()
                for r in results
            )
            if not already_covered:
                results.append(svc)

    if location == "production-center":
        prod_checks = _parse_tcp_checks(settings.live_tcp_prod)
        for name, host, port in prod_checks:
            ok, _ = _tcp_check(host, port)
            if not any(r.service == name for r in results):
                results.append(LiveServiceCheck(service=name, online=ok, port=port, response_time_ms=0))

    return results


def _tcp_service_checks(location: str = "home-lab") -> list[LiveServiceCheck]:
    import asyncio
    import socket
    import time

    if location == "production-center":
        checks = _parse_tcp_checks(settings.live_tcp_prod)
    else:
        checks = _parse_tcp_checks(settings.live_tcp_home)

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
                response_time_ms=-1,  # -1 = systemd-check, kein TCP
            )
            for s in services
        ]
    except Exception as e:
        logger.warning("Report service status parse failed: %s", e)
        return []


def _tcp_check(host: str, port: int, timeout: float = 2.0) -> tuple[bool, int]:
    import socket
    import time
    try:
        start = time.monotonic()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        elapsed = max(1, round((time.monotonic() - start) * 1000))
        s.close()
        return True, elapsed
    except Exception as e:
        logger.debug("TCP check %s:%s failed: %s", host, port, e)
        return False, 0


# ── Service History ─────────────────────────────────────────────────────
# In-memory store: {location: {service_name: [(ts, ms, online), ...]}}
# Collected every 5 minutes by background task, keeps last 288 points (24h)
_service_history: dict[str, dict[str, list[dict]]] = {}
_HISTORY_MAX_POINTS = 288  # 24h at 5min intervals


def _collect_service_history():
    """Run TCP checks for all configured services and store results."""
    now = datetime.now(timezone.utc).isoformat()

    for location, tcp_key in [("home-lab", "live_tcp_home"), ("production-center", "live_tcp_prod")]:
        tcp_str = getattr(settings, tcp_key, "")
        checks = _parse_tcp_checks(tcp_str)

        if location not in _service_history:
            _service_history[location] = {}

        for name, host, port in checks:
            ok, ms = _tcp_check(host, port)
            if name not in _service_history[location]:
                _service_history[location][name] = []
            entry = {
                "timestamp": now,
                "response_time_ms": ms,
                "online": ok,
            }
            _service_history[location][name].append(entry)
            # Trim to max points
            if len(_service_history[location][name]) > _HISTORY_MAX_POINTS:
                _service_history[location][name] = _service_history[location][name][-_HISTORY_MAX_POINTS:]


@router.get("/{location}/services/history", response_model=ServiceHistoryResponse)
async def get_service_history(location: str):
    if location not in ("home-lab", "production-center"):
        raise HTTPException(status_code=404, detail=f"Unknown location: {location}")

    loc_data = _service_history.get(location, {})

    # Build port map from config for the location
    tcp_key = "live_tcp_home" if location == "home-lab" else "live_tcp_prod"
    tcp_str = getattr(settings, tcp_key, "")
    port_map = {name: port for name, _host, port in _parse_tcp_checks(tcp_str)}

    services = []
    for name, history in sorted(loc_data.items()):
        services.append(ServiceHistorySeries(
            name=name,
            host="",
            port=port_map.get(name, 0),
            history=[
                ServiceHistoryPoint(
                    timestamp=h["timestamp"],
                    response_time_ms=h["response_time_ms"],
                    online=h["online"],
                )
                for h in history
            ],
        ))

    return ServiceHistoryResponse(
        services=services,
        collected_at=datetime.now(timezone.utc).isoformat(),
    )


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
    except subprocess.TimeoutExpired as e:
        logger.warning("graphify update timed out: %s", e)
    except FileNotFoundError:
        logger.warning("graphify CLI not found for update")

    try:
        result = subprocess.run(
            ["graphify", "cluster-only", gdir],
            capture_output=True, text=True, timeout=120,
        )
        results["html"] = os.path.exists(_graph_path(location, "graph.html"))
    except subprocess.TimeoutExpired as e:
        logger.warning("graphify cluster-only timed out: %s", e)
    except FileNotFoundError:
        logger.warning("graphify CLI not found for cluster")

    try:
        results["png"] = _generate_graph_png(location)
    except HTTPException as e:
        logger.warning("Graph PNG generation failed: %s", e.detail)

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
        title = _extract_report_title(path)
        result.append(ReportListItem(
            filename=f, date=date_str, size_bytes=os.path.getsize(path), title=title,
        ))
    return result


@router.get("/{location}/reports/{filename}", response_model=ReportDetail)
async def get_report(location: str, filename: str):
    base = _reports_dir(location)
    path = os.path.realpath(os.path.join(base, filename))
    if not path.startswith(os.path.realpath(base) + os.sep) or not os.path.exists(path):
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


# ── Trading Reports (from trading-crew) ────────────────────────────────────

TRADING_REPORTS_DIR = os.path.expanduser("~/trading-crew/data/reports")


@router.get("/{location}/trading-reports", response_model=list[ReportListItem])
async def list_trading_reports(location: str, limit: int = 5):
    """List trading reports from trading-crew/data/reports/"""
    if not os.path.isdir(TRADING_REPORTS_DIR):
        return []
    
    all_files = []
    for f in os.listdir(TRADING_REPORTS_DIR):
        if f.startswith("report_") and (f.endswith(".json") or f.endswith(".txt")):
            all_files.append(f)
    
    # Sort by modification time (newest first)
    all_files.sort(key=lambda f: os.path.getmtime(os.path.join(TRADING_REPORTS_DIR, f)), reverse=True)
    
    # Take first 'limit' files
    files = all_files[:limit]
    result = []
    
    for f in files:
        path = os.path.join(TRADING_REPORTS_DIR, f)
        try:
            mtime = os.path.getmtime(path)
            date_str = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            
            # Try to extract title from JSON content or use filename
            title = f.replace("report_", "").replace(".json", "").replace(".txt", "")
            if f.endswith(".json"):
                try:
                    with open(path, encoding="utf-8") as fh:
                        data = json.load(fh)
                        if "date" in data:
                            title = f"Trading Report - {data['date']}"
                        else:
                            title = "Trading Report"
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning("Trading report JSON parse failed: %s", e)
            elif f.endswith(".txt"):
                title = "Market Analysis"
            
            result.append(ReportListItem(
                filename=f, 
                date=date_str, 
                size_bytes=os.path.getsize(path),
                title=title
            ))
        except Exception as e:
            logger.warning("Skipping unreadable report file %s: %s", f, e)
            continue
    
    return result


@router.get("/{location}/trading-reports/{filename}", response_model=ReportDetail)
async def get_trading_report(location: str, filename: str):
    """Get a specific trading report content"""
    path = os.path.realpath(os.path.join(TRADING_REPORTS_DIR, filename))
    
    # Security check: ensure resolved path is within reports directory
    if not path.startswith(os.path.realpath(TRADING_REPORTS_DIR) + os.sep) or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Trading report not found")
    
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to read report")
    
    # Determine format
    fmt = "json" if filename.endswith(".json") else "html" if filename.endswith(".txt") else "text"
    
    mtime = os.path.getmtime(path)
    date_str = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    
    return ReportDetail(filename=filename, date=date_str, content=content, format=fmt)
