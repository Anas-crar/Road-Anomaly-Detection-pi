#!/usr/bin/env python3
"""
Test script for Road Anomaly Detection System
Tests individual components before full deployment
"""

import sys
from pathlib import Path
import numpy as np
import cv2

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import onnxruntime as ort
        print(f"✓ ONNX Runtime {ort.__version__}")
        print(f"  Available providers: {ort.get_available_providers()}")
    except ImportError as e:
        print(f"✗ ONNX Runtime import failed: {e}")
        return False
    
    try:
        import yaml
        print(f"✓ PyYAML")
    except ImportError as e:
        print(f"✗ PyYAML import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✓ NumPy {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    return True


def test_camera():
    """Test camera access"""
    print("\nTesting camera access...")
    
    camera_sources = [0, 1, 2]
    found = False
    
    for source in camera_sources:
        try:
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✓ Camera found at source {source}")
                    print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
                    cap.release()
                    found = True
                    break
                else:
                    cap.release()
        except Exception as e:
            pass
    
    if not found:
        print("✗ No camera found")
        print("  Try: ls /dev/video*")
    
    return found


def test_model():
    """Test model loading"""
    print("\nTesting model loading...")
    
    model_path = Path("models/best.onnx")
    
    if not model_path.exists():
        print(f"✗ Model not found at {model_path}")
        return False
    
    try:
        import onnxruntime as ort
        
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        session = ort.InferenceSession(str(model_path), sess_options)
        
        print(f"✓ Model loaded successfully")
        print(f"  Input name: {session.get_inputs()[0].name}")
        print(f"  Input shape: {session.get_inputs()[0].shape}")
        print(f"  Output names: {[o.name for o in session.get_outputs()]}")
        
        return True
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False


def test_inference():
    """Test model inference"""
    print("\nTesting model inference...")
    
    try:
        from detector import AnomalyDetector
        
        detector = AnomalyDetector(
            model_path="models/best.onnx",
            confidence_threshold=0.5
        )
        print("Detector input size:", detector.input_size)
        
        # Create dummy image
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Run inference
        detections, inference_time = detector.detect(dummy_image)
        
        print(f"✓ Inference successful")
        print(f"  Inference time: {inference_time*1000:.2f}ms")
        print(f"  Detections: {len(detections)}")
        
        return True
    except Exception as e:
        print(f"✗ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_stream():
    """Test video stream"""
    print("\nTesting video stream...")
    
    try:
        from video_stream import VideoStream
        
        vs = VideoStream(src=0).start()
        
        # Try to read a few frames
        success_count = 0
        for i in range(5):
            ret, frame = vs.read()
            if ret and frame is not None:
                success_count += 1
        
        vs.stop()
        
        if success_count >= 3:
            print(f"✓ Video stream working ({success_count}/5 frames)")
            return True
        else:
            print(f"✗ Video stream unstable ({success_count}/5 frames)")
            return False
    except Exception as e:
        print(f"✗ Video stream failed: {e}")
        return False


def test_logger():
    """Test logger"""
    print("\nTesting logger...")
    
    try:
        from logger import AnomalyLogger
        
        logger = AnomalyLogger(
            logs_dir="logs",
            clips_dir="output/clips",
            images_dir="output/images"
        )
        
        # Test logging a dummy detection
        dummy_detection = [{
            'class': 'test',
            'confidence': 0.99,
            'bbox': [100, 100, 200, 200]
        }]
        
        dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        event_id = logger.log_detection(
            detections=dummy_detection,
            frame=dummy_frame,
            inference_time=0.1,
            save_clip=False
        )
        
        if event_id:
            print(f"✓ Logger working (event: {event_id})")
            return True
        else:
            print("✗ Logger failed to create event")
            return False
    except Exception as e:
        print(f"✗ Logger failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("Road Anomaly Detection System - Component Tests")
    print("="*60)
    
    results = {
        'Imports': test_imports(),
        'Camera': test_camera(),
        'Model': test_model(),
        'Inference': test_inference(),
        'Video Stream': test_video_stream(),
        'Logger': test_logger()
    }
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} {status}")
    
    print("="*60)
    
    if all(results.values()):
        print("\n✓ All tests passed! System is ready.")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
