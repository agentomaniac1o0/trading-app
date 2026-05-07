# Trading App – Roadmap

**Repo:** `~/trading-app/` (öffentlich auf GitHub)
**Plattformen:** CachyOS (Linux Desktop) + Android (Mobile)
**Deployment:** LXC 104 auf pve-1 (Debian 13)

## Plattform-Ziele

| Plattform | Ziel | Status |
|-----------|------|--------|
| CachyOS (Linux) | Flutter Desktop (native) + Web (localhost:8080) | Scaffolded |
| Android | Flutter Mobile APK | Scaffolded |
| Web | Flutter Web Build (nginx/8080 auf LXC 104) | Scaffolded |

Flutter kompiliert aus einer Codebasis für alle drei Targets (`flutter run -d linux`, `flutter build apk`, `flutter build web`). Die Unterscheidung erfolgt ausschließlich über den Build-Target, nicht im Code.

---

## Phase 1 – MVP (aktuell)

### Erledigt

- [x] Projekt-Repo initialisiert (`~/trading-app/`, git main branch)
- [x] FastAPI Backend komplett aufgesetzt
  - [x] `config.py` – Pydantic-Settings aus `.env`
  - [x] `database.py` – SQLAlchemy async engine + session
  - [x] `models.py` – Trade + Setting ORM-Modelle
  - [x] `schemas.py` – Pydantic request/response schemas
  - [x] `crud.py` – Alle CRUD-Operationen (create, list, close, portfolio stats)
  - [x] `routers/trades.py` – GET/POST/PATCH Trade-Endpoints
  - [x] `routers/portfolio.py` – GET Portfolio Summary
  - [x] `routers/prices.py` – GET Live-Preise
  - [x] `services/price_engine.py` – yfinance + ccxt/KuCoin mit Cache
  - [x] `services/import_trades.py` – trades.json → SQLite Migration
  - [x] `main.py` – FastAPI-App mit CORS + Health-Endpoint
  - [x] Alembic-Config + initiale Migration 001
  - [x] pytest-asyncio Tests (5 Tests)
  - [x] `deploy/lxc104-setup.sh` – LXC 104 Provisioning-Script
- [x] Flutter Frontend komplett aufgesetzt
  - [x] Dark-Finance-Theme (CI-Farben: `#00b09b`, `#e74c3c`, `#f0a500`, `#0d1117`)
  - [x] 4 Pages: Portfolio, Trade öffnen, Trade schließen, Settings
  - [x] 4 Widgets: KpiCard, TradeCard, AmpelIndicator, PriceChart
  - [x] 3 Provider: trades, portfolio, prices (Riverpod)
  - [x] 3 Models: Trade, PortfolioSummary, Price
  - [x] 2 Services: ApiClient (Dio), PriceService (mit Cache)
  - [x] go_router + NavigationBar (4 Tabs)
  - [x] `pubspec.yaml` mit allen Dependencies
  - [x] `web/index.html` für Flutter Web
- [x] `data/trades.json` – Leeres Template (initial_capital: 10000)
- [x] `.gitignore` – Python, Flutter, IDE, Daten-Dateien
- [x] `AGENTS.md` – Skill-Trigger, Architektur, Konventionen

### Noch offen (Phase 1)

- [ ] **GitHub-Repo** erstellen und pushen
- [ ] **LXC 104** auf pve-1 einrichten (Debian 13, Python 3.13, Flutter, Dart)
- [ ] **Backend starten und testen** (`uvicorn app.main:app`)
- [ ] **Flutter-Build testen** (`flutter build web`, `flutter run -d linux`, `flutter build apk`)
- [ ] **CachyOS Desktop-Build** sicherstellen (Flutter Linux embedding)
- [ ] **Android APK-Build** sicherstellen (Flutter Android embedding)
- [ ] **trades.json** von `trading-crew/data/trades.json` kopieren + ersten Import-Run
- [ ] **KuCoin API-Key** für Live-Preise (Read-Only)
- [ ] **End-to-End Test**: Trade öffnen → Preis holen → Trade schließen
- [ ] **Portfolio-KPIs** verifizieren (echtes trades.json importieren)

---

## Phase 2 – Erweiterungen (später)

- [ ] **Report-Viewer** – Reports aus trading-crew im Frontend anzeigen
- [ ] **Circuit Breaker** – Automatischer Stop nach X Verlusten hintereinander
- [ ] **Backtesting** – Historische Strategie-Simulation
- [ ] **Live-Trading-Modus** – KuCoin API (Read-Only → Trading)
- [ ] **Push-Notifications** – Mobile Alerts (Android)
- [ ] **Asset-Datenbank** – Sektoren, Beschreibungen, Icons
- [ ] **Offene-Positionen-Detailseite** – Mehr Info, Chart, Historie
- [ ] **Echtzeit-Preise** – WebSocket statt Polling
- [ ] **Dark/Light Mode Toggle** – Farbschema umschaltbar
- [ ] **Drift-Local-Cache** – Offline-First mit lokaler SQLite im Flutter-Client

---

## Architektur

```
┌─────────────────────────────────────────────────┐
│  Flutter Frontend (CachyOS + Android + Web)      │
│  Riverpod · fl_chart · go_router · dio           │
│  Native Linux · APK · PWA                         │
└───────────────────────┬─────────────────────────┘
                        │ HTTP/JSON
┌───────────────────────▼─────────────────────────┐
│  FastAPI Backend (LXC 104)                        │
│  SQLAlchemy async · Alembic · yfinance · ccxt     │
│  Port 8000                                        │
└───────────────────────┬─────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────┐
│  SQLite Database (trading.db)                     │
│  trades · settings                                │
└──────────────────────────────────────────────────┘
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
| Routing | go_router | 14.0+ |

## CI-Farben

| Farbe | Hex | Verwendung |
|-------|-----|-----------|
| Grün/Positiv | `#00b09b` | Gewinne, LONG-Signal, Bullish |
| Rot/Negativ | `#e74c3c` | Verluste, SHORT-Signal, Bearish |
| Gold | `#f0a500` | Highlights, Alerts |
| Blau | `#3498db` | Links, Sekundär |
| Violett | `#9b59b6` | Krypto-Sektor |
| Dunkel | `#0d1117` | Hintergrund |

## Entwicklungsprinzipien

- **Paper-First:** Jedes Feature zuerst im Paper-Modus testen
- **API-first:** Backend-Endpoint vor Flutter-UI implementieren
- **Cross-Platform:** Eine Codebasis für CachyOS, Android und Web
- **Tests mitdenken:** Backend: pytest + TestClient, Frontend: widget_test.dart
- **Security:** API-Keys NIE im Flutter-Code – immer im Backend `~/.env`
- **Offline-First:** Lokale drift-DB als Cache, FastAPI als Remote-Source
- **CI-Konsistenz:** Gleiche Farbwerte wie trading-crew Dashboard
- **Repo-Sprache:** Docs DE+EN, Code-Kommentare EN, Commit-Messages EN