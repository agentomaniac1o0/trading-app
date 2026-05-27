#!/bin/bash
# Trading App – One-Command Update
set -e

BOLD="\033[1m"
GREEN="\033[32m"
RESET="\033[0m"

API_URL="${API_BASE_URL:-http://100.103.32.107:8000}"
TRADING_DIR="${TRADING_DIR:-$HOME/trading-app}"

echo -e "${BOLD}${GREEN}═══ Trading App Update ═══${RESET}"

if [ ! -d "$TRADING_DIR" ]; then
    echo "→ Klonen..."
    git clone https://github.com/agentomaniac1o0/trading-app.git "$TRADING_DIR"
fi

cd "$TRADING_DIR"
echo "→ git pull..."
git pull

cd frontend
echo "→ flutter build linux..."
flutter build linux --release --dart-define="API_BASE_URL=$API_URL"

echo "→ copy desktop integration..."
cp "$TRADING_DIR/flatpak/app.trading.TradingApp.desktop" "$TRADING_DIR/frontend/build/linux/x64/release/bundle/"
cp "$TRADING_DIR/flatpak/icon.png" "$TRADING_DIR/frontend/build/linux/x64/release/bundle/"

cd ../flatpak
rm -rf .flatpak-builder
echo "→ flatpak install..."
flatpak-builder --repo=repo --force-clean --install --user build-dir \
    app.trading.TradingApp.yml

echo "→ link desktop entry..."
mkdir -p $HOME/.local/share/applications
ln -sf $HOME/.local/share/flatpak/exports/share/applications/app.trading.TradingApp.desktop $HOME/.local/share/applications/

echo ""
echo -e "${GREEN}✓ App bereit:${RESET} flatpak run app.trading.TradingApp"
echo -e "  Commit: $(git -C "$TRADING_DIR" rev-parse --short HEAD)"
