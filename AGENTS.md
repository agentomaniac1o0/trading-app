# Trading App – Projektanweisungen

## Projektziel

Cross-Platform Trading App (FastAPI + Flutter) mit Paper Trading und Erweiterungsoption auf Live-Trading. Das Backend dient **beiden Frontends**: Trading App (Flutter) und Mission Control App (separates Flutter-Projekt in `~/missioncontrol-app/`).

**Repo:** `~/trading-app/` (öffentlich auf GitHub)
**Deployment:** ai-agents VM (CachyOS) — Tailscale-Only-Binding an `100.103.32.107`

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
├── ROADMAP.md
├── update.sh              # One-Command Update (git pull → build → flatpak)
├── .gitignore
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── alembic.ini
│   ├── static/
│   │   └── avatars/        # Trader-Avatare (PNG, über /static/avatars/ served)
│   │       ├── buffett.png, lynch.png, soros.png
│   │       ├── wood.png, saylor.png, planb.png
│   ├── tests/
│   └── app/
│       ├── main.py          # FastAPI-App, CORS, Router-Registrierung
│       ├── config.py
│       ├── database.py
│       ├── models.py         # Trade, Setting, TraderJudgment
│       ├── schemas.py        # Pydantic-Schemas (324 Zeilen, Trading + Mission Control)
│       ├── crud.py
│       ├── routers/
│       │   ├── trades.py           # GET/POST/PATCH Trade-Endpoints
│       │   ├── portfolio.py        # GET Portfolio Summary + Live Portfolio
│       │   ├── prices.py           # GET Live-Preise + Search + History
│       │   ├── traders.py          # GET Trader-Profile mit Base64-Avataren
│       │   ├── reports.py          # GET Market Reports + Portfolio Review
│       │   ├── judgments.py        # GET/POST Trader-Judgments pro Symbol
│       │   └── missioncontrol.py   # Monitoring: Overview, System, Live, Health,
│       │                           #   Code-Quality, Reports, Graphiphy (SVG/PNG/HTML)
│       └── services/
│           ├── price_engine.py     # yfinance + ccxt/KuCoin mit Cache
│           ├── asset_db.py         # 35+ Assets mit Symbol+Market-Mapping
│           ├── evaluator.py        # Trigger für trading-crew evaluate.py
│           └── import_trades.py    # trades.json → SQLite Migration
├── frontend/
│   ├── pubspec.yaml
│   ├── assets/
│   │   ├── avatars/          # Trader-Avatare (Flutter Asset Bundle)
│   │   └── report_icons/     # Report-Kategorie-Icons (PNG)
│   └── lib/
│       ├── main.dart
│       ├── app.dart               # GoRouter + ThemeModeProvider
│       ├── config/
│       │   ├── api_config.dart
│       │   └── theme.dart         # Dark + Light Theme
│       ├── models/
│       │   ├── live_portfolio.dart
│       │   ├── portfolio.dart
│       │   ├── portfolio_review.dart
│       │   ├── price.dart
│       │   ├── trade.dart           # inkl. stopLoss-Feld
│       │   └── trader_profile.dart
│       ├── services/
│       │   ├── api_client.dart
│       │   ├── asset_search_service.dart
│       │   └── price_service.dart
│       ├── providers/
│       │   ├── live_portfolio_provider.dart
│       │   ├── market_report_provider.dart
│       │   ├── portfolio_provider.dart
│       │   ├── portfolio_review_provider.dart
│       │   ├── price_provider.dart
│       │   ├── trade_provider.dart
│       │   └── trader_provider.dart
│       ├── pages/
│       │   ├── market_reports_page.dart   # 8 Kategorien + Portfolio Review
│       │   ├── portfolio_page.dart        # KPIs + Sparklines + Trader Board
│       │   ├── trade_close_page.dart      # Merge + Partial Close + Stop-Loss
│       │   ├── trade_open_page.dart       # Autocomplete + Stop-Loss-Eingabe
│       │   └── settings_page.dart         # Dark/Light-Toggle
│       └── widgets/
│           ├── ampel_indicator.dart
│           ├── kpi_card.dart
│           ├── portfolio_review_card.dart  # AI-Kommentator
│           ├── price_chart.dart
│           ├── sparkline.dart
│           ├── trade_card.dart
│           └── trader_avatar_row.dart
├── flatpak/
│   ├── app.trading.TradingApp.yml
│   ├── app.trading.TradingApp.desktop
│   ├── icon.png
│   ├── build-dir/
│   └── repo/
├── data/
│   └── trades.json
├── graphify-out/              # Knowledge Graph (generiert von graphify)
└── deploy/
    └── lxc104-setup.sh
