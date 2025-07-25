import cv2
from threading import Thread, Event
from copy import copy

from aethervr.config import CaptureConfig


class CameraCapture:

    def __init__(self, config: CaptureConfig, on_frame, on_error):
        self.frame = None
        self.source_config = config
        self.on_frame = on_frame
        self.on_error = on_error

        self.active_config: CaptureConfig = None
        self.running = Event()
        self.thread = None

    def start(self):
        self.active_config = copy(self.source_config)
        self.running.set()

        self.thread = Thread(target=self.capture_images)
        self.thread.start()

    def restart(self):
        if self.source_config == self.active_config:
            return

        self.close()
        self.start()

    def capture_images(self):
        print("Opening capture device...")

        capture = cv2.VideoCapture(self.active_config.camera_index)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.active_config.frame_width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.active_config.frame_height)

        if not capture.isOpened():
            self.on_error()
            return

        print("Capture device opened")

        while self.running.is_set():
            ret, frame = capture.read()
            if not ret:
                print("Failed to capture camera image")
                continue

            self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame = cv2.flip(self.frame, 1)
            self.on_frame(self.frame)

        capture.release()
        print("Camera capture closed")

    def close(self):
        if not self.running.is_set():
            return

        print("Closing camera capture...")
        self.running.clear()
        self.thread.join()
