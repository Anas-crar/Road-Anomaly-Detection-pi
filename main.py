#!/usr/bin/env python3
"""
Road Anomaly Detection System - Main Application
Headless mode for Raspberry Pi 4 deployment
"""

import sys
import signal
import time
import yaml
from pathlib import Path
import cv2
import logging
from typing import Dict, List
import argparse

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from detector import AnomalyDetector
from video_stream import VideoStream, CircularFrameBuffer
from logger import AnomalyLogger


class RoadAnomalyDetectionSystem:
    """Main application class for road anomaly detection"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the detection system
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self.load_config(config_path)
        
        # Initialize components
        self.detector = None
        self.video_stream = None
        self.logger = None
        self.circular_buffer = None
        
        # State variables
        self.running = False
        self.last_detection_time = {}  # Track last detection time per class
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("Road Anomaly Detection System initialized")
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'model': {
                'path': 'models/best.onnx',
                'input_size': [640, 640],
                'confidence_threshold': 0.5,
                'iou_threshold': 0.45
            },
            'camera': {
                'source': 0,
                'resolution': [1280, 720],
                'fps': 30
            },
            'detection': {
                'classes': ['pothole', 'obstacle', 'crack', 'bump']
            },
            'performance': {
                'target_fps': 5,
                'use_threading': True,
                'buffer_size': 2
            },
            'logging': {
                'save_clips': True,
                'save_images': True,
                'clip_duration': 5,
                'log_level': 'INFO'
            },
            'storage': {
                'logs_dir': 'logs',
                'clips_dir': 'output/clips',
                'images_dir': 'output/images',
                'max_storage_gb': 10,
                'cleanup_days': 7
            },
            'alerts': {
                'min_detection_interval': 2
            }
        }
    
    def initialize_components(self):
        """Initialize all system components"""
        print("\nInitializing components...")
        
        # Initialize detector
        print("Loading detection model...")
        self.detector = AnomalyDetector(
            model_path=self.config['model']['path'],
            input_size=tuple(self.config['model']['input_size']),
            confidence_threshold=self.config['model']['confidence_threshold'],
            iou_threshold=self.config['model']['iou_threshold'],
            class_names=self.config['detection']['classes']
        )
        
        # Initialize logger
        print("Initializing logger...")
        self.logger = AnomalyLogger(
            logs_dir=self.config['storage']['logs_dir'],
            clips_dir=self.config['storage']['clips_dir'],
            images_dir=self.config['storage']['images_dir'],
            max_storage_gb=self.config['storage']['max_storage_gb'],
            cleanup_days=self.config['storage']['cleanup_days'],
            log_level=self.config['logging']['log_level']
        )
        
        # Initialize video stream
        print("Starting video stream...")
        self.video_stream = VideoStream(
            src=self.config['camera']['source'],
            resolution=tuple(self.config['camera']['resolution']),
            fps=self.config['camera']['fps'],
            buffer_size=self.config['performance']['buffer_size']
        ).start()
        
        # Initialize circular buffer for saving clips
        if self.config['logging']['save_clips']:
            buffer_size = int(self.config['camera']['fps'] * self.config['logging']['clip_duration'])
            self.circular_buffer = CircularFrameBuffer(max_size=buffer_size)
            print(f"Circular buffer initialized with {buffer_size} frames")
        
        print("All components initialized successfully!\n")
    
    def should_log_detection(self, detections: List[Dict]) -> bool:
        """
        Check if detection should be logged based on interval
        
        Args:
            detections: List of detections
            
        Returns:
            True if should log
        """
        current_time = time.time()
        min_interval = self.config['alerts']['min_detection_interval']
        
        for det in detections:
            class_name = det['class']
            last_time = self.last_detection_time.get(class_name, 0)
            
            if current_time - last_time >= min_interval:
                self.last_detection_time[class_name] = current_time
                return True
        
        return False
    
    def process_frame(self, frame):
        """
        Process a single frame
        
        Args:
            frame: Input frame from video stream
        """
        # Run detection
        detections, inference_time = self.detector.detect(frame)
        
        # Update metrics
        self.logger.update_metrics(inference_time)
        
        # Handle detections
        if detections and self.should_log_detection(detections):
            # Prepare frames for clip
            pre_frames = None
            post_frames = []
            
            if self.config['logging']['save_clips'] and self.circular_buffer:
                pre_frames = self.circular_buffer.get_all()
            
            # Draw detections on frame
            annotated_frame = self.detector.draw_detections(frame, detections)
            
            # Log the detection
            self.logger.log_detection(
                detections=detections,
                frame=annotated_frame,
                inference_time=inference_time,
                save_clip=self.config['logging']['save_clips'],
                pre_frames=pre_frames,
                post_frames=post_frames  # Post frames will be collected separately
            )
        
        # Add frame to circular buffer
        if self.circular_buffer:
            self.circular_buffer.add(frame)
    
    def run(self):
        """Main run loop"""
        try:
            self.initialize_components()
            self.running = True
            
            print("="*60)
            print("ROAD ANOMALY DETECTION SYSTEM - RUNNING")
            print("="*60)
            print(f"Target FPS: {self.config['performance']['target_fps']}")
            print(f"Confidence Threshold: {self.config['model']['confidence_threshold']}")
            print("Press Ctrl+C to stop")
            print("="*60 + "\n")
            
            frame_count = 0
            fps_update_interval = 30
            fps_timer = time.time()
            current_fps = 0
            
            while self.running:
                # Read frame
                ret, frame = self.video_stream.read()
                
                if not ret or frame is None:
                    logging.warning("Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                # Process frame
                start_time = time.time()
                self.process_frame(frame)
                process_time = time.time() - start_time
                
                # Calculate FPS
                frame_count += 1
                if frame_count % fps_update_interval == 0:
                    elapsed = time.time() - fps_timer
                    current_fps = fps_update_interval / elapsed
                    fps_timer = time.time()
                    
                    # Print status
                    metrics = self.logger.get_metrics()
                    print(f"\rFPS: {current_fps:.2f} | "
                          f"Frames: {metrics['total_frames']} | "
                          f"Detections: {metrics['total_events']} | "
                          f"Avg Inference: {metrics.get('avg_inference_time', 0)*1000:.1f}ms",
                          end='', flush=True)
                
                # Frame rate control
                target_delay = 1.0 / self.config['performance']['target_fps']
                sleep_time = target_delay - process_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\n\nShutdown signal received...")
        except Exception as e:
            logging.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Cleanup and shutdown"""
        print("\nShutting down...")
        self.running = False
        
        # Stop video stream
        if self.video_stream:
            self.video_stream.stop()
        
        # Save final metrics
        if self.logger:
            self.logger.save_session_metrics()
            self.logger.print_summary()
        
        print("Shutdown complete")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}")
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Road Anomaly Detection System')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--camera', type=int, default=None,
                       help='Camera source (overrides config)')
    parser.add_argument('--confidence', type=float, default=None,
                       help='Confidence threshold (overrides config)')
    
    args = parser.parse_args()
    
    # Create system instance
    system = RoadAnomalyDetectionSystem(config_path=args.config)
    
    # Override config with command line arguments
    if args.camera is not None:
        system.config['camera']['source'] = args.camera
    if args.confidence is not None:
        system.config['model']['confidence_threshold'] = args.confidence
    
    # Run the system
    system.run()


if __name__ == "__main__":
    main()
