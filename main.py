import time
import cv2
from config.settings import *
from core.detector import ONNXDetector
from io.camera import initialize_camera
from io.recorder import EventRecorder
from utils.logger import log_event
from utils.file_utils import generate_image_path
from utils.fps import FPSCounter

def draw_detections(frame, detections):
    for det in detections:
        x1, y1, x2, y2 = det["box"]
        label = f"{det['class']} {det['confidence']:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )
    return frame

def main():
    log_event("🚀 Starting Road Anomaly Detection System")

    detector = ONNXDetector(MODEL_PATH)
    cap = initialize_camera(CAMERA_INDEX)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = FPS_FALLBACK

    recorder = EventRecorder(fps, PRE_EVENT_SECONDS)
    fps_counter = FPSCounter()

    while True:
        ret, frame = cap.read()
        if not ret:
            log_event("⚠️ Camera frame read failed")
            break

        recorder.update_buffer(frame)
        detections = detector.detect(frame)
        
        if detections:
            frame = draw_detections(frame, detections)

        if detections:
            for det in detections:
                log_event(
                    f"⚠️ Detected {det['class']} "
                    f"(Confidence: {det['confidence']:.2f})"
                )

            image_path = generate_image_path()
            cv2.imwrite(image_path, frame)
            log_event(f"📸 Image saved: {image_path}")

            recorder.start_recording(fps, frame.shape)

            start_time = time.time()
            while time.time() - start_time < POST_EVENT_SECONDS:
                ret, new_frame = cap.read()
                if not ret:
                    break
                new_detections = detector.detect(new_frame)
                if new_detections:
                    new_frame = draw_detections(new_frame, new_detections)

                recorder.write_frame(new_frame)


            recorder.stop_recording()
            log_event("🎥 Video clip saved")

        current_fps = fps_counter.update()
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    main()
