# Deployment Guide - Raspberry Pi 4

Complete guide to deploy the Road Anomaly Detection System on Raspberry Pi 4.

## Pre-Deployment Checklist

### Hardware
- [ ] Raspberry Pi 4 (4GB or 8GB RAM)
- [ ] High-speed microSD card (32GB+, UHS-I, A2 rated)
- [ ] USB camera or Pi Camera Module v2
- [ ] Official Raspberry Pi power supply (5V 3A)
- [ ] (Optional) Active cooling case

### Software Preparation
- [ ] Flash Raspberry Pi OS (64-bit) to microSD
- [ ] Enable SSH for headless access
- [ ] Configure WiFi (if needed)
- [ ] Update system packages

## Step-by-Step Deployment

### 1. Initial Setup on Development Machine (Arch Linux)

```bash
# Test the system on your development machine first
cd road_anomaly_detection
python test_system.py

# Test with a video file (if you have one)
# Update config.yaml: camera.source to video file path
python main.py

# Press Ctrl+C after confirming it works
```

### 2. Optimize the Model (Optional but Recommended)

```bash
# Quantize the model for better performance
python quantize_model.py models/best.onnx

# This creates models/best_quantized.onnx
# Update config.yaml to use the quantized model
```

### 3. Prepare Raspberry Pi

```bash
# Flash Raspberry Pi OS (64-bit) using Raspberry Pi Imager
# Enable SSH and configure WiFi in imager settings

# Boot the Raspberry Pi and SSH into it
ssh pi@raspberrypi.local
# Default password: raspberry (change this!)

# Update system
sudo apt update && sudo apt full-upgrade -y

# Enable camera (if using Pi Camera Module)
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable

# Reboot
sudo reboot
```

### 4. Transfer Project to Raspberry Pi

From your development machine:

```bash
# Create archive (excluding unnecessary files)
cd road_anomaly_detection
tar -czf road_anomaly_detection.tar.gz \
    --exclude='logs/*' \
    --exclude='output/*' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    .

# Transfer to Raspberry Pi
scp road_anomaly_detection.tar.gz pi@raspberrypi.local:~/

# SSH to Raspberry Pi
ssh pi@raspberrypi.local

# Extract
tar -xzf road_anomaly_detection.tar.gz
cd road_anomaly_detection
```

### 5. Install Dependencies on Raspberry Pi

```bash
# Run installation script
bash install_rpi.sh

# This will install all required packages
# Takes 10-20 minutes depending on internet speed
```

### 6. Configure for Your Setup

```bash
# Edit configuration
nano config/config.yaml

# Key settings to verify:
# - camera.source (0 for USB, check with 'ls /dev/video*')
# - model.path (ensure it points to your model)
# - model.confidence_threshold (adjust based on testing)
# - performance.target_fps (start with 5)
```

### 7. Test the System

```bash
# Run component tests
python3 test_system.py

# If all tests pass, run the main application
python3 main.py

# Monitor the output
# You should see FPS, frame count, and detection stats
# Press Ctrl+C to stop
```

### 8. Setup as System Service (Recommended)

```bash
# Setup systemd service for automatic startup
sudo bash setup_service.sh

# Answer 'y' when prompted to enable and start

# Check service status
sudo systemctl status road-anomaly

# View live logs
sudo journalctl -u road-anomaly -f
```

### 9. Performance Optimization

#### A. Enable 64-bit Kernel
```bash
# Edit config
sudo nano /boot/config.txt

# Add at the end:
arm_64bit=1

# Reboot
sudo reboot
```

#### B. Overclock (Optional, if you have good cooling)
```bash
sudo nano /boot/config.txt

# Add these lines (moderate overclock):
over_voltage=2
arm_freq=1800

# For aggressive overclock (requires active cooling):
# over_voltage=6
# arm_freq=2000

# Reboot
sudo reboot
```

#### C. Increase GPU Memory
```bash
sudo nano /boot/config.txt

# Add:
gpu_mem=256

# Reboot
sudo reboot
```

