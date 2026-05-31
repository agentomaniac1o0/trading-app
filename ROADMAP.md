# Trading App – Roadmap

**Repo:** `~/trading-app/` (öffentlich auf GitHub)
**Plattformen:** CachyOS (Linux Desktop) + Android (Mobile)
**Deployment:** ai-agents VM (Tailscale-Only an `100.103.32.107`)

## Plattform-Ziele

| Plattform | Ziel | Status |
|-----------|------|--------|
| CachyOS (Linux) | Flutter Desktop (native) + Flatpak | Aktiv |
| Android | Flutter Mobile APK | Build erfolgreich |
| Web | Flutter Web Build (nicht aktiv deployed) | Scaffolded |

Flutter kompiliert aus einer Codebasis für alle drei Targets (`flutter run -d linux`, `flutter build apk`, `flutter build web`). Die Unterscheidung erfolgt ausschließlich über den Build-Target, nicht im Code.

---

## Phase 1 – MVP (abgeschlossen)

### Backend
- [x] FastAPI Backend komplett aufgesetzt (`config.py`, `database.py`, `models.py`, `schemas.py`, `crud.py`)
- [x] Trade CRUD (öffnen, schließen, Partial Close, Stop-Loss)
- [x] Portfolio Summary + Live Portfolio mit aktuellen Preisen
- [x] Preis-Engine: yfinance (Stocks) + ccxt/KuCoin (Crypto) mit Cache
- [x] Asset-Datenbank: 35+ Assets mit Symbol-Mapping
- [x] Trader-Profile API (5 Trader mit Avataren, Traits, Bio)
- [x] Trader-Judgments CRUD (GET/POST pro Symbol)
- [x] Market-Report-Endpoints (8 Kategorien + Portfolio Review)
- [x] Mission Control API (Overview, System, Live, Health, Code Quality, Reports)
- [x] Graphiphy Endpoints (Stats, God-Nodes, Communities, Search, Viz, SVG, PNG)
- [x] Alembic Migration + `trades.json` → SQLite Import
- [x] Tailscale-Only-Binding (`100.103.32.107`)

### Frontend
- [x] Dark/Light Mode mit sofortigem Toggle
- [x] 5 Tabs: Portfolio, Trades (Merge+Partial Close), New Trade, Reports, Settings
- [x] Market Reports Page: 8 Kategorien + Portfolio Review (HTML + Markdown)
- [x] AI-Kommentator: Sentiment-Summary über Trader-Urteile
- [x] Stop-Loss-Eingabe + Stop-Loss-HIT-Warnung
- [x] Sparklines (7-Tage-Historie pro offener Position)
- [x] P&L-Kurve über geschlossene Trades
- [x] Autocomplete-Asset-Suche
- [x] Trader Board mit Avataren + Trait-Badges

### Infrastruktur
- [x] Flatpak Continuous Delivery (systemd + OSTree-Repo)
- [x] Android APK-Build (66.1 MB)
- [x] `update.sh` — One-Command Update (git pull → build → flatpak)
- [x] Desktop-Integration (.desktop file + icon)

---

## Phase 2 – In Bearbeitung

- [ ] **Mission Control Frontend** — separates Flutter-Projekt (`~/missioncontrol-app/`) nutzt `/api/missioncontrol/`
- [ ] **Settings-Page** — Live-API-Status, DB-Status, Theme-Persistierung
- [ ] **KuCoin API-Key** — Read-Only Live-Preise für Crypto

---

## Phase 3 – Geplant

- [ ] **Live-Trading-Modus** — KuCoin API (Read-Only → Trading)
- [ ] **Circuit Breaker** — Automatischer Stop nach X Verlusten
- [ ] **Backtesting** — Historische Strategie-Simulation
- [ ] **Push-Notifications** — Mobile Alerts (Android)
- [ ] **Asset-Datenbank** — Sektoren, Beschreibungen, Icons
- [ ] **Offene-Positionen-Detailseite** — Mehr Info, Chart, Historie
- [ ] **Echtzeit-Preise** — WebSocket statt Polling
- [ ] **Drift-Local-Cache** — Offline-First mit lokaler SQLite im Flutter-Client

---

## Architektur

```
┌───────────────────────┐  ┌───────────────────────┐
│  Trading App (Flutter) │  │  Mission Control (Flutter)│
│  Paper Trading + Reports│  │  Monitoring + Graphiphy │
│  Port 8080 / Native    │  │  Separates Repo          │
└───────────┬───────────┘  └───────────┬─────────────┘
            │ HTTP/JSON                │ HTTP/JSON
┌───────────▼─────────────────────────▼──────────────┐
│  FastAPI Backend (Port 8000, Tailscale-Only)          │
│                                                         │
│  Trading: trades · portfolio · prices · traders         │
│           reports · judgments                           │
│  Mission Control: overview · system · live · health     │
│                    code-quality · reports · graphiphy    │
│                                                         │
│  SQLAlchemy async · Alembic · yfinance · ccxt          │
│  networkx · matplotlib (Graph PNG)                     │
└───────────────────────┬──────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────┐
│  SQLite Database (trading.db)                            │
│  trades · settings · trader_judgments                    │
│  + Monitoring-Reports (filesystem: ~/agent-templates/)  │
│  + Graphiphy graph.json (filesystem: ~/graphify-out/)  │
└─────────────────────────────────────────────────────────┘
```

## Technologie-Stack

| Komponente | Technologie | Version |
|-----------|------------|---------|
| Backend | FastAPI | 0.115+ |
| DB ORM | SQLAlchemy | 2.0+ (async) |
| Migrationen | Alembic | 1.13+ |
| Preise | yfinance + ccxt | latest |
| Graph-Generierung | networkx + matplotlib | latest |
| Frontend | Flutter | 3.24+ |
| State | Riverpod | 2.5+ |
| HTTP | Dio | 5.0+ |
| Charts | fl_chart | 0.69+ |
| HTML-Rendering | flutter_html | ^3.0.0-beta.2 |
| Markdown | flutter_markdown | ^0.7.0 |
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
- **Tailscale-Only:** Alle Services binden an `100.103.32.107`, niemals `0.0.0.0` oder `127.0.0.1`
- **Cross-Platform:** Eine Codebasis für CachyOS, Android und Web
- **Tests mitdenken:** Backend: pytest + TestClient, Frontend: widget_test.dart
- **Security:** API-Keys NIE im Flutter-Code – immer im Backend `~/.env`
- **Offline-First:** Lokale drift-DB als Cache, FastAPI als Remote-Source
- **CI-Konsistenz:** Gleiche Farbwerte wie trading-crew Dashboard
- **Repo-Sprache:** Docs DE+EN, Code-Kommentare EN, Commit-Messages EN