import os
import time


def log_event(message):
    os.makedirs("output/logs", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    log_message = f"[{timestamp}] {message}"
    print(log_message)

    with open("output/logs/events.log", "a") as f:
        f.write(log_message + "\n")