#### D. Disable Desktop Environment
```bash
# Switch to console mode
sudo systemctl set-default multi-user.target

# Reboot
sudo reboot

# To re-enable desktop later:
# sudo systemctl set-default graphical.target
```

#### E. Increase Swap Size
```bash
# Edit swap config
sudo nano /etc/dphys-swapfile

# Change CONF_SWAPSIZE to 2048
CONF_SWAPSIZE=2048

# Restart swap
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 10. Monitoring and Maintenance

#### View Logs
```bash
# System logs
tail -f logs/system_$(date +%Y%m%d).log

# Event logs
cat logs/events_$(date +%Y%m%d).json | python3 -m json.tool

# Service logs
sudo journalctl -u road-anomaly -f
```

#### Check Performance
```bash
# CPU temperature
vcgencmd measure_temp

# CPU frequency
vcgencmd measure_clock arm

# Memory usage
free -h

# Disk usage
df -h
```

#### Access Detection Results
```bash
# List recent detections
ls -lht output/images/ | head -20

# List video clips
ls -lht output/clips/ | head -10

# Copy files from Pi to your computer
# From your computer:
scp -r pi@raspberrypi.local:~/road_anomaly_detection/output ./
```

## Troubleshooting

### Camera Issues

**Camera not detected:**
```bash
# Check for video devices
ls -l /dev/video*

# For USB camera, try different sources:
v4l2-ctl --list-devices

# For Pi Camera, ensure it's enabled:
vcgencmd get_camera
# Should show: supported=1 detected=1
```

**Camera permissions:**
```bash
# Add user to video group
sudo usermod -a -G video pi

# Logout and login again
```

### Performance Issues

**Low FPS (<3):**
- Reduce camera resolution in config.yaml
- Use quantized model
- Lower confidence threshold
- Disable clip saving temporarily
- Check CPU temperature (throttling if >80°C)

**High CPU usage:**
```bash
# Monitor CPU
htop

# Check if other services are running
systemctl list-units --type=service --state=running

# Stop unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups
```

**Memory issues:**
```bash
# Check memory
free -h

# Kill memory-intensive processes
sudo systemctl stop packagekit
sudo systemctl disable packagekit
```

### Storage Issues

**Disk full:**
```bash
# Check disk usage
df -h

# Clean old logs and outputs
cd ~/road_anomaly_detection
rm -rf logs/*
rm -rf output/clips/*
rm -rf output/images/*

# Or adjust config.yaml:
# storage.max_storage_gb: 5
# storage.cleanup_days: 3
```

## Production Recommendations

1. **Use a UPS** - Prevents corruption from power failures
2. **Enable Watchdog** - Auto-reboot if system hangs
3. **Setup Log Rotation** - Prevent logs from filling disk
4. **Regular Backups** - Backup detection data weekly
5. **Monitor Temperature** - Ensure adequate cooling
6. **Network Upload** - Sync detections to cloud/server

## Security Considerations

```bash
# Change default password
passwd

# Update SSH configuration
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication yes (or use keys)

# Setup firewall
sudo apt install ufw
sudo ufw allow ssh
sudo ufw enable

# Keep system updated
sudo apt update && sudo apt upgrade -y
```

## Next Steps

After successful deployment:

1. Run for 24 hours and monitor performance
2. Review detection logs for false positives
3. Adjust confidence thresholds if needed
4. Consider adding remote monitoring
5. Document any hardware-specific issues
6. Create backup of working configuration

## Support

For issues specific to:
- **Hardware**: Check Raspberry Pi forums
- **ONNX Runtime**: Check ONNX Runtime GitHub
- **OpenCV**: Check OpenCV documentation
- **General**: Review logs and error messages

## Performance Expectations

Typical performance on Raspberry Pi 4 (4GB):

| Configuration | FPS | Latency | CPU Usage |
|--------------|-----|---------|-----------|
| 640x640, FP32 | 3-5 | 200-300ms | 60-80% |
| 640x640, INT8 | 5-8 | 125-200ms | 50-70% |
| 416x416, INT8 | 8-12 | 80-125ms | 40-60% |

These are approximate values and may vary based on model complexity and scene content.
