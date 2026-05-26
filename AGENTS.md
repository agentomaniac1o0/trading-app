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
- [ ] KuCoin API-Key für Live-Preise (Read-Only)
- [ ] Trading Crew: Reports in Category-Pattern schreiben
- [ ] trades.json von trading-crew kopieren + ersten Import-Run
- [ ] Backend auf LXC 104 deployen (pve-1 Zugang fehlt aktuell)
- [ ] Settings-Page mit echten Werten (API-Status, DB-Status)

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
- Projekt `~/monitoring-app/` erstellt mit AGENTS.md
- GitHub: https://github.com/agentomaniac1o0/monitoring-app
- Geplant: Monitoring-App als separate Flutter-App, Backend in trading-app/backend erweitert
- Daten: strukturiertes JSON von Monitoring Crews, live Health-Checks
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

