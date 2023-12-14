import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode

import numpy as np

from aether.pose import Position
from aether import mediapipe_models


class HeadDetectionResults:

    def __init__(self):
        self.position = Position(0.0, 0.0, 0.0)
        self.pitch = 0.0
        self.yaw = 0.0


class HeadTracker:

    MODEL_FILE_NAME = "face_landmarker.task"
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"

    def __init__(self, detection_callback):
        self.detection_callback = detection_callback

        model_path = mediapipe_models.download(HeadTracker.MODEL_FILE_NAME, HeadTracker.MODEL_URL)

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
            running_mode=RunningMode.LIVE_STREAM,
            result_callback=self._process_results
        )
        self.detector = FaceLandmarker.create_from_options(options)
        self.timestamp = 0

        self.initial_position = None
        self.calibrate_next_frame = True

        print("Head tracker initialized")

    def detect(self, frame):
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.detector.detect_async(image, self.timestamp)
        self.timestamp += 1

    def _process_results(self, detection_results, image, timestamp):
        if len(detection_results.facial_transformation_matrixes) == 0:
            return
        
        matrix = detection_results.facial_transformation_matrixes[0]
        x_axis = matrix[0][0:3]
        x_axis = x_axis / np.linalg.norm(x_axis)
        y_axis = matrix[1][0:3]
        y_axis = y_axis / np.linalg.norm(y_axis)
        z_axis = matrix[2][0:3]
        z_axis = z_axis / np.linalg.norm(z_axis)

        x = x_axis[0]
        y = z_axis[1]
        z = x_axis[2]

        position = Position(matrix[0][3] / 100.0, matrix[1][3] / 100.0, -matrix[2][3] / 100.0)

        if self.calibrate_next_frame:
            self.initial_position = position.copy()
            print(f"Calibrated at [{position.x}, {position.y}, {position.z}]")
            self.calibrate_next_frame = False
        else:
            position -= self.initial_position

        results = HeadDetectionResults()
        results.pitch = float(np.rad2deg(np.arcsin(y)))
        results.yaw = float(np.rad2deg(-np.arctan2(z, x)))
        results.position = position
        self.detection_callback(results)

    def close(self):
        self.detector.close()
        print("Head tracker closed")