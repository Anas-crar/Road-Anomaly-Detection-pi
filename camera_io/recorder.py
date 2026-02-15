import cv2
import time
from collections import deque
from utils.file_utils import generate_video_path


class EventRecorder:
    def __init__(self, fps, buffer_seconds):
        self.buffer = deque(maxlen=int(fps * buffer_seconds))
        self.recording = False
        self.writer = None

    def update_buffer(self, frame):
        self.buffer.append(frame.copy())

    def start_recording(self, fps, frame_shape):
        path = generate_video_path()
        height, width = frame_shape[:2]

        # Try to use H.264 (avc1) first, fallback to mp4v
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        self.writer = cv2.VideoWriter(path, fourcc, fps, (width, height))
        
        if not self.writer.isOpened():
            # Fallback to mp4v if avc1 fails
            print("Warning: avc1 codec not available, falling back to mp4v")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(path, fourcc, fps, (width, height))

        for frame in self.buffer:
            self.writer.write(frame)

        self.recording = True
        self.start_time = time.time()

    def write_frame(self, frame):
        if self.recording:
            self.writer.write(frame)

    def stop_recording(self):
        if self.recording:
            self.writer.release()
            self.recording = False
