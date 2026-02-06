# Project Structure

## Complete File Organization

```
road_anomaly_detection/
│
├── main.py                      # Main application entry point (executable)
│
├── config/
│   └── config.yaml              # System configuration (YAML)
│
├── src/                         # Source code modules
│   ├── detector.py              # ONNX detector with NMS
│   ├── video_stream.py          # Threaded video capture
│   └── logger.py                # Event logging and storage
│
├── models/
│   └── best.onnx                # Trained ONNX model (7.2 MB)
│
├── logs/                        # Log files (auto-created)
│   ├── events_YYYYMMDD.json     # Detection events
│   ├── system_YYYYMMDD.log      # System logs
│   └── metrics_YYYYMMDD.json    # Performance metrics
│
├── output/                      # Detection outputs (auto-created)
│   ├── clips/                   # Video clips of detections
│   └── images/                  # Detection frame images
│
├── requirements.txt             # Python dependencies
│
├── test_system.py              # Component testing script (executable)
├── quantize_model.py           # Model quantization utility (executable)
│
├── install_rpi.sh              # Raspberry Pi installation script (executable)
├── setup_service.sh            # Systemd service setup (executable)
│
├── README.md                   # Main documentation
├── DEPLOYMENT.md               # Deployment guide for Raspberry Pi
├── QUICKREF.md                 # Quick reference for common commands
├── REPORT_TEMPLATE.md          # Project report template
│
└── .gitignore                  # Git ignore rules

```

## File Descriptions

### Core Application Files

**main.py** (11 KB)
- Application entry point
- Orchestrates all components
- Handles configuration and signal handling
- Main processing loop

**config/config.yaml** (1.3 KB)
- YAML configuration file
- Camera, model, performance, logging settings
- Easily customizable without code changes

### Source Modules

**src/detector.py** (9.6 KB)
- ONNX Runtime inference engine
- Image preprocessing pipeline
- Non-Maximum Suppression (NMS)
- Bounding box drawing utilities

**src/video_stream.py** (6.9 KB)
- Threaded video capture
- Circular frame buffer
- Video writer for clips
- Low-latency streaming

**src/logger.py** (11 KB)
- Event-based logging system
- Image and video clip saving
- Automatic storage management
- Performance metrics tracking

### Model Files

**models/best.onnx** (7.2 MB)
- Your trained ONNX model
- Optimized for CPU inference
- Can be replaced with quantized version

### Utility Scripts

**test_system.py** (6.6 KB)
- Component testing suite
- Verifies all dependencies
- Tests camera, model, inference
- Validates entire pipeline

**quantize_model.py** (4.7 KB)
- ONNX model quantization utility
- Converts FP32 to INT8
- Reduces model size and increases speed

**install_rpi.sh** (2.0 KB)
- Automated installation for Raspberry Pi
- Installs system dependencies
- Sets up Python packages
- Verifies setup

**setup_service.sh** (1.7 KB)
- Creates systemd service
- Enables auto-start on boot
- Manages service lifecycle

### Documentation

**README.md** (8.6 KB)
- Project overview and features
- Installation instructions
- Usage examples
- Performance optimization tips

**DEPLOYMENT.md** (7.8 KB)
- Step-by-step deployment guide
- Raspberry Pi configuration
- Performance tuning
- Troubleshooting

**QUICKREF.md** (4.4 KB)
- Quick command reference
- Common tasks
- Emergency procedures
- Configuration tweaks

**REPORT_TEMPLATE.md** (10.6 KB)
- Project report template
- Methodology documentation
- Results and analysis sections
- Ready to fill in your data

## Dependencies

### Python Packages (requirements.txt)

- **numpy** - Numerical computations
- **opencv-python** - Computer vision and video I/O
- **onnxruntime** - ONNX model inference (CPU)
- **PyYAML** - Configuration file parsing
- **python-dateutil** - Date/time handling
- **psutil** - System resource monitoring

### System Dependencies (Raspberry Pi)

- Python 3.8+
- OpenCV 4.5+
- ATLAS/OpenBLAS (for NumPy)
- Video4Linux (for camera)
- FFmpeg (for video encoding)

## Data Flow

```
Camera → Video Stream → Detector → Logger → Storage
   ↓           ↓           ↓          ↓         ↓
  USB      Threading   ONNX RT   Events    Files
Device     Buffer      CPU       JSON      (Images/
                       Inference           Videos)
```

## Storage Structure

### Logs Directory
- `events_20260206.json` - Daily event log (JSON)
- `system_20260206.log` - Daily system log (text)
- `metrics_20260206_153045.json` - Session metrics

### Output Directory
- `images/20260206_153045_123456.jpg` - Detection snapshots
- `clips/20260206_153045_123456.mp4` - Video clips

## File Sizes (Approximate)

| Component | Size |
|-----------|------|
| Source code | ~30 KB |
| Configuration | ~1.5 KB |
| Model (FP32) | ~7.2 MB |
| Model (INT8) | ~1.8 MB |
| Documentation | ~32 KB |
| Scripts | ~15 KB |
| **Total (minimal)** | **~8 MB** |

## Execution Flow

1. **Initialization**
   - Load configuration
   - Initialize detector with ONNX model
   - Start video stream
   - Setup logger

2. **Main Loop**
   - Read frame from video stream
   - Preprocess image
   - Run ONNX inference
   - Postprocess detections (NMS)
   - Log anomalies if detected
   - Update metrics

3. **Shutdown**
   - Stop video stream
   - Save final metrics
   - Print summary
   - Clean up resources

## Customization Points

### Easy to Modify

1. **Detection classes** - Edit `config.yaml`
2. **Confidence threshold** - Edit `config.yaml`
3. **Camera settings** - Edit `config.yaml`
4. **Storage limits** - Edit `config.yaml`

### Moderate Difficulty

1. **Model architecture** - Replace ONNX file, update detector.py
2. **Preprocessing** - Modify `detector.py` preprocessing
3. **Postprocessing** - Modify NMS or filtering logic
4. **Alert system** - Add new alert methods in `logger.py`

### Advanced

1. **Multi-camera support** - Extend `video_stream.py`
2. **Real-time streaming** - Add RTSP/WebRTC support
3. **Cloud integration** - Add upload functionality
4. **Hardware acceleration** - Add TensorRT/OpenVINO support

## Resource Usage

### Memory
- Base system: ~500 MB
- Application: ~300-500 MB
- Total: ~800-1000 MB (safe for 4GB Pi)

### CPU
- Single inference: ~180-250 ms (CPU only)
- Target FPS: 5 FPS = 200 ms/frame
- Average usage: 50-70%

### Disk
- Model: ~7 MB (FP32) or ~2 MB (INT8)
- Per detection: ~500 KB (image) + ~5 MB (5s clip)
- Daily (100 detections): ~550 MB
- Weekly: ~4 GB (with auto-cleanup)

## Next Steps

1. **Development**: Test on your Arch Linux laptop
2. **Optimization**: Quantize model if needed
3. **Deployment**: Transfer to Raspberry Pi
4. **Testing**: Run for 24 hours
5. **Tuning**: Adjust thresholds based on results
6. **Production**: Setup as systemd service

## Support and Maintenance

- Logs automatically rotate daily
- Old files cleaned up based on config
- Metrics saved per session
- Systemd manages restarts
- All operations logged for debugging
