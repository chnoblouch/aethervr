import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode
import numpy as np

from aethervr import mediapipe_models
from aethervr.pose import Position
from aethervr.tracking_state import HeadState


class HeadTracker:

    def __init__(self, detection_callback):
        self.detection_callback = detection_callback

        model_path = mediapipe_models.get_model_path(mediapipe_models.FACE_LANDMARKER_FILE_NAME)

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
            running_mode=RunningMode.LIVE_STREAM,
            result_callback=self._process_results,
        )
        self.detector = FaceLandmarker.create_from_options(options)
        self.timestamp = 0

        print("Head tracker initialized")

    def detect(self, frame):
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.detector.detect_async(image, self.timestamp)
        self.timestamp += 1

    def _process_results(self, detection_results, image, timestamp):
        state = HeadState(visible=False)

        if len(detection_results.face_landmarks) > 0:
            state.landmarks = detection_results.face_landmarks[0]

        if len(detection_results.facial_transformation_matrixes) > 0:
            state.visible = True

            matrix = detection_results.facial_transformation_matrixes[0]
            
            # state.position = Position(matrix[0][3] / 100.0, matrix[1][3] / 100.0, -matrix[2][3] / 100.0)
            state.position = Position(0.0, 0.0, 0.0)

            x_axis = matrix[0][0:3]
            x_axis = x_axis / np.linalg.norm(x_axis)
            y_axis = matrix[1][0:3]
            y_axis = y_axis / np.linalg.norm(y_axis)
            z_axis = matrix[2][0:3]
            z_axis = z_axis / np.linalg.norm(z_axis)

            x = x_axis[0]
            y = z_axis[1]
            z = x_axis[2]

            state.pitch = -float(np.rad2deg(np.arcsin(y)))
            state.yaw = -float(np.rad2deg(np.arctan2(z, x)))

        self.detection_callback(state)

    def close(self):
        self.detector.close()
        print("Head tracker closed")