```

## Phase 1 – MVP (abgeschlossen)

1. **Projekt-Setup** – FastAPI + Flutter + SQLite + GitHub + Deployment
2. **Portfolio-Übersicht** – KPIs (Startkapital, Kassenbestand, Portfoliowert, P&L, Win-Rate)
3. **Trade erfassen** – LONG/SHORT, Live-Preis, Asset-Datenbank, Autocomplete
4. **Trade schließen** – P&L-Berechnung, Historie, Partial Close, Stop-Loss
5. **Daten-Migration** – trades.json → SQLite Import
6. **Market Reports** – 8 Kategorien + Portfolio Review, HTML/Markdown-Rendering
7. **Trader Board** – Profile mit Avataren, Traits, AI-Kommentator
8. **Mission Control Backend** – Monitoring API (Overview, System, Live, Health, Code Quality)
9. **Graphiphy** – Knowledge Graph Viz (SVG/PNG/HTML, Communities, God-Nodes, Search)
10. **Flatpak-CD** – Continuous Delivery via OSTree-Repo

## Phase 2 – In Bearbeitung

- Mission Control Frontend (separates Flutter-Projekt `~/missioncontrol-app/`)
- Settings-Page mit Live-API-Status und DB-Status
- Live-Trading-Modus (KuCoin API, Read-Only + API-Key)

## Phase 3+ (später)

- Circuit Breaker (automatischer Stop nach X Verlusten)
- Backtesting (historische Strategie-Simulation)
- Push-Notifications (Mobile Alerts)
- Echtzeit-Preise (WebSocket statt Polling)
- Drift-Local-Cache (Offline-First)

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
- **Tailscale-Only:** Alle Services binden an `100.103.32.107`, niemals `0.0.0.0` oder `127.0.0.1`
- **Tests mitdenken:** Backend: pytest + TestClient, Frontend: widget_test.dart
- **Security:** API-Keys NIE im Flutter-Code – immer im Backend `~/.env`
- **Offline-First:** Lokale drift-DB als Cache, FastAPI als Remote-Source
- **CI-Konsistenz:** Gleiche Farbwerte wie trading-crew Dashboard
- **Repo-Sprache:** Docs DE+EN, Code-Kommentare EN, Commit-Messages EN

## API-Endpoints

### Trading API (`/api/`)

| Methode | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/api/trades` | Offene + geschlossene Trades |
| POST | `/api/trades` | Neuen Trade eröffnen |
| PATCH | `/api/trades/{id}/close` | Trade schließen (Partial Close möglich) |
| GET | `/api/portfolio` | Portfolio-Zusammenfassung (KPIs) |
| GET | `/api/portfolio/live` | Live-Portfolio mit aktuellen Preisen |
| GET | `/api/prices/{symbol}` | Live-Preis für Symbol |
| GET | `/api/prices/{symbol}/history?days=N` | Preis-Historie (7-30 Tage) |
| GET | `/api/prices/search?q=` | Asset-Suche (Name/Symbol) |
| GET | `/api/traders` | Trader-Profile mit Base64-Avataren |
| GET | `/api/judgments/{symbol}` | Trader-Judgments für Symbol |
| POST | `/api/judgments` | Trader-Judgments speichern |
| GET | `/api/reports/market` | Alle Report-Kategorien auflisten |
| GET | `/api/reports/market/{category}` | Neuester Report pro Kategorie |
| GET | `/api/reports/portfolio-review` | Neuester Portfolio Review |
| GET | `/api/health` | Health-Check |

### Mission Control API (`/api/missioncontrol/`)

