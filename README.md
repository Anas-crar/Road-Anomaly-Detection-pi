# Road Anomaly Detection System

Real-time road anomaly detection system for Raspberry Pi 4 using ONNX Runtime and OpenCV.

## Features

- **Real-time Detection**: Detects potholes, obstacles, cracks, and bumps at ≥5 FPS
- **Headless Operation**: Runs without display, perfect for embedded deployment
- **Automatic Logging**: Saves detection events with timestamps, images, and video clips
- **Optimized for Edge**: CPU-only inference with threading and buffering
- **Smart Storage Management**: Automatic cleanup based on age and storage limits
- **Low False Positives**: Configurable confidence thresholds and detection intervals

## Project Structure

```
road_anomaly_detection/
├── main.py                 # Main application entry point
├── config/
│   └── config.yaml         # Configuration file
├── src/
│   ├── detector.py         # ONNX detector implementation
│   ├── video_stream.py     # Threaded video capture
│   └── logger.py           # Event logging and storage management
├── models/
│   └── best.onnx           # Trained ONNX model
├── logs/                   # System and event logs
├── output/
│   ├── clips/              # Video clips of detections
│   └── images/             # Detection frame snapshots
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Hardware Requirements

- **Raspberry Pi 4** (4GB or 8GB RAM recommended)
- **USB Camera** or **Raspberry Pi Camera Module v2**
- **High-speed microSD card** (UHS-I, A2 rated, ≥32GB)
- **Power supply** (Official 5V 3A recommended)

## Software Requirements

- **OS**: Raspberry Pi OS (64-bit recommended) or Arch Linux ARM
- **Python**: 3.8 or higher
- **OpenCV**: 4.5.0 or higher
- **ONNX Runtime**: 1.12.0 or higher

## Installation

### On Arch Linux (Development)

```bash
# Install system dependencies
sudo pacman -S python python-pip opencv python-yaml

# Install Python dependencies
pip install -r requirements.txt
```

### On Raspberry Pi OS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-opencv python3-yaml libatlas-base-dev

# Install Python dependencies
pip3 install -r requirements.txt

# Optional: Install optimized ONNX Runtime for ARM
pip3 install onnxruntime
```

## Configuration

Edit `config/config.yaml` to customize the system:

### Key Settings

```yaml
model:
  confidence_threshold: 0.5    # Detection confidence threshold
  input_size: [640, 640]       # Model input size

camera:
  source: 0                    # Camera device (0 for USB, 1 for CSI)
  resolution: [1280, 720]      # Camera resolution
  fps: 30                      # Camera FPS

performance:
  target_fps: 5                # Processing target FPS
  buffer_size: 2               # Frame buffer size

logging:
  save_clips: true             # Save video clips
  save_images: true            # Save detection images
  clip_duration: 5             # Seconds of video around detection

storage:
  max_storage_gb: 10           # Maximum storage for outputs
  cleanup_days: 7              # Delete files older than this
```

## Usage

### Basic Usage

```bash
# Run with default config
python3 main.py

# Specify custom config
python3 main.py --config /path/to/config.yaml

# Override camera source
python3 main.py --camera 0

# Override confidence threshold
python3 main.py --confidence 0.6
```

### Running as a Service (Raspberry Pi)

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/road-anomaly.service
```

Add the following content:

```ini
[Unit]
Description=Road Anomaly Detection Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/road_anomaly_detection
ExecStart=/usr/bin/python3 /home/pi/road_anomaly_detection/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable road-anomaly.service
sudo systemctl start road-anomaly.service

# Check status
sudo systemctl status road-anomaly.service

# View logs
sudo journalctl -u road-anomaly.service -f
```

## Model Information

### Supported Model Formats

- **ONNX** (.onnx) - Recommended for cross-platform compatibility
- Trained with YOLOv5, YOLOv8, or similar object detectors

### Model Input/Output

The system expects models with:
- **Input**: RGB image tensor [1, 3, H, W] normalized to [0, 1]
- **Output**: Detection results in YOLO format
  - YOLOv5: [batch, num_detections, 5+num_classes]
  - YOLOv8: [batch, num_detections, 6]

### Quantization (Optional)

For better performance on Raspberry Pi, quantize your model to INT8:

```python
# Example quantization script (quantize_model.py)
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

