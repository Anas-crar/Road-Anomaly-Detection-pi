"""
ONNX-based Road Anomaly Detector
Optimized for Raspberry Pi 4 with CPU inference
"""

import cv2
import numpy as np
import onnxruntime as ort
from typing import List, Tuple, Dict
import time


class AnomalyDetector:
    """Lightweight ONNX Runtime detector for road anomalies"""

    def __init__(self, model_path: str, input_size: Tuple[int, int] = (640, 640),
                 confidence_threshold: float = 0.5, iou_threshold: float = 0.45,
                 class_names: List[str] = None):

        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.class_names = class_names or ["anomaly"]

        # Initialize ONNX Runtime
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 4

        providers = ['CPUExecutionProvider']

        print(f"Loading ONNX model from {model_path}...")
        self.session = ort.InferenceSession(model_path, sess_options, providers=providers)

        # Get model input/output names
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]

        # Detect model input size AFTER session exists
        input_shape = self.session.get_inputs()[0].shape

        if isinstance(input_shape[2], int) and isinstance(input_shape[3], int):
            model_h = int(input_shape[2])
            model_w = int(input_shape[3])
            self.input_size = (model_w, model_h)
        else:
            self.input_size = input_size

        print(f"Model loaded successfully!")
        print(f"Model expects input size: {self.input_size}")
        print(f"Input name: {self.input_name}")
        print(f"Output names: {self.output_names}")
        print(f"Providers: {self.session.get_providers()}")

        
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model input
        
        Args:
            image: Input BGR image from OpenCV
            
        Returns:
            Preprocessed image tensor
        """
        # Resize to model input size
        img = cv2.resize(image, self.input_size)
        
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        img = img.astype(np.float32) / 255.0
        
        # Transpose to CHW format (channels first)
        img = np.transpose(img, (2, 0, 1))
        
        # Add batch dimension
        img = np.expand_dims(img, axis=0)
        
        return img
    
    def postprocess(self, outputs: List[np.ndarray], orig_shape: Tuple[int, int]) -> List[Dict]:
        """
        Postprocess model outputs to get bounding boxes
        
        Args:
            outputs: Raw model outputs
            orig_shape: Original image shape (height, width)
            
        Returns:
            List of detections with format:
            [{'class': str, 'confidence': float, 'bbox': [x1, y1, x2, y2]}, ...]
        """
        detections = []
        
        # Handle different ONNX output formats
        # This depends on your model architecture (YOLOv5, YOLOv8, etc.)
        output = outputs[0]
        
        # YOLOv5/YOLOv8 format: [batch, num_detections, 5+num_classes]
        # or [batch, num_detections, 6] for YOLOv8
        if len(output.shape) == 3:
            output = output[0]  # Remove batch dimension
        
        # Filter by confidence
        if output.shape[1] > 5:  # YOLOv5 format with class probabilities
            # Format: [x, y, w, h, obj_conf, class1_conf, class2_conf, ...]
            obj_conf = output[:, 4]
            class_confs = output[:, 5:]
            class_ids = np.argmax(class_confs, axis=1)
            max_class_confs = np.max(class_confs, axis=1)
            confidences = obj_conf * max_class_confs
        else:  # YOLOv8 format
            # Format: [x, y, w, h, class_id, confidence] or similar
            confidences = output[:, 4] if output.shape[1] > 4 else output[:, -1]
            class_ids = output[:, 5].astype(int) if output.shape[1] > 5 else np.zeros(len(output), dtype=int)
        
        # Filter detections by confidence threshold
        mask = confidences >= self.confidence_threshold
        filtered_output = output[mask]
        filtered_confidences = confidences[mask]
        filtered_class_ids = class_ids[mask]
        
        if len(filtered_output) == 0:
            return detections
        
        # Extract boxes (convert from center format to corner format)
        boxes = filtered_output[:, :4]
        
        # Scale boxes to original image size
        orig_h, orig_w = orig_shape
        scale_x = orig_w / self.input_size[0]
        scale_y = orig_h / self.input_size[1]
        
        # Convert from center format (cx, cy, w, h) to corner format (x1, y1, x2, y2)
        boxes_corner = np.zeros_like(boxes)
        boxes_corner[:, 0] = (boxes[:, 0] - boxes[:, 2] / 2) * scale_x  # x1
        boxes_corner[:, 1] = (boxes[:, 1] - boxes[:, 3] / 2) * scale_y  # y1
        boxes_corner[:, 2] = (boxes[:, 0] + boxes[:, 2] / 2) * scale_x  # x2
        boxes_corner[:, 3] = (boxes[:, 1] + boxes[:, 3] / 2) * scale_y  # y2
        
        # Apply Non-Maximum Suppression
        indices = self.nms(boxes_corner, filtered_confidences, self.iou_threshold)
        
        # Create detection dictionaries
        for idx in indices:
            class_id = int(filtered_class_ids[idx])
            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"
            
            detection = {
                'class': class_name,
                'confidence': float(filtered_confidences[idx]),
                'bbox': boxes_corner[idx].astype(int).tolist(),
                'class_id': class_id
            }
            detections.append(detection)
        
        return detections
    
    @staticmethod
    def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> List[int]:
        """
        Non-Maximum Suppression
        
        Args:
            boxes: Bounding boxes in format [x1, y1, x2, y2]
            scores: Confidence scores
            iou_threshold: IoU threshold
            
        Returns:
            Indices of boxes to keep
        """
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return keep
    
    def detect(self, image: np.ndarray) -> Tuple[List[Dict], float]:
        """
        Run detection on an image
        
        Args:
            image: Input BGR image from OpenCV
            
        Returns:
            Tuple of (detections, inference_time)
        """
        orig_shape = image.shape[:2]
        
        # Preprocess
        input_tensor = self.preprocess(image)
        
        # Run inference
        start_time = time.time()
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        inference_time = time.time() - start_time
        
        # Postprocess
        detections = self.postprocess(outputs, orig_shape)
        
        return detections, inference_time
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes and labels on image
        
        Args:
            image: Input image
            detections: List of detections
            
        Returns:
            Image with drawn detections
        """
        img_copy = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class']
            confidence = det['confidence']
            
            # Different colors for different classes
            color_map = {
                'pothole': (0, 0, 255),      # Red
                'obstacle': (0, 165, 255),    # Orange
                'crack': (0, 255, 255),       # Yellow
                'bump': (255, 144, 30)        # Blue
            }
            color = color_map.get(class_name, (0, 255, 0))
            
            # Draw bounding box
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(img_copy, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(img_copy, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return img_copy
