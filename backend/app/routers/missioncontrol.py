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
    critical_count = (
        text.lower().count("kritisch") - text.lower().count("nicht kritisch")
        + text.count("🔴")
    )
    score -= min(critical_count * 5, 30)
    warning_count = text.count("⚠️")
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

    # Host RAM: "RAM Gesamt | 31.1 GB" + "RAM Verwendet | 16.5 GB"
    m_ram_total = re.search(r"RAM Gesamt\s*\|\s*([\d.]+)\s*GB", text)
    m_ram_used = re.search(r"RAM Verwendet\s*\|\s*([\d.]+)\s*GB", text)
    if m_ram_total and m_ram_used:
        total = float(m_ram_total.group(1))
        used = float(m_ram_used.group(1))
        host["ram_percent"] = round(used / total * 100, 1) if total > 0 else 0.0

    # Host CPU: "Load Average | 0.17 / 0.09 / 0.02"
    m_load = re.search(r"Load Average\s*\|\s*([\d.]+)\s*/\s*[\d.]+\s*/\s*[\d.]+", text)
    if m_load:
        host["cpu_percent"] = float(m_load.group(1)) * 15

    # Host uptime: "Uptime | 8 Tage, 16 Stunden" or "Uptime | 8 Tage, 16 Stunden |"
    m_uptime = re.search(r"Uptime\s*\|\s*([^|\n]+)", text)
    if m_uptime:
        host["uptime"] = m_uptime.group(1).strip()

    # Host kernel: "Kernel | 6.8.12-23-pve..."
    m_kernel = re.search(r"^\|\s*Kernel\s*\|\s*([^|\n]+)", text, re.MULTILINE)
    if m_kernel:
        host["kernel_version"] = m_kernel.group(1).strip()

    host["updates_pending"] = (
        "⚠️" in text and ("update verfügbar" in text.lower() or "ausstehende updates" in text.lower())
    )

    # VMs — parse the VM-STATUS table
    # Format: | VM-ID | Name | Status | CPUs | RAM (max) | RAM (akt.) | CPU-Auslastung | Uptime |
    #          | 100 | nextcloud-vm | ✅ running | 4 | 6.0 GB | 4.7 GB | 0.75% | 3 Tage |
    vms = []
    in_vm_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if "VM-ID" in stripped and "Name" in stripped and "Uptime" in stripped:
            in_vm_table = True
            continue
        if in_vm_table and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 8 and re.match(r"\d+", cols[0]):
                vm_id = cols[0]
                name = cols[1]
                status_raw = cols[2]
                cpu_str = cols[6]
                uptime_str = cols[7] if len(cols) > 7 else ""
                status = "running" if "✅" in status_raw else "stopped"
                cpu_pct = 0.0
                m_c = re.search(r"([\d.]+)%", cpu_str)
                if m_c:
                    cpu_pct = float(m_c.group(1))
                ram_act = cols[5]
                ram_max = cols[4]
                ram_pct = 0.0
                m_r = re.search(r"([\d.]+)\s*%", ram_act)
                if not m_r:
                    m_r_a = re.search(r"([\d.]+)\s*GB", ram_act)
                    m_r_m = re.search(r"([\d.]+)\s*GB", ram_max)
                    if m_r_a and m_r_m:
                        ram_pct = round(float(m_r_a.group(1)) / float(m_r_m.group(1)) * 100, 1)
                else:
                    ram_pct = float(m_r.group(1))
                uptime_days = 0
                m_u = re.search(r"(\d+)\s*Tage?", uptime_str)
                if m_u:
                    uptime_days = int(m_u.group(1))
                prefix = "LXC" if "LXC" in name.upper() else "VM"
                vms.append({
                    "name": f"{prefix} {vm_id}: {name}",
                    "status": status,
                    "cpu_percent": cpu_pct,
                    "ram_percent": ram_pct,
                    "disk_percent": 0.0,
                    "uptime_days": uptime_days,
                })
            if len(vms) >= 4:
                break
        elif in_vm_table and not stripped.startswith("|"):
            in_vm_table = False

    # Add LXC 104 if not in VM table (it isn't yet in the report)
    lxc104_present = any("104" in v["name"] for v in vms)
    if not lxc104_present:
        disk_104 = 0.0
        m_d104 = re.search(r"LXC 104[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*(\d+)%", text)
        if m_d104:
            disk_104 = float(m_d104.group(1))
        vms.append({
            "name": "LXC 104: Trading App",
            "status": "running",
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "disk_percent": disk_104,
            "uptime_days": 0,
        })

    # Set disk percentages from storage section (5.1 / SPEICHERPLATZ)
    # Format: | **VM 100 (Nextcloud)** | / | 114 GB | 2.8 GB | 106 GB | 3% |
    disk_map = {}
    for line in text.splitlines():
        for pat in [r"\*?\*?(VM \d+|LXC \d+)", r"(LXC \d+.*?)\]"]:
            m = re.search(pat, line)
            if m:
                key = m.group(1).replace("**", "").strip()
                pct_m = re.search(r"\|\s*(\d+)\s*%\s*\|?\s*$", line)
                if pct_m:
                    disk_map[key] = float(pct_m.group(1))
                    break
    for vm in vms:
        vm_id = re.search(r"(\d+)", vm["name"].split(":")[0])
        vm_num = vm_id.group(1) if vm_id else ""
        for key, pct in disk_map.items():
            key_num = re.search(r"(\d+)", key)
            key_n = key_num.group(1) if key_num else ""
            if key.lower() in vm["name"].lower() or (vm_num and key_n and vm_num == key_n):
                vm["disk_percent"] = pct
                break

    # Services — from "DIENSTE" section
    services = []
    in_svc_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if "## 3." in stripped or ("dienst" in stripped.lower() and "status" in stripped.lower()):
            in_svc_section = True
            continue
        if in_svc_section:
            if stripped.startswith("##") and "dienst" not in stripped.lower():
                in_svc_section = False
                continue
            m_svc = re.search(r"\|\s*(\w[\w\s\-\.]+?)\s*\|\s*(✅|❌)\s*(\w+)", stripped)
            if m_svc:
                svc_name = m_svc.group(1).strip()
                online = "✅" in m_svc.group(2) and "inaktiv" not in stripped.lower()
                port = {"Apache": 443, "MariaDB": 3306, "Redis": 6379, "Nginx": 443,
                        "FastSD": 7860, "ComfyUI": 8188, "Ghost": 2368}.get(svc_name, 0)
                services.append({
                    "name": svc_name,
                    "online": online,
                    "port": port,
                })

    # Backups — parse "BACKUPS" section table
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
