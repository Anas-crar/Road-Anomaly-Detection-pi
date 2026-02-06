#!/bin/bash

# Installation script for Road Anomaly Detection System on Raspberry Pi
# Run with: bash install_rpi.sh

set -e

echo "=================================="
echo "Road Anomaly Detection Setup"
echo "=================================="
echo ""

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "Detected: $MODEL"
else
    echo "Warning: Not detected as Raspberry Pi"
fi

echo ""
echo "Step 1: Updating system..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-opencv \
    python3-yaml \
    libatlas-base-dev \
    libopenblas-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libharfbuzz0b \
    libwebp-dev \
    libjasper-dev \
    libilmbase-dev \
    libopenexr-dev \
    libgstreamer1.0-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev

echo ""
echo "Step 3: Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Step 4: Setting up directories..."
mkdir -p logs output/clips output/images

echo ""
echo "Step 5: Testing camera access..."
if ls /dev/video* 1> /dev/null 2>&1; then
    echo "Camera devices found:"
    ls -l /dev/video*
else
    echo "Warning: No camera devices detected"
    echo "Please connect your USB camera or enable the Pi Camera"
fi

echo ""
echo "Step 6: Checking model file..."
if [ -f "models/best.onnx" ]; then
    echo "Model file found: models/best.onnx"
else
    echo "Warning: Model file not found at models/best.onnx"
    echo "Please copy your trained model to this location"
fi

echo ""
echo "=================================="
echo "Installation complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Verify configuration in config/config.yaml"
echo "2. Test the system: python3 main.py"
echo "3. To run as a service, use: sudo bash setup_service.sh"
echo ""
