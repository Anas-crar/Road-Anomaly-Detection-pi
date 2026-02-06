# Quick Reference Guide

## Common Commands

### Testing
```bash
# Test all components
python3 test_system.py

# Run main application
python3 main.py

# Run with custom config
python3 main.py --config my_config.yaml

# Override camera source
python3 main.py --camera 1

# Override confidence threshold
python3 main.py --confidence 0.6
```

### Service Management
```bash
# Start service
sudo systemctl start road-anomaly

# Stop service
sudo systemctl stop road-anomaly

# Restart service
sudo systemctl restart road-anomaly

# Check status
sudo systemctl status road-anomaly

# View logs
sudo journalctl -u road-anomaly -f

# Enable auto-start on boot
sudo systemctl enable road-anomaly

# Disable auto-start
sudo systemctl disable road-anomaly
```

### Monitoring
```bash
# View recent detections
ls -lht output/images/ | head -20

# View detection events
cat logs/events_$(date +%Y%m%d).json | python3 -m json.tool

# View system logs
tail -f logs/system_$(date +%Y%m%d).log

# Check CPU temperature
vcgencmd measure_temp

# Check CPU frequency
vcgencmd measure_clock arm

# Monitor system resources
htop
```

### Maintenance
```bash
# Clean old outputs
rm -rf output/clips/*
rm -rf output/images/*

# Clean logs
rm -rf logs/*

# Check disk space
df -h

# Backup detection data
tar -czf detections_backup_$(date +%Y%m%d).tar.gz output/ logs/

# Copy to another machine
scp detections_backup_*.tar.gz user@host:/path/
```

## File Locations

| Item | Location |
|------|----------|
| Main script | `main.py` |
| Configuration | `config/config.yaml` |
| Model file | `models/best.onnx` |
| Detection images | `output/images/` |
| Video clips | `output/clips/` |
| Event logs | `logs/events_*.json` |
| System logs | `logs/system_*.log` |
| Session metrics | `logs/metrics_*.json` |

## Configuration Quick Tweaks

### Increase FPS
```yaml
# In config.yaml:
model:
  input_size: [416, 416]  # Reduce from [640, 640]
camera:
  resolution: [640, 480]   # Reduce from [1280, 720]
logging:
  save_clips: false        # Disable clip saving
```

### Reduce False Positives
```yaml
# In config.yaml:
model:
  confidence_threshold: 0.6  # Increase from 0.5
alerts:
  min_detection_interval: 3  # Increase from 2
```

### Save Storage Space
```yaml
# In config.yaml:
storage:
  max_storage_gb: 5      # Reduce from 10
  cleanup_days: 3        # Reduce from 7
logging:
  save_clips: false      # Only save images
```

## Troubleshooting Quick Fixes

### Camera not working
```bash
# List video devices
ls -l /dev/video*

# Test camera
v4l2-ctl --list-devices

# Try different source in config.yaml
camera:
  source: 1  # Try 0, 1, 2
```

### Low FPS
```bash
# Check CPU throttling
vcgencmd get_throttled
# 0x0 = OK, anything else = throttling

# Check temperature
vcgencmd measure_temp
# Should be < 80°C

# Reduce input size in config.yaml
```

### High Memory Usage
```bash
# Check memory
free -h

# Reduce buffer size in config.yaml
performance:
  buffer_size: 1  # Reduce from 2
```

### Service won't start
```bash
# Check service logs
sudo journalctl -u road-anomaly -n 50

# Check file permissions
ls -la main.py
chmod +x main.py

# Check Python path
which python3
```

## Performance Tuning

### For Maximum FPS
- Use quantized model
- Reduce input size to 416x416
- Disable clip saving
- Lower camera resolution
- Overclock CPU (with cooling)

### For Maximum Accuracy
- Use full precision model (FP32)
- Use 640x640 input
- Lower confidence threshold
- Process every frame
- Higher camera resolution

### For Long-term Stability
- Enable automatic cleanup
- Limit storage size
- Monitor temperature
- Use systemd service
- Enable watchdog

## Emergency Commands

### System unresponsive
```bash
# Force stop service
sudo systemctl kill -s SIGKILL road-anomaly

# Reboot
sudo reboot

# Check logs after reboot
sudo journalctl -b -u road-anomaly
```

### Disk full
```bash
# Quick cleanup
rm -rf output/clips/* output/images/*
rm -rf logs/*.log

# Check space
df -h
```

### Memory issues
```bash
# Clear cache
sudo sync
echo 3 | sudo tee /proc/sys/vm/drop_caches

# Check what's using memory
ps aux --sort=-%mem | head -10
```

## Getting Help

1. Check system logs: `logs/system_*.log`
2. Check service logs: `sudo journalctl -u road-anomaly`
3. Run test script: `python3 test_system.py`
4. Review configuration: `cat config/config.yaml`
5. Check README.md and DEPLOYMENT.md for detailed guides
