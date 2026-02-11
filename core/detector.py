import onnxruntime as ort
import numpy as np
import cv2
from config.settings import INPUT_SIZE, CONF_THRESHOLD
from config.class_names import CLASS_NAMES


class ONNXDetector:
    def __init__(self, model_path):
        print("🔄 Loading ONNX Runtime model...")
        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        print("✅ Model loaded successfully")

    def preprocess(self, frame):
        self.original_h, self.original_w = frame.shape[:2]

        img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
        img = img[:, :, ::-1]
        img = img.transpose(2, 0, 1)
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)
        return img

    def detect(self, frame):
        input_tensor = self.preprocess(frame)
        outputs = self.session.run(None, {self.input_name: input_tensor})[0]

        detections = []

        x_scale = self.original_w / INPUT_SIZE
        y_scale = self.original_h / INPUT_SIZE

        for det in outputs[0]:
            obj_conf = det[4]
            if obj_conf < CONF_THRESHOLD:
                continue

            class_scores = det[5:]
            class_id = np.argmax(class_scores)
            class_conf = class_scores[class_id]
            confidence = float(obj_conf * class_conf)

            if confidence < CONF_THRESHOLD:
                continue

            # YOLO format: center_x, center_y, width, height
            cx, cy, w, h = det[:4]

            x1 = int((cx - w / 2) * x_scale)
            y1 = int((cy - h / 2) * y_scale)
            x2 = int((cx + w / 2) * x_scale)
            y2 = int((cy + h / 2) * y_scale)

            detections.append({
                "box": (x1, y1, x2, y2),
                "class": CLASS_NAMES[class_id],
                "confidence": confidence
            })

        return detections