| Methode | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/{location}/overview` | Systemübersicht (Status, Health-Score, Alerts) |
| GET | `/{location}/system` | Detailliertes System (Host, VMs, Services, Backups, Updates) |
| GET | `/{location}/live` | Live-Healthchecks (Ping + TCP-Checks) |
| GET | `/{location}/health` | Health-Score-Berechnung |
| GET | `/{location}/code-quality` | Security-Audit-Findings, Open Ports |
| GET | `/{location}/reports` | Monitoring-Report-Liste |
| GET | `/{location}/reports/{filename}` | Einzeler Report-Details |
| GET | `/{location}/graphiphy/stats` | Knowledge Graph Statistiken |
| GET | `/{location}/graphiphy/god-nodes` | Top-N God-Nodes |
| GET | `/{location}/graphiphy/communities` | Community-Liste |
| GET | `/{location}/graphiphy/community/{id}` | Community-Nodes |
| GET | `/{location}/graphiphy/search?q=` | Graph-Suche |
| GET | `/{location}/graphiphy/viz` | Interaktive HTML-Visualisierung |
| GET | `/{location}/graphiphy/svg` | SVG-Export |
| GET | `/{location}/graphiphy/png` | PNG-Export (200 DPI) |
| POST | `/{location}/graphiphy/viz/refresh` | Graph aktualisieren |

**Location-Parameter:** `home-lab` (Standard) oder `production-center`

## Was NICHT hier rein gehört

- CronMaster → bleibt in `agent-templates/`
- Watchdog / Intraday-Alerts → bleibt in `trading-crew/`
- Monitoring Crew (Berichte-Erstellung) → bleibt in `agent-templates/monitoring/`
- Mission Control **Frontend** → separates Flutter-Projekt in `~/missioncontrol-app/`
- **Mission Control Backend-API** → IST hier (`routers/missioncontrol.py`)
- Trading Crew (Agent-Logik) → bleibt in `~/trading-crew/`

## Deployment (ai-agents, CachyOS)

**Security Policy: Tailscale-Only-Binding.** Kein Service bindet an `0.0.0.0` oder `127.0.0.1`. Alle Services binden ausschließlich an `100.103.32.107`.

| Service | Port | Bind-Adresse | Systemd Unit |
|---------|------|-------------|-------------|
| Backend (FastAPI) | 8000 | `100.103.32.107` | `trading-backend.service` |
| Flatpak Repo (HTTP) | 8081 | `100.103.32.107` | `trading-repo.service` |

**Kritische Env-Variablen (`~/.env`):**

| Variable | Wert | Nutzer |
|----------|------|--------|
| `TRADING_BACKEND_URL` | `http://100.103.32.107:8000` | trading-crew `portfolio_context.py` |
| `API_BASE_URL` | `http://100.103.32.107:8000` | Mission Control App |

**Backend starten:**
```bash
cd ~/trading-app/backend && .venv/bin/uvicorn app.main:app --host 100.103.32.107 --port 8000
```

**One-Command Update (update.sh):**
```bash
cd ~/trading-app && bash update.sh
# Macht: git pull → flutter build linux → flatpak-builder → desktop entry install
```

**Flatpak manuell bauen (auf ai-agents Server):**
```bash
cd ~/trading-app/frontend && flutter build linux --release --dart-define=API_BASE_URL=http://100.103.32.107:8000
cd ~/trading-app/flatpak && rm -rf .flatpak-builder && flatpak-builder --repo=repo --force-clean --install --user build-dir app.trading.TradingApp.yml
```

**Client-Update (auf CachyOS-Desktop):**
```bash
flatpak remote-add --user --no-gpg-verify trading-repo http://100.103.32.107:8081  # einmalig
flatpak update app.trading.TradingApp
```

**Android APK:**
```bash
cd ~/trading-app/frontend && flutter build apk --release --dart-define=API_BASE_URL=http://100.103.32.107:8000
# APK: build/app/outputs/flutter-apk/app-release.apk
```

## Session-Log: 2026-05-26

