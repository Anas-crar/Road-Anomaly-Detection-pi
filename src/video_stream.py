"""
Video Stream Handler with Thread-based Buffering
Optimized for Raspberry Pi 4
"""

import cv2
import threading
import queue
from typing import Optional, Tuple
import time


class VideoStream:
    """Threaded video stream reader for better performance"""
    
    def __init__(self, src: int = 0, resolution: Tuple[int, int] = (1280, 720), 
                 fps: int = 30, buffer_size: int = 2):
        """
        Initialize video stream
        
        Args:
            src: Camera source (0 for USB camera) or video file path
            resolution: Desired resolution (width, height)
            fps: Target FPS
            buffer_size: Size of frame buffer
        """
        self.src = src
        self.resolution = resolution
        self.fps = fps
        self.buffer_size = buffer_size
        
        self.stream = None
        self.frame_queue = queue.Queue(maxsize=buffer_size)
        self.stopped = False
        self.thread = None
        
    def start(self) -> 'VideoStream':
        """Start the video stream"""
        print(f"Starting video stream from source: {self.src}")
        
        # Initialize video capture
        self.stream = cv2.VideoCapture(self.src)
        
        if not self.stream.isOpened():
            raise RuntimeError(f"Failed to open video source: {self.src}")
        
        # Set camera properties
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.stream.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Disable auto-focus for faster capture (if supported)
        self.stream.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        
        # Reduce buffer size for lower latency
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Get actual properties
        actual_width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.stream.get(cv2.CAP_PROP_FPS))
        
        print(f"Stream initialized: {actual_width}x{actual_height} @ {actual_fps} FPS")
        
        # Start the thread
        self.stopped = False
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        
        # Wait for first frame
        time.sleep(0.5)
        
        return self
    
    def _update(self):
        """Update thread - continuously read frames"""
        while not self.stopped:
            if not self.stream.isOpened():
                self.stopped = True
                break
            
            ret, frame = self.stream.read()
            
            if not ret:
                self.stopped = True
                break
            
            # If queue is full, remove oldest frame
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            # Add new frame
            try:
                self.frame_queue.put(frame, block=False)
            except queue.Full:
                pass
    
    def read(self) -> Optional[Tuple[bool, Optional[cv2.Mat]]]:
        """
        Read the next frame
        
        Returns:
            Tuple of (success, frame) or None if stopped
        """
        if self.stopped:
            return False, None
        
        try:
            frame = self.frame_queue.get(timeout=1.0)
            return True, frame
        except queue.Empty:
            return False, None
    
    def stop(self):
        """Stop the video stream"""
        print("Stopping video stream...")
        self.stopped = True
        
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        
        if self.stream is not None:
            self.stream.release()
        
        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        print("Video stream stopped")
    
    def is_opened(self) -> bool:
        """Check if stream is opened"""
        return self.stream is not None and self.stream.isOpened() and not self.stopped
    
    def get_fps(self) -> int:
        """Get stream FPS"""
        if self.stream is not None:
            return int(self.stream.get(cv2.CAP_PROP_FPS))
        return 0


class VideoWriter:
    """Video writer for saving clips"""
    
    def __init__(self, output_path: str, fps: int = 30, 
                 resolution: Tuple[int, int] = (1280, 720)):
        """
        Initialize video writer
        
        Args:
            output_path: Output file path
            fps: Frames per second
            resolution: Video resolution (width, height)
        """
        self.output_path = output_path
        self.fps = fps
        self.resolution = resolution
        
        # Use MP4V codec (widely supported)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        self.writer = cv2.VideoWriter(
            output_path,
            fourcc,
            fps,
            resolution
        )
        
        if not self.writer.isOpened():
            raise RuntimeError(f"Failed to create video writer: {output_path}")
    
    def write(self, frame: cv2.Mat):
        """Write a frame to video"""
        if self.writer is not None and self.writer.isOpened():
            # Resize frame if needed
            if frame.shape[1] != self.resolution[0] or frame.shape[0] != self.resolution[1]:
                frame = cv2.resize(frame, self.resolution)
            self.writer.write(frame)
    
    def release(self):
        """Release the video writer"""
        if self.writer is not None:
            self.writer.release()


class CircularFrameBuffer:
    """Circular buffer for storing frames (for pre-event recording)"""
    
    def __init__(self, max_size: int = 150):
        """
        Initialize circular buffer
        
        Args:
            max_size: Maximum number of frames to store
        """
        self.max_size = max_size
        self.buffer = []
        self.index = 0
    
    def add(self, frame: cv2.Mat):
        """Add frame to buffer"""
        if len(self.buffer) < self.max_size:
            self.buffer.append(frame.copy())
        else:
            self.buffer[self.index] = frame.copy()
            self.index = (self.index + 1) % self.max_size
    
    def get_all(self):
        """Get all frames in chronological order"""
        if len(self.buffer) < self.max_size:
            return self.buffer.copy()
        else:
            return self.buffer[self.index:] + self.buffer[:self.index]
    
    def clear(self):
        """Clear the buffer"""
        self.buffer.clear()
        self.index = 0
    
    def __len__(self):
        """Get buffer size"""
        return len(self.buffer)
