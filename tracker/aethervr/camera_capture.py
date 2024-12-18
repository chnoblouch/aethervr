import cv2
from threading import Thread


class CameraCapture:

    def __init__(self, on_frame):
        print("Opening capture device...")

        self.running = True
        self.frame = None
        self.on_frame = on_frame

        self.thread = Thread(target=self.capture_images)
        self.thread.start()

    def capture_images(self):
        capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 860)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not capture.isOpened():
            raise Exception("Failed to open capture device")

        print("Capture device opened")

        while self.running:
            ret, frame = capture.read()
            if not ret:
                print("Failed to capture camera image")
                self.running = False
                break

            self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame = cv2.flip(self.frame, 1)
            self.on_frame(self.frame)

        capture.release()
        print("Camera capture closed")

    def close(self):
        print("Closing camera capture...")
        self.running = False
