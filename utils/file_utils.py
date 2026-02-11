import os
import time


def generate_timestamp():
    return time.strftime("%Y%m%d_%H%M%S")


def generate_image_path():
    os.makedirs("output/images", exist_ok=True)
    return f"output/images/{generate_timestamp()}.jpg"


def generate_video_path():
    os.makedirs("output/videos", exist_ok=True)
    return f"output/videos/{generate_timestamp()}.mp4"
