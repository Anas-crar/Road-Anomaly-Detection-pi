import cv2
from config.settings import FRAME_WIDTH, FRAME_HEIGHT


def initialize_camera(index):
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError("❌ Unable to open USB camera")

    return cap
