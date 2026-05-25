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
├── ROADMAP.md
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
│           ├── asset_db.py
│           └── import_trades.py
├── frontend/
│   ├── pubspec.yaml
│   └── lib/
│       ├── main.dart
│       ├── app.dart
│       ├── config/
│       │   ├── api_config.dart
│       │   └── theme.dart
│       ├── models/
│       │   ├── live_portfolio.dart
│       │   ├── portfolio.dart
│       │   ├── portfolio_review.dart
│       │   ├── price.dart
│       │   ├── trade.dart
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
│       │   ├── market_reports_page.dart
│       │   ├── portfolio_page.dart
│       │   ├── trade_close_page.dart
│       │   ├── trade_open_page.dart
│       │   └── settings_page.dart
│       └── widgets/
│           ├── ampel_indicator.dart
│           ├── kpi_card.dart
│           ├── portfolio_review_card.dart
│           ├── price_chart.dart
│           ├── sparkline.dart
│           ├── trade_card.dart
│           └── trader_avatar_row.dart
├── flatpak/
│   ├── app.trading.TradingApp.yml
│   ├── build-dir/
│   └── repo/
├── data/
│   └── trades.json
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
- Trading Crew: Category-Reports ins Filesystem schreiben (Pattern: `{category}_YYYY-MM-DD.txt`)
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

## Deployment (ai-agents, CachyOS)

| Service | Port | Systemd Unit | Befehl |
|---------|------|-------------|--------|
| Backend (FastAPI) | 8000 | `trading-backend.service` | `systemctl --user start trading-backend` |
| Flatpak Repo (HTTP) | 8081 | `trading-repo.service` | `systemctl --user start trading-repo` |

**Backend starten:**
```bash
cd ~/trading-app/backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Flatpak bauen (auf ai-agents Server):**
```bash
cd ~/trading-app/frontend && flutter build linux --release --dart-define=API_BASE_URL=http://100.103.32.107:8000
cd ~/trading-app/flatpak && rm -rf .flatpak-builder && flatpak-builder --repo=repo --force-clean --install --user build-dir app.trading.TradingApp.yml
```

**Client-Update (auf CachyOS-Desktop) — bei Frontend-Änderungen IMMER zuerst pullen:**
```bash
flatpak remote-add --user --no-gpg-verify trading-repo http://100.103.32.107:8081  # einmalig
cd ~/trading-app && git pull                                           # Änderungen holen
cd frontend && flutter build linux --release --dart-define=API_BASE_URL=http://100.103.32.107:8000
cd ../flatpak && rm -rf .flatpak-builder && flatpak-builder --repo=repo --force-clean --install --user build-dir app.trading.TradingApp.yml
flatpak run app.trading.TradingApp
```

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
- [ ] KuCoin API-Key für Live-Preise (Read-Only)
- [ ] Trading Crew: Reports in Category-Pattern schreiben
- [ ] trades.json von trading-crew kopieren + ersten Import-Run
- [ ] Backend auf LXC 104 deployen (pve-1 Zugang fehlt aktuell)
- [ ] Settings-Page mit echten Werten (API-Status, DB-Status)