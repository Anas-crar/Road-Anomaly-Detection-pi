#!/bin/bash

# Setup systemd service for Road Anomaly Detection
# Run with: sudo bash setup_service.sh

set -e

SERVICE_NAME="road-anomaly"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
WORK_DIR=$(pwd)
USER=$(whoami)

echo "=================================="
echo "Setting up systemd service"
echo "=================================="
echo ""
echo "Service name: $SERVICE_NAME"
echo "Working directory: $WORK_DIR"
echo "User: $USER"
echo ""

# Create service file
cat > /tmp/${SERVICE_NAME}.service << EOF
[Unit]
Description=Road Anomaly Detection Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
ExecStart=/usr/bin/python3 $WORK_DIR/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Move service file to systemd directory
sudo mv /tmp/${SERVICE_NAME}.service $SERVICE_FILE

# Reload systemd
sudo systemctl daemon-reload

echo "Service file created: $SERVICE_FILE"
echo ""
echo "To control the service:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Enable:  sudo systemctl enable $SERVICE_NAME  (auto-start on boot)"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""

read -p "Do you want to enable and start the service now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    echo ""
    echo "Service enabled and started!"
    echo "Checking status..."
    sleep 2
    sudo systemctl status $SERVICE_NAME
fi
