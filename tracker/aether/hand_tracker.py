from dataclasses import dataclass
from threading import Lock
import math
import time

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

from aether.tracking_state import HandState
from aether.pose import Position, Orientation
from aether.config import *
from aether import mediapipe_models


class HandTracker:
    MODEL_FILE_NAME = "hand_landmarker.task"
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

    def __init__(self, head_tracker, detection_callback) -> None:
        self.head_tracker = head_tracker
        self.detection_callback = detection_callback

        model_path = mediapipe_models.download(
            HandTracker.MODEL_FILE_NAME, HandTracker.MODEL_URL
        )

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            num_hands=2,
            running_mode=RunningMode.LIVE_STREAM,
            result_callback=self._process_results,
        )
        self.detector = HandLandmarker.create_from_options(options)
        self.timestamp = 0

        print("Hand tracker initialized")

    def detect(self, frame):
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.detector.detect_async(image, self.timestamp)
        self.timestamp += 1

    def _process_results(self, detection_results, image, timestamp):
        try:
            left_hand = HandState(timestamp=time.time_ns())
            right_hand = HandState(timestamp=time.time_ns())

            for i, landmarks in enumerate(detection_results.hand_landmarks):
                handedness = detection_results.handedness[i][0].display_name
                handedness = "Right" if handedness == "Left" else "Left"

                if handedness == "Left":
                    hand = left_hand
                    tracking_origin = LEFT_HAND_TRACKING_ORIGIN
                    offset = LEFT_HAND_WORLD_ORIGIN
                elif handedness == "Right":
                    hand = right_hand
                    tracking_origin = RIGHT_HAND_TRACKING_ORIGIN
                    offset = RIGHT_HAND_WORLD_ORIGIN
                else:
                    continue

                p1 = HandTracker.get_landmark_position(landmarks[0])
                p2 = HandTracker.get_landmark_position(landmarks[5])
                p3 = HandTracker.get_landmark_position(landmarks[17])
                flip = handedness == "Left"

                dx = landmarks[17].x - landmarks[5].x
                dy = landmarks[17].y - landmarks[5].y
                depth_estimate = math.sqrt(dx * dx + dy * dy)

                raw_x = float(landmarks[0].x)
                raw_y = float(landmarks[0].y)

                hand_x = offset[0] + 2.0 * (raw_x - tracking_origin[0])
                hand_y = offset[1] - 2.0 * (raw_y - tracking_origin[1])
                hand_z = 0.1 - 7.0 * depth_estimate
                position = Position(hand_x, hand_y, hand_z)

                orientation = Orientation.from_triangle(p1, p2, p3, flip)

                hand.visible = True
                hand.landmarks = landmarks
                hand.position = position
                hand.orientation = orientation

            self.detection_callback(left_hand, right_hand)
        except Exception as e:
            print(e)

    def close(self):
        self.detector.close()
        print("Hand tracker closed")

    @staticmethod
    def get_landmark_position(landmark):
        return Position(landmark.x, -landmark.y, landmark.z)
