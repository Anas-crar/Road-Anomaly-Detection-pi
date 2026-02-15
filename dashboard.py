import os
import cv2
import time
import sys
from flask import Flask, render_template, send_from_directory, jsonify, Response

app = Flask(__name__)

# Constants
OUTPUT_DIR = "output"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")
LOGS_FILE = os.path.join(OUTPUT_DIR, "logs", "events.log")

def gen_frames(video_path):
    print(f"DEBUG: Opening video stream for {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"ERROR: Could not open video file: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30  # Fallback
        
    delay = 1.0 / fps
    print(f"DEBUG: Streaming at {fps} FPS (delay: {delay:.4f}s)")

    while cap.isOpened():
        start_time = time.time()
        success, frame = cap.read()
        if not success:
            print("DEBUG: End of video stream")
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Throttle to match FPS
            elapsed = time.time() - start_time
            if elapsed < delay:
                time.sleep(delay - elapsed)
                
    cap.release()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    # Count files
    image_count = len([name for name in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, name))]) if os.path.exists(IMAGES_DIR) else 0
    video_count = len([name for name in os.listdir(VIDEOS_DIR) if os.path.isfile(os.path.join(VIDEOS_DIR, name))]) if os.path.exists(VIDEOS_DIR) else 0
    
    # Parse logs for anomaly count and structured data
    anomaly_count = 0
    recent_logs = []
    
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            for line in reversed(lines):
                line = line.strip()
                if "Detected" in line:
                    anomaly_count += 1
                    
                    # Parse line: "[2025-02-15 12:00:00] ⚠️ Detected Pothole (Confidence: 0.85)"
                    try:
                        parts = line.split("] ", 1)
                        timestamp = parts[0][1:]
                        message = parts[1]
                        
                        # Extract class and confidence
                        # message example: "⚠️ Detected Pothole (Confidence: 0.85)"
                        desc_parts = message.split("Detected ", 1)[1].split(" (Confidence:")
                        # Map legacy codes to real names
                        class_mapping = {
                            "D00": "Longitudinal Crack",
                            "D01": "Transverse Crack",
                            "D10": "Alligator Crack",
                            "D20": "Pothole",
                            "D40": "Rutting"
                        }
                        
                        anomaly_class = desc_parts[0]
                        # Apply mapping if needed
                        anomaly_class = class_mapping.get(anomaly_class, anomaly_class)
                        
                        confidence = desc_parts[1].replace(")", "") if len(desc_parts) > 1 else "N/A"
                        
                        recent_logs.append({
                            'timestamp': timestamp,
                            'type': anomaly_class,
                            'confidence': confidence,
                            'original': line
                        })
                    except Exception as e:
                        # Fallback for parsing errors
                         recent_logs.append({
                            'timestamp': 'Unknown',
                            'type': 'Unknown',
                            'confidence': 'N/A',
                            'original': line
                        })

                if len(recent_logs) >= 10:
                    break 

    return jsonify({
        'images': image_count,
        'videos': video_count,
        'anomalies': anomaly_count,
        'recent_logs': recent_logs
    })

@app.route('/api/media')
def get_media():
    images = []
    if os.path.exists(IMAGES_DIR):
        images = sorted([f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')], reverse=True)[:12]
    
    videos = []
    if os.path.exists(VIDEOS_DIR):
        videos = sorted([f for f in os.listdir(VIDEOS_DIR) if f.endswith('.mp4')], reverse=True)[:6]

    return jsonify({
        'images': images,
        'videos': videos
    })

@app.route('/media/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

@app.route('/media/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEOS_DIR, filename)

@app.route('/video_feed/<path:filename>')
def video_feed(filename):
    video_path = os.path.join(VIDEOS_DIR, filename)
    return Response(gen_frames(video_path), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/thumbnail/<path:filename>')
def get_thumbnail(filename):
    video_path = os.path.join(VIDEOS_DIR, filename)
    
    # Check if file exists
    if not os.path.exists(video_path):
        return "Video not found", 404
        
    try:
        cap = cv2.VideoCapture(video_path)
        success, frame = cap.read()
        cap.release()
        
        if success:
            ret, buffer = cv2.imencode('.jpg', frame)
            return Response(buffer.tobytes(), mimetype='image/jpeg')
        else:
            return "Could not read frame", 500
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
