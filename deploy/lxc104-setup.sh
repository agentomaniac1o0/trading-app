#!/bin/bash
set -euo pipefail

echo "=== Trading App – LXC 104 Setup ==="
echo "Target: LXC 104 on pve-1 (Debian 13)"

apt update && apt upgrade -y
apt install -y \
    python3.13 python3.13-venv python3.13-dev \
    pip git curl wget \
    nginx certbot \
    build-essential \
   sqlite3

if ! command -v flutter &>/dev/null; then
    echo "Installing Flutter..."
    snap install flutter --classic 2>/dev/null || {
        git clone https://github.com/flutter/flutter.git -b stable /opt/flutter
        echo 'export PATH="/opt/flutter/bin:$PATH"' >> /etc/profile.d/flutter.sh
        export PATH="/opt/flutter/bin:$PATH"
        flutter precache
    }
fi

echo "Setting up FastAPI backend..."
useradd -m -s /bin/bash trading 2>/dev/null || true
mkdir -p /opt/trading-app/backend /opt/trading-app/data
cd /opt/trading-app/backend
python3.13 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aiosqlite alembic pydantic pydantic-settings yfinance ccxt httpx

echo "Creating systemd service for FastAPI..."
cat > /etc/systemd/system/trading-api.service << 'EOF'
[Unit]
Description=Trading App FastAPI Backend
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/trading-app/backend
ExecStart=/opt/trading-app/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=DATABASE_URL=sqlite+aiosqlite:////opt/trading-app/data/trading.db

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable trading-api

echo "Creating systemd service for Flutter web..."
cat > /etc/systemd/system/trading-web.service << 'EOF'
[Unit]
Description=Trading App Flutter Web Frontend
After=network.target trading-api.service

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/trading-app/frontend
ExecStart=/usr/bin/dart /opt/trading-app/frontend/.dart_tool/flutter_build/web/server.dart
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Configuring nginx reverse proxy..."
cat > /etc/nginx/sites-available/trading-app << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/trading-app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl enable nginx && systemctl restart nginx

echo "Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh
systemctl enable tailscaled
systemctl start tailscaled

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Copy trading-app code to /opt/trading-app/"
echo "2. Copy trades.json to /opt/trading-app/data/"
echo "3. Create /opt/trading-app/backend/.env with API keys"
echo "4. Run: cd /opt/trading-app/backend && venv/bin/alembic upgrade head"
echo "5. Run: systemctl start trading-api"
echo "6. Build Flutter web: cd /opt/trading-app/frontend && flutter build web"
echo "7. Run: systemctl start trading-web"
echo "8. Connect Tailscale: tailscale up"