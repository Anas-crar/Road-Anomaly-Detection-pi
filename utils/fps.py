import time


class FPSCounter:
    def __init__(self):
        self.start_time = time.time()
        self.frames = 0

    def update(self):
        self.frames += 1
        elapsed = time.time() - self.start_time
        return self.frames / elapsed if elapsed > 0 else 0