### Portfolio-Review-Refresh-Fix
- **Bug:** Portfolio Review in der mobilen App wurde nicht aktualisiert, Refresh-Button funktionierte nicht
- **Root Cause:** `StateProvider<int>` + `ref.watch()`-Pattern im `FutureProvider` für den Refresh-Trigger funktioniert nicht zuverlassig im Zusammenspiel mit `ConsumerStatefulWidget` + `StatefulShellRoute.indexedStack`
- **Fix:** `portfolio_review_provider.dart`: `StateProvider` entfernt, `refreshPortfolioReview()` nutzt jetzt `ref.invalidate(portfolioReviewProvider)` direkt
- **Fix:** `trade_provider.dart`: `closeTrade()` invalidateiert jetzt den `portfolioReviewProvider` direkt statt uber `portfolioReviewRefreshKey`
- **Fix:** `market_report_provider.dart`: Fehlender `import 'package:dio/dio.dart'` hinzugefugt
- **Betroffene Dateien:**
  - `frontend/lib/providers/portfolio_review_provider.dart`
  - `frontend/lib/providers/trade_provider.dart`
  - `frontend/lib/providers/market_report_provider.dart`

## Session-Log: 2026-05-25

### Trade-Import aus Trading Crew
- **192 Trades** aus `~/trading-crew/data/trades.json` in SQLite importiert (via `import_trades.py`)
- Zeitraum: 2026-03-08 bis 2026-05-22
- 26 offene Positionen, 168 geschlossene Trades
- Portfolio nach Import: Value $10,521.37, Total P&&L +$532.13 (5.32%), Win-Rate 42.3%
- `initial_capital` setting auf $10,000 gesetzt

### Market Reports: Neue Seite + Navigation
- **5\. Tab "Reports"** in Bottom-NavigationBar (zwischen Portfolio und Trades)
- `GoRouter`: `/market-reports` → `MarketReportsPage`
- **8 Kategorien**: Crash Prophet, Diamond Hands, Crypto Analysis, Equities, Forex, Commodities, Real Estate, Trader Perspectives
- Layout: Wide → Sidebar (200px links) + Markdown-Content (rechts), Narrow → Kategorie-Liste oben + Content unten
- `flutter_markdown` ^0.7.0 zur `pubspec.yaml` hinzugefügt

### Backend: Market-Report-Endpoints
- `GET /api/reports/market/{category}` — liefert neuesten Report als JSON `{category, report_date, content}`
- `GET /api/reports/market` — listet alle 8 Kategorien mit Verfügbarkeit auf
- Datei-Pattern: `~/trading-crew/data/reports/{category}_*.txt` (z.B. `crashprophet_2026-05-25.txt`)
- 404 wenn kein Report existiert → Frontend zeigt "Kein Report verfügbar"
- Trading Crew muss zukünftig Reports in dieses Pattern schreiben

### Trades-Sektion erweitert
- `trade_close_page.dart`: Portfolio-Review-Assets mit Trader-Urteilen unter der Liste offener Trades
- AppBar-Titel von "Close Trade" → "Trades"
- `portfolioReviewProvider` wird mitgewacht, ReviewCard darunter gerendert

### Portfolio-Seite bereinigt
- Market-Reports-Karte aus Portfolio-Seite entfernt (jetzt eigener Tab)
- `_buildMarketReports()`-Methode gelöscht

### Neue Dateien
- `frontend/lib/pages/market_reports_page.dart`
- `frontend/lib/providers/market_report_provider.dart`

### Betroffene Dateien
- `frontend/lib/app.dart` — 5\. Tab + Route
- `frontend/pubspec.yaml` — flutter_markdown
- `backend/app/routers/reports.py` — 2 neue Endpoints
- `frontend/lib/pages/trade_close_page.dart` — Review-Section
- `frontend/lib/pages/portfolio_page.dart` — Market-Reports entfernt

## Session-Log: 2026-05-25 (früher)

### Trader Board: Vom AppBar ins Portfolio-Body
- **Problem:** Trader-Profile waren eng linksbündig in horizontal scrollbarer AppBar-Leiste (40px Höhe) — kaum sichtbar, keine Beschreibung
- **Lösung:** Trader-Profile aus `AppBar.bottom` entfernt und als vollflächige "Trader Board"-Karte oben im Portfolio-Body platziert
  - Layout: `Wrap` mit `spacing: 12`, `runSpacing: 12` — je 2 Trader pro Zeile über die ganze Breite
  - `_TraderTile`: `SizedBox(width: (screen-60)/2)` → Row mit Avatar (r=18) + Expanded(Column mit Name, Title, Traits)
  - Traits als farbige Badges (`Container` mit farbigem Hintergrund, farbigem Text)
