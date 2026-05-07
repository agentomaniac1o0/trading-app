# Trading App – Projektanweisungen

## Projektziel

Cross-Platform Trading App (FastAPI + Flutter) mit Paper Trading und Erweiterungsoption auf Live-Trading.

**Repo:** `~/trading-app/` (öffentlich auf GitHub)
**Deployment:** LXC 104 auf pve-1 (Debian 13, 4 GB RAM, 20 GB Disk)

## Architektur

```
┌─────────────────────────────────────────────────────┐
│  Flutter Frontend (Web + Mobile)                      │
│  Riverpod state · fl_chart · go_router · dio         │
│  Port 8080 (web) / Native (Android/iOS/Desktop)      │
└────────────────────────┬────────────────────────────┘
                         │ HTTP/JSON
┌────────────────────────▼────────────────────────────┐
│  FastAPI Backend                                      │
│  SQLAlchemy async · Alembic · yfinance · ccxt         │
│  Port 8000                                            │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│  SQLite Database (trading.db)                         │
│  trades · settings · assets · predictions             │
└───────────────────────────────────────────────────────┘
```

## Technologie-Stack

| Komponente | Technologie | Version |
|-----------|------------|---------|
| Backend | FastAPI | 0.115+ |
| DB ORM | SQLAlchemy | 2.0+ (async) |
| Migrationen | Alembic | 1.13+ |
| Preise | yfinance + ccxt | latest |
| Frontend | Flutter | 3.24+ |
| State | Riverpod | 2.5+ |
| HTTP | Dio | 5.0+ |
| Charts | fl_chart | 0.69+ |
| Local DB | drift (sqflite) | 2.20+ |

## CI-Farben

| Farbe | Hex | Verwendung |
|-------|-----|-----------|
| Grün/Positiv | `#00b09b` | Gewinne, LONG-Signal, Bullish |
| Rot/Negativ | `#e74c3c` | Verluste, SHORT-Signal, Bearish |
| Gold | `#f0a500` | Highlights, Alerts |
| Blau | `#3498db` | Links, Sekundär |
| Violett | `#9b59b6` | Krypto-Sektor |
| Dunkel | `#0d1117` | Hintergrund |

## Projektstruktur

```
trading-app/
├── AGENTS.md              # Diese Datei
├── CLAUDE.md              # Deutsch (primär)
├── CLAUDE_EN.md           # Englisch
├── README.md
├── .gitignore
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── alembic.ini
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── crud.py
│       ├── routers/
│       │   ├── trades.py
│       │   ├── portfolio.py
│       │   └── prices.py
│       └── services/
│           ├── price_engine.py
│           └── import_trades.py
├── frontend/
│   ├── pubspec.yaml
│   └── lib/
│       ├── main.dart
│       ├── app.dart
│       ├── config/
│       ├── models/
│       ├── services/
│       ├── providers/
│       ├── pages/
│       └── widgets/
└── deploy/
    └── lxc104-setup.sh
```

## Phase 1 – MVP

1. **Projekt-Setup** – FastAPI + Flutter + SQLite + GitHub + LXC 104
2. **Portfolio-Übersicht** – KPIs (Startkapital, Kassenbestand, Portfoliowert, P&L, Win-Rate)
3. **Trade erfassen** – LONG/SHORT, Live-Preis, Asset-Datenbank
4. **Trade schließen** – P&L-Berechnung, Historie
5. **Daten-Migration** – trades.json → SQLite Import

## Phase 2+ (später)

- Report-Viewer (Reports aus trading-crew einbinden)
- Circuit Breaker (automatischer Stop nach X Verlusten)
- Backtesting (historische Strategie-Simulation)
- Live-Trading-Modus (KuCoin API, Read-Only + API-Key)
- Push-Notifications (Mobile Alerts)

## Skill-Trigger

| Skill | Wann aktivieren |
|-------|----------------|
| `trading-app-scaffold` | Neues Projekt aufsetzen, Projektstruktur erstellen, LXC-Deployment |
| `trading-app-feature` | Neues Feature hinzufügen, neue Seite, neuer API-Endpoint, DB-Migration |
| `flutter-app-architecture` | Architektur-Entscheidungen, MVVM-Pattern, Layer-Struktur |
| `riverpod` | State Management, Provider erstellen, Datenfluss in Flutter |
| `effective-dart` | Dart-Code-Stil, Linting, Code-Review |
| `flutter-testing` | Widget-Tests, Integration-Tests, Mocking |
| `grill-me` | Bevor größere Architektur-Entscheidungen getroffen werden |
| `code-cleanup` | Nach jedem Feature-Sprint, vor jedem Commit |

## Entwicklungsprinzipien

- **Paper-First:** Jedes Feature zuerst im Paper-Modus testen
- **API-first:** Backend-Endpoint vor Flutter-UI implementieren
- **Tests mitdenken:** Backend: pytest + TestClient, Frontend: widget_test.dart
- **Security:** API-Keys NIE im Flutter-Code – immer im Backend `~/.env`
- **Offline-First:** Lokale drift-DB als Cache, FastAPI als Remote-Source
- **CI-Konsistenz:** Gleiche Farbwerte wie trading-crew Dashboard
- **Repo-Sprache:** Docs DE+EN, Code-Kommentare EN, Commit-Messages EN

## Was NICHT hier rein gehört

- Mission Control Dashboard → bleibt in `trading-crew/app/`
- CronMaster → bleibt in `agent-templates/`
- Watchdog / Intraday-Alerts → bleibt in `trading-crew/`
- Monitoring → bleibt in `agent-templates/monitoring/`
- Discord-Bot → bleibt in `trading-crew/notifications/`

## Offen

- [ ] GitHub-Repo erstellt und gepusht
- [ ] LXC 104 auf pve-1 eingerichtet (Debian 13, Python 3.13, Flutter, Dart)
- [ ] FastAPI Backend Grundstruktur
- [ ] Flutter Frontend Grundstruktur
- [ ] SQLite Schema + Alembic Migration
- [ ] trades.json → SQLite Import-Migration
- [ ] KuCoin API-Key für Live-Preise (Read-Only)