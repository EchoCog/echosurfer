#!/bin/bash

# Exit on error
set -e

echo "Setting up Deep Tree Echo environment on Shells.com..."

# Configure system limits for better resource management
sudo tee /etc/security/limits.d/deepecho.conf << EOF
deepecho soft nproc 2048
deepecho hard nproc 4096
deepecho soft nofile 8192
deepecho hard nofile 16384
EOF

# Update system
sudo apt-get update

# Install system dependencies (minimal set)
sudo apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    firefox \
    git \
    vim \
    nodejs \
    npm \
    xvfb \
    x11vnc \
    curl \
    wget \
    htop \
    tmux

# Configure swap for better memory management
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Create Deep Tree Echo user
if ! id -u deepecho &>/dev/null; then
    sudo useradd -m -s /bin/bash deepecho
    sudo usermod -aG sudo deepecho
    echo "deepecho ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/deepecho
fi

# Set up project directory
sudo mkdir -p /opt/deepecho
sudo chown deepecho:deepecho /opt/deepecho

# Create and activate virtual environment
python3 -m venv /opt/deepecho/venv
source /opt/deepecho/venv/bin/activate

# Install Python dependencies with version pinning
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright with minimal browsers
playwright install firefox
playwright install-deps

# Configure Firefox for minimal resource usage
mkdir -p /opt/deepecho/.mozilla/firefox/deepecho
cat > /opt/deepecho/.mozilla/firefox/deepecho/user.js << EOF
user_pref("browser.cache.disk.enable", false);
user_pref("browser.cache.memory.enable", true);
user_pref("browser.cache.memory.capacity", 51200);
user_pref("browser.sessionhistory.max_entries", 10);
user_pref("browser.sessionhistory.max_total_viewers", 3);
EOF

# Create systemd service with resource limits
sudo tee /etc/systemd/system/deepecho.service << EOF
[Unit]
Description=Deep Tree Echo - Team Leader
After=network.target

[Service]
Type=simple
User=deepecho
Group=deepecho
WorkingDirectory=/opt/deepecho/windsurf
Environment=DISPLAY=:0
Environment=PYTHONUNBUFFERED=1
Environment=TEAM_ROLE=LEADER
Environment=FIREFOX_PROFILE=/opt/deepecho/.mozilla/firefox/deepecho
Environment=NODE_OPTIONS=--max-old-space-size=1024
CPUQuota=80%
MemoryLimit=3G
ExecStart=/opt/deepecho/venv/bin/python main.py
Restart=always
RestartSec=10
Nice=10
LimitNOFILE=16384

[Install]
WantedBy=multi-user.target
EOF

# Create tmux session manager
tee /opt/deepecho/manage.sh << EOF
#!/bin/bash
tmux new-session -d -s deepecho
tmux rename-window -t deepecho:0 'monitor'
tmux send-keys -t deepecho:0 'python monitor.py' C-m
tmux new-window -t deepecho:1 -n 'logs'
tmux send-keys -t deepecho:1 'journalctl -u deepecho -f' C-m
tmux new-window -t deepecho:2 -n 'htop'
tmux send-keys -t deepecho:2 'htop' C-m
EOF

chmod +x /opt/deepecho/manage.sh

# Create cleanup script
tee /opt/deepecho/cleanup.sh << EOF
#!/bin/bash
# Cleanup script to run daily
find /opt/deepecho/logs -type f -mtime +7 -delete
find /tmp -type f -mtime +1 -delete
journalctl --vacuum-time=7d
EOF

chmod +x /opt/deepecho/cleanup.sh

# Add cleanup to crontab
(crontab -l 2>/dev/null; echo "0 0 * * * /opt/deepecho/cleanup.sh") | crontab -

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable deepecho
sudo systemctl start deepecho

echo "Setup complete! Deep Tree Echo is now running as a service."
echo "Management commands:"
echo "1. Start management console: tmux attach -t deepecho"
echo "2. Check status: sudo systemctl status deepecho"
echo "3. View logs: journalctl -u deepecho -f"
echo "4. Monitor resources: htop"
echo ""
echo "Resource allocation:"
echo "- CPU: Limited to 80% to leave room for system"
echo "- Memory: Limited to 3GB to prevent OOM"
echo "- Swap: 4GB configured for memory pressure"
echo ""
echo "Team Leader: Deep Tree Echo"
echo "Status: Online and Ready"
