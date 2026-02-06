"""
Logging System for Road Anomaly Detection
Handles event logging, clip saving, and storage management
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import cv2
from pathlib import Path
import shutil


class AnomalyLogger:
    """Logger for road anomaly events"""
    
    def __init__(self, logs_dir: str = "logs", clips_dir: str = "output/clips",
                 images_dir: str = "output/images", max_storage_gb: float = 10.0,
                 cleanup_days: int = 7, log_level: str = "INFO"):
        """
        Initialize anomaly logger
        
        Args:
            logs_dir: Directory for log files
            clips_dir: Directory for video clips
            images_dir: Directory for detection images
            max_storage_gb: Maximum storage in GB
            cleanup_days: Delete files older than this many days
            log_level: Logging level
        """
        self.logs_dir = Path(logs_dir)
        self.clips_dir = Path(clips_dir)
        self.images_dir = Path(images_dir)
        self.max_storage_bytes = max_storage_gb * 1024 * 1024 * 1024
        self.cleanup_days = cleanup_days
        
        # Create directories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging(log_level)
        
        # Event log file (JSON format)
        self.event_log_path = self.logs_dir / f"events_{datetime.now().strftime('%Y%m%d')}.json"
        self.events = []
        
        # Load existing events if file exists
        if self.event_log_path.exists():
            try:
                with open(self.event_log_path, 'r') as f:
                    self.events = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load existing events: {e}")
                self.events = []
        
        # Performance metrics
        self.metrics = {
            'total_frames': 0,
            'total_detections': 0,
            'total_inference_time': 0.0,
            'session_start': datetime.now().isoformat()
        }
        
        logging.info("AnomalyLogger initialized")
    
    def setup_logging(self, log_level: str):
        """Setup Python logging"""
        log_file = self.logs_dir / f"system_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def log_detection(self, detections: List[Dict], frame: cv2.Mat, 
                     inference_time: float, save_clip: bool = False,
                     pre_frames: List[cv2.Mat] = None, 
                     post_frames: List[cv2.Mat] = None) -> Optional[str]:
        """
        Log a detection event
        
        Args:
            detections: List of detections
            frame: Current frame
            inference_time: Inference time in seconds
            save_clip: Whether to save video clip
            pre_frames: Frames before detection
            post_frames: Frames after detection
            
        Returns:
            Event ID if logged, None otherwise
        """
        if not detections:
            return None
        
        timestamp = datetime.now()
        event_id = timestamp.strftime('%Y%m%d_%H%M%S_%f')
        
        # Create event record
        event = {
            'event_id': event_id,
            'timestamp': timestamp.isoformat(),
            'detections': [{
                'class': d['class'],
                'confidence': d['confidence'],
                'bbox': d['bbox']
            } for d in detections],
            'inference_time': inference_time,
            'frame_saved': False,
            'clip_saved': False
        }
        
        # Save frame image
        try:
            image_path = self.images_dir / f"{event_id}.jpg"
            cv2.imwrite(str(image_path), frame)
            event['image_path'] = str(image_path.relative_to(Path.cwd()))
            event['frame_saved'] = True
            logging.info(f"Saved detection image: {image_path}")
        except Exception as e:
            logging.error(f"Failed to save image: {e}")
        
        # Save video clip if requested
        if save_clip and pre_frames and post_frames:
            try:
                clip_path = self.save_clip(event_id, pre_frames, frame, post_frames)
                event['clip_path'] = str(clip_path.relative_to(Path.cwd()))
                event['clip_saved'] = True
                logging.info(f"Saved video clip: {clip_path}")
            except Exception as e:
                logging.error(f"Failed to save clip: {e}")
        
        # Add to events list
        self.events.append(event)
        
        # Save events to file
        self._save_events()
        
        # Log to console
        detection_summary = ", ".join([f"{d['class']}({d['confidence']:.2f})" for d in detections])
        logging.info(f"ANOMALY DETECTED [{event_id}]: {detection_summary}")
        
        # Update metrics
        self.metrics['total_detections'] += len(detections)
        
        # Cleanup old files
        self._cleanup_storage()
        
        return event_id
    
    def save_clip(self, event_id: str, pre_frames: List[cv2.Mat], 
                 current_frame: cv2.Mat, post_frames: List[cv2.Mat]) -> Path:
        """
        Save video clip with pre and post detection frames
        
        Args:
            event_id: Event identifier
            pre_frames: Frames before detection
            current_frame: Frame with detection
            post_frames: Frames after detection
            
        Returns:
            Path to saved clip
        """
        clip_path = self.clips_dir / f"{event_id}.mp4"
        
        # Combine all frames
        all_frames = pre_frames + [current_frame] + post_frames
        
        if not all_frames:
            raise ValueError("No frames to save")
        
        # Get frame dimensions
        h, w = all_frames[0].shape[:2]
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30  # Assume 30 fps for playback
        writer = cv2.VideoWriter(str(clip_path), fourcc, fps, (w, h))
        
        # Write frames
        for frame in all_frames:
            writer.write(frame)
        
        writer.release()
        
        return clip_path
    
    def update_metrics(self, inference_time: float):
        """Update performance metrics"""
        self.metrics['total_frames'] += 1
        self.metrics['total_inference_time'] += inference_time
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        metrics = self.metrics.copy()
        
        if metrics['total_frames'] > 0:
            metrics['avg_inference_time'] = metrics['total_inference_time'] / metrics['total_frames']
            metrics['avg_fps'] = 1.0 / metrics['avg_inference_time'] if metrics['avg_inference_time'] > 0 else 0
        else:
            metrics['avg_inference_time'] = 0
            metrics['avg_fps'] = 0
        
        metrics['total_events'] = len(self.events)
        
        return metrics
    
    def _save_events(self):
        """Save events to JSON file"""
        try:
            with open(self.event_log_path, 'w') as f:
                json.dump(self.events, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save events: {e}")
    
    def _cleanup_storage(self):
        """Cleanup old files based on age and storage limit"""
        try:
            # Remove files older than cleanup_days
            cutoff_date = datetime.now() - timedelta(days=self.cleanup_days)
            
            for directory in [self.clips_dir, self.images_dir]:
                for file_path in directory.glob('*'):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date:
                            file_path.unlink()
                            logging.info(f"Deleted old file: {file_path}")
            
            # Check total storage
            total_size = self._get_directory_size(self.clips_dir) + \
                        self._get_directory_size(self.images_dir)
            
            if total_size > self.max_storage_bytes:
                logging.warning(f"Storage limit exceeded: {total_size / 1024 / 1024 / 1024:.2f} GB")
                self._remove_oldest_files(total_size - self.max_storage_bytes)
        
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
    
    def _get_directory_size(self, directory: Path) -> int:
        """Get total size of directory in bytes"""
        total = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total
    
    def _remove_oldest_files(self, bytes_to_free: int):
        """Remove oldest files until enough space is freed"""
        all_files = []
        
        for directory in [self.clips_dir, self.images_dir]:
            for file_path in directory.glob('*'):
                if file_path.is_file():
                    all_files.append((file_path, file_path.stat().st_mtime))
        
        # Sort by modification time (oldest first)
        all_files.sort(key=lambda x: x[1])
        
        freed = 0
        for file_path, _ in all_files:
            if freed >= bytes_to_free:
                break
            
            size = file_path.stat().st_size
            file_path.unlink()
            freed += size
            logging.info(f"Deleted file to free space: {file_path}")
    
    def save_session_metrics(self):
        """Save session metrics to file"""
        metrics_path = self.logs_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(metrics_path, 'w') as f:
                json.dump(self.get_metrics(), f, indent=2)
            logging.info(f"Session metrics saved to {metrics_path}")
        except Exception as e:
            logging.error(f"Failed to save metrics: {e}")
    
    def print_summary(self):
        """Print detection summary"""
        metrics = self.get_metrics()
        
        print("\n" + "="*50)
        print("SESSION SUMMARY")
        print("="*50)
        print(f"Total Frames Processed: {metrics['total_frames']}")
        print(f"Total Anomalies Detected: {metrics['total_events']}")
        print(f"Average Inference Time: {metrics['avg_inference_time']*1000:.2f} ms")
        print(f"Average FPS: {metrics['avg_fps']:.2f}")
        print("="*50 + "\n")