- **Betroffene Dateien:**
  - `frontend/lib/widgets/trader_avatar_row.dart` — Wrap-Layout, vergrößerter Avatar, Title + Trait-Badges
  - `frontend/lib/pages/portfolio_page.dart` — Trader aus AppBar.bottom entfernt, `_buildTraderProfiles()` als Card im ListView
  - Import `trader_profile.dart` hinzugefügt
- **Commit:** `b060041` feat: Trader Board as full-width card with Wrap layout, avatar + title + trait badges

### Flatpak-Build-Workflow korrigiert
- **Root Cause:** `.flatpak-builder/` cached alte Quellen → `--force-clean` reicht nicht, Cache muss gelöscht werden
- **Workflow-Fix:** `rm -rf .flatpak-builder` VOR jedem `flatpak-builder`-Aufruf
- **Client-Build:** Immer `git pull` vor `flutter build` wenn Frontend-Code geändert wurde
- AGENTS.md-Deployment-Section aktualisiert mit korrigierten Befehlen

## Session-Log: 2026-05-22

### Flatpak-Build & Continuous Delivery
- Flutter Linux-Release gebaut mit `--dart-define=API_BASE_URL=http://100.103.32.107:8000` (Tailscale-IP ai-agents)
- Flatpak via `flatpak-builder --repo=repo` gebaut
- `trading-repo.service` (systemd --user) serviert Flatpak-OSTree-Repo persistierend auf Port 8081
- `trading-backend.service` (systemd --user) startet FastAPI auf Port 8000
- Client updated via `flatpak update app.trading.TradingApp` ohne manuelles Deinstallieren

### Navigation-Fix
- `app.dart`: `GoRouter`-Routen in `StatefulShellRoute.indexedStack` eingebettet
- `HomeShell` mit `NavigationBar` korrekt mit Router verdrahtet
- Alle 4 Tabs jetzt erreichbar: Portfolio, Trades, New Trade, Settings

### Asset-Datenbank + Autocomplete-Suche
- `backend/app/services/asset_db.py`: 35+ Assets (Rohstoffe, Tech-Aktien, Krypto, Forex, ETFs) mit Symbol+Market-Mapping
- `GET /api/prices/search?q=` – Case-insensitive Suche nach Name oder Symbol
- `frontend/lib/services/asset_search_service.dart` – Dio-Client für Search-API
- Trade-Open-Page: Autocomplete-Eingabefeld ersetzt manuelle Symbol-Eingabe; bei Auswahl werden Name, Symbol, Market und Live-Preis automatisch gesetzt

### Gold-Preis-Fix
- Problem: `GOLD` (Ticker) = Barrick Gold Mining-Aktie ($43.40) statt Gold-Future
- Lösung: AssetDB mapped "Gold" → `GC=F` ($4,510.50)

### Portfolio-Berechnung korrigiert
- `portfolio.py`: Formel von `cash + invested + closed_pnl` auf `initial_capital - invested + closed_pnl` korrigiert
- Cash = initial_capital − Summe(offene Trades) + Summe(geschlossene P&L)
- Portfolio Value = Cash + Invested = initial_capital + Summe(geschlossene P&L)

### P&L-Kurve + Sparklines
- Portfolio: Kumulierte P&L-Kurve (fl_chart LineChart) über geschlossene Trades
- Portfolio: Offene Positionen mit Kosten-Aufschlüsselung
- Sparkline-Widget (`widgets/sparkline.dart`): Mini-LineChart mit 7-Tage-Verlauf pro offener Position
- `GET /api/prices/{symbol}/history?days=N` – yfinance (Stocks) / KuCoin CCXT (Crypto)

### Trade schließen UX
- Live-Preis wird automatisch beim Betreten der Seite geladen
- Close-Button sofort klickbar (holt Preis nach wenn nötig)
- `trade_provider.dart`: `openTrade()` und `closeTrade()` invalidieren jetzt auch `portfolioProvider`

### Neue Dateien
- `backend/app/services/asset_db.py`
- `frontend/lib/services/asset_search_service.dart`
- `frontend/lib/widgets/sparkline.dart`

## Offen

