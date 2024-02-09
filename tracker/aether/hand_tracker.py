from dataclasses import dataclass
from threading import Lock
import math

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
# fmt: off
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
# fmt: on
from mediapipe import solutions

import cv2
import numpy as np

from aether.pose import Position, Rotation
from aether import mediapipe_models


@dataclass
class Hand:
    position: Position
    orientation: Rotation
    select: bool


@dataclass
class HandDetectionResults:
    left: Hand
    right: Hand


class HandAverager:
    def __init__(self):
        self.count = 2
        self.positions = []
        self.orientations = []
        self.index = 0

        for _ in range(self.count):
            self.positions.append(Position(0.0, 0.0, 0.0))
            self.orientations.append(Rotation(0.0, 0.0, 0.0, 1.0))

    def insert(self, position, orientation):
        self.positions[self.index] = position
        self.orientations[self.index] = orientation
        self.index = (self.index + 1) % self.count

    def get_average_position(self):
        sum_position = Position(0.0, 0.0, 0.0)

        for position in self.positions:
            sum_position.x += position.x
            sum_position.y += position.y
            sum_position.z += position.z

        return Position(
            sum_position.x / self.count,
            sum_position.y / self.count,
            sum_position.z / self.count,
        )

    def get_average_orientation(self):
        # https://github.com/christophhagen/averaging-quaternions/blob/master/averageQuaternions.py

        quaternions = np.array([[o.w, o.x, o.y, o.z] for o in self.orientations])
        m = quaternions.shape[0]
        a = np.zeros(shape=(4, 4))

        for i in range(0, m):
            q = quaternions[i, :]
            a = np.outer(q, q) + a

        a = (1.0 / m) * a
        eigen_values, eigen_vectors = np.linalg.eig(a)
        eigen_vectors = eigen_vectors[:, eigen_values.argsort()[::-1]]

        avg = np.real(eigen_vectors[:, 0])

        return Rotation(avg[1], avg[2], avg[3], avg[0])


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

        self.mp_results = None
        self.lock = Lock()

        self.averagers = [HandAverager(), HandAverager()]

        print("Hand tracker initialized")

    def detect(self, frame):
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.detector.detect_async(image, self.timestamp)
        self.timestamp += 1

    def _process_results(self, detection_results, image, timestamp):
        self.lock.acquire()
        self.mp_results = detection_results
        self.lock.release()

        left_hand = Hand(Position(0.0, 0.0, 0.0), Rotation(0.0, 0.0, 0.0, 1.0), False)
        right_hand = Hand(Position(0.0, 0.0, 0.0), Rotation(0.0, 0.0, 0.0, 1.0), False)

        try:
            for i, landmarks in enumerate(detection_results.hand_world_landmarks):
                handedness = detection_results.handedness[i][0].display_name

                # HACK
                handedness = "Right" if handedness == "Left" else "Left"

                if handedness == "Left":
                    hand = left_hand
                elif handedness == "Right":
                    hand = right_hand
                else:
                    continue

                landmarks_2d = detection_results.hand_landmarks[i]
                landmarks_3d = detection_results.hand_world_landmarks[i]

                width, height = image.width, image.height
                focal_length = 0.75 * width
                center = (0.5 * width, 0.5 * height)

                camera_matrix = np.array(
                    [
                        [focal_length, 0, center[0]],
                        [0, focal_length, center[1]],
                        [0, 0, 1],
                    ],
                    dtype="double",
                )

                dist_coeffs = np.array([0.0, 0.0, 0.0, 0.0])

                object_points = np.array([[l.x, l.y, l.z] for l in landmarks_3d])
                image_points = np.array(
                    [[l.x * width, l.y * height] for l in landmarks_2d]
                )

                retval, rvec, tvec = cv2.solvePnP(
                    object_points,
                    image_points,
                    camera_matrix,
                    dist_coeffs,
                    flags=cv2.SOLVEPNP_SQPNP,
                )

                hand_x = float(landmarks_2d[0].x) - 0.5
                hand_y = -float(landmarks_2d[0].y) + 0.5
                hand_z = -0.3
                position = Position(hand_x, hand_y, hand_z)

                p1 = HandTracker.get_landmark_position(landmarks_2d[0])
                p2 = HandTracker.get_landmark_position(landmarks_2d[5])
                p3 = HandTracker.get_landmark_position(landmarks_2d[17])
                flip = handedness == "Right"

                orientation = Rotation.from_triangle(p1, p2, p3, flip)

                if handedness == "Left":
                    averager = self.averagers[0]
                elif handedness == "Right":
                    averager = self.averagers[1]

                averager.insert(position, orientation)

                hand.position = averager.get_average_position()
                hand.orientation = averager.get_average_orientation()
                hand.select = HandTracker.is_pinching(landmarks_2d)

            self.detection_callback(HandDetectionResults(left_hand, right_hand))
        except Exception as e:
            print(e)

    def draw(self, image):
        height, width, channels = image.shape

        self.lock.acquire()

        if self.mp_results is None:
            self.lock.release()
            return

        for i, pose in enumerate(self.mp_results.hand_landmarks):
            for a, b in solutions.hands_connections.HAND_CONNECTIONS:
                is_pinching = HandTracker.is_pinching(self.mp_results.hand_landmarks[i])
                color = (0, 0, 255) if is_pinching else (0, 255, 0)

                x1 = int(width * pose[a].x)
                y1 = int(height * pose[a].y)
                x2 = int(width * pose[b].x)
                y2 = int(height * pose[b].y)
                cv2.line(image, (x1, y1), (x2, y2), color, 2)

            for j, landmark in enumerate(pose):
                is_key_point = j in (5, 17)
                radius = max(int(10 + 50 * landmark.z), 0) if is_key_point else 4

                if j == 5:
                    color = (0, 255, 255)
                elif j == 17:
                    color = (0, 0, 255)
                else:
                    color = (255, 0, 0)

                x = int(width * landmark.x)
                y = int(height * landmark.y)
                cv2.circle(image, (x, y), radius, color, -1)

        self.lock.release()

    def close(self):
        self.detector.close()
        print("Hand tracker closed")

    @staticmethod
    def get_landmark_position(landmark):
        return Position(landmark.x, -landmark.y, landmark.z)

    @staticmethod
    def is_pinching(landmarks_2d):
        tip1 = landmarks_2d[4]
        tip2 = landmarks_2d[8]
        return math.sqrt((tip2.x - tip1.x) ** 2 + (tip2.y - tip1.y) ** 2) < 0.06