model_fp32 = 'models/best.onnx'
model_quant = 'models/best_quantized.onnx'

quantize_dynamic(
    model_fp32,
    model_quant,
    weight_type=QuantType.QUInt8
)
```

## Output Files

### Event Logs

JSON log files in `logs/` directory:

```json
{
  "event_id": "20260206_143022_123456",
  "timestamp": "2026-02-06T14:30:22.123456",
  "detections": [
    {
      "class": "pothole",
      "confidence": 0.87,
      "bbox": [245, 389, 312, 445]
    }
  ],
  "inference_time": 0.185,
  "image_path": "output/images/20260206_143022_123456.jpg",
  "clip_path": "output/clips/20260206_143022_123456.mp4"
}
```

### System Logs

Text logs in `logs/system_YYYYMMDD.log`:
- System status
- Performance metrics
- Error messages

### Metrics

Session metrics in `logs/metrics_YYYYMMDD_HHMMSS.json`:
- Total frames processed
- Total detections
- Average FPS
- Average inference time

## Performance Optimization

### Raspberry Pi 4 Specific

1. **Enable 64-bit OS**: Better performance with ARM64 architecture
2. **Overclock**: Safely overclock CPU to 2.0 GHz (add to `/boot/config.txt`):
   ```
   over_voltage=6
   arm_freq=2000
   ```
3. **Increase GPU memory**: Allocate 256MB to GPU (in `/boot/config.txt`):
   ```
   gpu_mem=256
   ```
4. **Disable Desktop**: Use headless mode to free resources
5. **Use SWAP**: Increase swap to 2GB for stability

### Software Optimizations

- **Model Quantization**: Convert to INT8 for 2-4x speedup
- **Lower Resolution**: Reduce camera resolution to 640x480
- **Frame Skipping**: Process every 2nd or 3rd frame
- **Batch Size**: Keep at 1 for lowest latency
- **Threading**: Enabled by default for camera I/O

## Testing

### Test with Video File

```bash
# Modify config.yaml
camera:
  source: "/path/to/test_video.mp4"

# Run detection
python3 main.py
```

### Benchmark Performance

```bash
# Run for 100 frames and check metrics
python3 main.py
# Press Ctrl+C after ~20 seconds
# Check logs/metrics_*.json for average FPS
```

## Troubleshooting

### Common Issues

**Low FPS (< 3 FPS)**
- Reduce input resolution in config
- Enable model quantization
- Reduce confidence threshold
- Disable clip saving

**High False Positives**
- Increase confidence threshold (0.6-0.7)
- Increase min_detection_interval
- Retrain model with more diverse data

**Camera Not Detected**
- Check camera connection: `ls /dev/video*`
- Try different source values (0, 1, 2)
- For Pi Camera: Enable legacy camera with `raspi-config`

**Out of Memory**
- Reduce buffer_size
- Disable clip saving
- Use quantized model
- Reduce camera resolution

**Storage Full**
- Reduce max_storage_gb
- Reduce cleanup_days
- Disable clip saving

## Development

### Code Structure

- **detector.py**: ONNX inference and NMS
- **video_stream.py**: Threaded camera capture with buffering
- **logger.py**: Event logging and storage management
- **main.py**: Main application loop and coordination

### Adding New Features

To add a new anomaly class:
1. Retrain model with new class
2. Update `detection.classes` in config.yaml
3. Optionally add color mapping in `detector.py`

## Performance Targets

- **FPS**: ≥5 FPS with 640x640 input
- **Latency**: <200ms per frame
- **Precision**: >0.8 on validation set
- **Memory**: <1.5GB RAM usage

## License

This project is for educational purposes as part of the Raspberry Pi edge AI challenge.

## References

- [ONNX Runtime Documentation](https://onnxruntime.ai/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [YOLOv5 Documentation](https://docs.ultralytics.com/)

## Contact

For issues and questions, please refer to the project documentation or create an issue in the repository.