- [x] GitHub-Repo erstellt und gepusht (https://github.com/agentomaniac1o0/trading-app)
- [x] LXC 104 auf pve-1 eingerichtet (Debian 13, Python 3.13, Flutter, Dart)
- [x] FastAPI Backend Grundstruktur
- [x] Flutter Frontend Grundstruktur
- [x] SQLite Schema + Alembic Migration
- [x] trades.json → SQLite Import-Migration
- [x] Backend-Start testen (`uvicorn app.main:app`)
- [x] Flutter-Build testen (`flutter build web`)
- [x] End-to-End: Trade öffnen, Preis holen, Trade schließen
- [x] Navigation mit BottomNavigationBar (4 Tabs)
- [x] Asset-Datenbank + Autocomplete-Suche (Trade erfassen)
- [x] Portfolio-Berechnung korrigiert
- [x] P&L-Kurve + Sparklines im Portfolio
- [x] Flatpak-Continuous-Delivery (systemd + Remote-Update)
- [x] Trader Board: Vollflächige Card mit Wrap-Layout, Avatar, Name, Title, Trait-Badges
- [x] Trade-Import: 192 Trades aus Trading Crew in SQLite importiert
- [x] Market Reports Page: 5. Tab, 8 Kategorien, Markdown-Renderer
- [x] Backend: GET /api/reports/market/{category} + /api/reports/market
- [x] Trades-Sektion: Portfolio-Review-Assets unter offenen Trades
- [x] Stop-Loss-System + Partial Close
- [x] Trade-Merge (gleiche Assets gruppiert)
- [x] Dark/Light Mode Toggle
- [x] HTML-Report-Rendering + Report-Zeitstempel
- [x] Mission Control Backend API (Overview, System, Live, Health, Code Quality, Graphiphy)
- [x] Netzwerk-Security-Härtung (Tailscale-Only-Binding)
- [x] Tailscale-Only-Binding für alle Services
- [x] `update.sh` — One-Command Update
- [ ] KuCoin API-Key für Live-Preise (Read-Only)
- [ ] Settings-Page mit echten Werten (API-Status, DB-Status, Theme-Persistierung)
- [ ] Mission Control Frontend (separates Flutter-Projekt `~/missioncontrol-app/`)
- [ ] Trading Crew: Reports in Category-Pattern schreiben
- [ ] Backend auf LXC 104 deployen (pve-1 Zugang fehlt aktuell)

## Session-Log: 2026-05-25 (später)

### Portfolio-Layout-Fix: IntrinsicHeight
- **Bug:** `Container(height: double.infinity)` als Divider im `Row` der Overview-Card in einer `ListView` → Card unendlich hoch → alle nachfolgenden Sections (P&L Curve, Open Positions, Portfolio Review) verschluckt
- **Root Cause:** Commit `31e5614` hatte `Container(height: 80)` durch `height: double.infinity` ersetzt
- **Fix:** Row mit `IntrinsicHeight` + `CrossAxisAlignment.stretch` umwickelt, `height: double.infinity` entfernt

### Responsive Overview Card
- Wide (>700px): Trader Icons links, Dashboard rechts mit vertikalem Divider
- Mobile: untereinander gestapelt mit horizontalem Divider dazwischen

### Portfolio Review → Reports verschoben
- `_buildPortfolioReview` aus Portfolio-Page entfernt
- Als 9. Kategorie (default) in MarketReportsPage integriert
- Rendert `PortfolioReviewCard` statt Markdown

### Android-Build
- Android SDK + NDK + Java installiert
- `flutter create --platforms=android .` für Android-Projektstruktur
- `AndroidManifest.xml`: `INTERNET`-Permission + `usesCleartextTraffic="true"` (HTTP zum Backend)
- APK-Build erfolgreich (66.1 MB)
- APK in Nextcloud: `Home Lab/Trading App/trading-app-YYYYMMDD-HHMM.apk`

### Reports-Fix (mobile)
- Narrow-Layout: Kategorie-Liste war vertikale `ListView` mit height:50 → nur 1 Kategorie sichtbar
- Fix: `ListView.builder` mit `scrollDirection: Axis.horizontal` auf mobile

### Monitoring-App initiiert
- Grill-Me-Session: 11 Architektur-Entscheidungen getroffen
- Projekt `~/missioncontrol-app/` erstellt mit AGENTS.md
- GitHub: https://github.com/agentomaniac1o0/monitoring-app
- **Mission Control Backend-API** ist in trading-app (`routers/missioncontrol.py`)
- Mission Control **Frontend** als separates Flutter-Projekt (`~/missioncontrol-app/`)
- Daten: strukturiertes JSON von Monitoring Crews, live Health-Checks
- Streamlit-Dashboard (`trading-crew/app/`) wurde gelöscht
---

## Session-Log: 2026-05-27 – Umfangreiches Trading-App-Update

### HTML-Report-Rendering (Flutter)
- `flutter_html: ^3.0.0-beta.2` als Dependency hinzugefügt
- `market_reports_page.dart`: Auto-Detection HTML vs Markdown, HTML-Rendering via `flutter_html` mit Dark-Theme-Styling
- Avatar-Pfade in HTML-Reports werden zu Punktsymbolen konvertiert (Bilder via Asset-Bundle komplex)
- Trader-Avatars nach `frontend/assets/avatars/` kopiert (buffett, lynch, soros, wood, saylor, planb)

### Report-Zeitstempel
- Backend `reports.py`: Extrahiert `report_time` aus Dateinamen (`HH-MM.txt`) oder fällt auf mtime zurück
- Frontend: Zeigt `Report: 2026-05-26 at 21:30` statt nur Datum

### Stop-Loss-System
- **Backend**: `stop_loss`-Feld in Trade-Model (DB-Migration via ALTER TABLE), Schema `TradeCreate`/`TradeResponse`, CRUD `create_trade`
- **Frontend**: Eingabefeld beim Trade-Eröffnen (optional), Anzeige im Trade-Balken mit Shield-Icon
- **Stop-Loss-HIT-Warnung**: Wenn Live-Preis den Stop-Loss erreicht/überschreitet → rote Warnung mit ⚠️

### Partial Close (Teilschließung)
- **Backend**: `TradeClose.quantity_close` — bei Teilmenge wird Closed-Trade-Record erstellt, offene Menge reduziert, P&L proportional berechnet
- **Frontend**: "Close Qty"-Eingabefeld + Button in Trade-Tiles. "Close All" für alle Positionen eines Assets

### Trade-Merge (gleiche Assets gruppiert)
- `trade_close_page.dart` komplett neu: `_groupBySymbol()` fasst gleiche Assets zusammen
- Ein Balken pro Asset mit: Positions-Count-Badge, Gesamtmenge, Ø-Einstieg, Live-Preis, Est. P&L
- Aufklappbar für Einzelpositionen mit separatem Close-Button

### Portfolio Open Positions – Sparklines
- `portfolio_page.dart`: `_LivePositionTile` (ConsumerWidget) ersetzt alte `_LivePositionRow`
- `_priceHistoryProvider` (FutureProvider.family) lädt 7-Tage-Historie pro Symbol
- Sparkline-Kurve (50px) mit grün/rot je nach Trend, Touch-Tooltip
- Entry/Live-Preis + Quantity darunter

### Trader-Icon-Redesign
- `trader_avatar_row.dart`: `spacing: 16`, `runSpacing: 12` für mehr Abstand
- Jeder Trader als geblockte Card mit `Container`-Border + 16px Avatar + Name + Traits
- Dashboard-Titel auf 18px, KPI-Blöcke mit farbigem Hintergrund + Border

### Portfolio Review AI-Kommentator
- `portfolio_review_card.dart`: Neue `_Kommentator`-Widget-Klasse
- Zählt bullische/bearische/Halten-Signale über alle Trader-Urteile
- Identifiziert kritische Assets (≥3 VERKAUFEN) und starke Assets (≥4 KAUFEN/AUFSTOCKEN)
- Generiert Sentiment-Summary mit Prozent-Angaben und konkreten Handlungsempfehlungen
- Violette Gradient-Box mit 🧠-Icon

### Dark/Light Mode
- `theme.dart`: `buildDarkTheme()` + `buildLightTheme()` mit separierten Farben
- Light-Theme: hellgrauer Hintergrund, weiße Cards, dunkle Texte, selbe Accent-Farben
- `settings_page.dart`: Switch-Toggle für Dark/Light
- `app.dart`: `TradingApp` → `ConsumerWidget`, watched `themeModeProvider` (StateProvider)
- Theme wird sofort umgeschaltet, kein Neustart nötig

### Backend-Fixes
- `reports.py`: `_parse_portfolio_review()` sucht jetzt nach "PORTFOLIO_REVIEW" (case-insensitive) zusätzlich zu "## PORTFOLIO", ignoriert HTML-Tags

### Builds
- Linux: `build/linux/x64/release/bundle/trading_app`
- Android: APK in Nextcloud `Home Lab/Trading App/`

### Betroffene Dateien (trading-app)
- `backend/app/models.py` — stop_loss-Feld
- `backend/app/schemas.py` — stop_loss, quantity_close
- `backend/app/crud.py` — partial close, stop_loss in create
- `backend/app/routers/reports.py` — report_time, robuste portfolio-review-Parsing
- `frontend/lib/models/trade.dart` — stopLoss-Feld
- `frontend/lib/providers/trade_provider.dart` — quantityClose in closeTrade
- `frontend/lib/pages/portfolio_page.dart` — Sparklines, blockigere KPIs, ConsumerWidget-Fix
- `frontend/lib/pages/trade_close_page.dart` — Merge + Partial Close
- `frontend/lib/pages/trade_open_page.dart` — Stop-Loss-Feld
- `frontend/lib/pages/market_reports_page.dart` — HTML-Rendering + Uhrzeit
- `frontend/lib/pages/settings_page.dart` — Dark/Light-Toggle
- `frontend/lib/widgets/portfolio_review_card.dart` — AI-Kommentator
- `frontend/lib/widgets/trader_avatar_row.dart` — Spacing + Card-Design
- `frontend/lib/config/theme.dart` — Light Theme
- `frontend/lib/app.dart` — ThemeModeProvider
- `frontend/pubspec.yaml` — flutter_html dependency + avatar assets

### Betroffene Dateien (trading-crew)
- `crew/tasks.py` — alle Build-Tasks auf HTML-Output umgestellt
- `crew/crew.py` — _clean_report, _split_and_save_categories, _fill_missing für HTML
- `app/` — gelöscht (Streamlit)
- `crew/portfolio_context.py` — Import-Pfad korrigiert
- `crew/trading_data.py` — aus app/ verschoben

## Session-Log: 2026-05-28 – Netzwerk-Security-Härtung & Bugfixes

### Netzwerk-Bindung (Security Policy)
- **Regel:** Kein Service bindet an `0.0.0.0` oder `127.0.0.1`. Alle Services binden **ausschließlich an die Tailscale-IP** `100.103.32.107`.
- **Begründung:** Services sind nur über das Tailscale-Mesh erreichbar — kein LAN/WAN-Zugriff. `127.0.0.1` bricht lokale Prozesse (Crew, Monitoring), `0.0.0.0` exponiert unnötig.

| Port | Service | Bind-Adresse | Systemd-Unit |
|------|---------|-------------|--------------|
| 8000 | FastAPI Backend | `100.103.32.107` | `trading-backend.service` |
| 8081 | Flatpak OSTree Repo | `100.103.32.107` | `trading-repo.service` |
| 22 | SSH | `100.103.32.107` | (system) |

### TRADING_BACKEND_URL Env-Variable
- **Datei:** `~/.env` → `TRADING_BACKEND_URL=http://100.103.32.107:8000`
- **Nutzer:** `trading-crew/crew/portfolio_context.py` liest diese Variable (Fallback: `http://localhost:8000`)
- **Warum kritisch:** Ohne diese Variable fällt die Crew auf `trades.json` (Stand: Mai 2022) zurück und produziert Portfolio-Reviews mit veralteten/verkauften Assets.

### Portfolio-Review-Parser-Fix
- **Bug:** Writer-Format-Change: `(SHORT 1 Pos.)` statt `(SHORT x1)` → `_parse_header()`-Regex fand keine Assets
- **Fix:** `backend/app/routers/reports.py:37` – Regex von `x(\d+)` auf `(?:x)?(\d+)\b` geändert (optionales `x`)
- **Betroffene Datei:** `backend/app/routers/reports.py`

