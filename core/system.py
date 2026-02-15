import cv2
import time
import threading
import logging
from config.settings import *
from core.detector import ONNXDetector
from camera_io.camera import initialize_camera
from camera_io.recorder import EventRecorder
from utils.logger import log_event
from utils.file_utils import generate_image_path
from utils.fps import FPSCounter

class AnomalyDetectorSystem:
    def __init__(self):
        self.camera_index = CAMERA_INDEX
        self.model_path = MODEL_PATH
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.latest_frame = None
        
        # Initialize components locally to avoid global state issues
        self.detector = None
        self.cap = None
        self.recorder = None
        self.fps_counter = None

    def start(self):
        if self.running:
            return

        log_event("🚀 Starting Road Anomaly Detection System (Background)")
        self.running = True
        self.thread = threading.Thread(target=self._run_detection_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        log_event("🛑 Road Anomaly Detection System Stopped")

    def get_latest_frame(self):
        """Returns the latest annotated frame (JPEG encoded)."""
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame

    def _run_detection_loop(self):
        # Initialize resources in the thread
        try:
            self.detector = ONNXDetector(self.model_path)
            self.cap = initialize_camera(self.camera_index)
            
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps == 0:
                fps = FPS_FALLBACK
            
            self.recorder = EventRecorder(fps, PRE_EVENT_SECONDS)
            self.fps_counter = FPSCounter()
            
            # Smart event control logic
            last_detection_time = 0
            DETECTION_COOLDOWN = 15
            detection_active = False
            last_no_detection_time = time.time()
            NO_DETECTION_RESET_TIME = 5

            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    log_event("⚠️ Camera frame read failed")
                    break

                self.recorder.update_buffer(frame)
                detections = self.detector.detect(frame)
                
                # Annotate frame for display
                display_frame = frame.copy()
                if detections:
                    display_frame = self._draw_detections(display_frame, detections)

                # Store latest frame safely
                ret_enc, buffer = cv2.imencode('.jpg', display_frame)
                if ret_enc:
                    with self.lock:
                        self.latest_frame = buffer.tobytes()

                # --- Event Logic ---
                current_time = time.time()
                
                if detections:
                    last_no_detection_time = current_time

                    if not detection_active and \
                       (current_time - last_detection_time > DETECTION_COOLDOWN):
                        
                        detection_active = True
                        last_detection_time = current_time
                        
                        # Log and Save
                        for det in detections:
                             log_event(f"⚠️ Detected {det['class']} (Confidence: {det['confidence']:.2f})")
                        
                        image_path = generate_image_path()
                        cv2.imwrite(image_path, display_frame) # Save annotated frame
                        log_event(f"📸 Image saved: {image_path}")
                        
                        # Record Video
                        self.recorder.start_recording(fps, frame.shape)
                        
                        # Capture post-event frames
                        start_time = time.time()
                        while time.time() - start_time < POST_EVENT_SECONDS and self.running:
                            ret, new_frame = self.cap.read()
                            if not ret:
                                break
                                
                            new_detections = self.detector.detect(new_frame)
                            new_display_frame = new_frame.copy()
                            if new_detections:
                                new_display_frame = self._draw_detections(new_display_frame, new_detections)
                            
                            # Update live feed during recording too
                            ret_enc, buffer = cv2.imencode('.jpg', new_display_frame)
                            if ret_enc:
                                with self.lock:
                                    self.latest_frame = buffer.tobytes()

                            self.recorder.write_frame(new_frame)
                        
                        self.recorder.stop_recording()
                        log_event("🎥 Video clip saved")

                else:
                     if current_time - last_no_detection_time > NO_DETECTION_RESET_TIME:
                        detection_active = False

                self.fps_counter.update()
                time.sleep(SLEEP_INTERVAL)

        except Exception as e:
            log_event(f"❌ System Error: {e}")
        finally:
            if self.cap:
                self.cap.release()
            
    def _draw_detections(self, frame, detections):
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            label = f"{det['class']} {det['confidence']:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame
