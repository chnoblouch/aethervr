from aether.gui import GUI
from aether.camera_capture import CameraCapture
from aether.runtime_connection import RuntimeConnection
from aether.head_tracker import HeadTracker
from aether.hand_tracker import HandTracker
from aether.tracking_state import TrackingState, HeadState, HandState
from aether.input_state import InputState
from aether.gesture_detector import GestureDetector
from aether.config import Config, ControllerConfig
import numpy as np
import time


class Application:

    def __init__(self):
        self.config = Config(
            left_controller_config=ControllerConfig(),
            right_controller_config=ControllerConfig(),
        )

        self.tracking_state = TrackingState()
        self.input_state = InputState()

        self.camera_capture = CameraCapture(self.on_frame)
        self.connection = RuntimeConnection(38057)

        self.head_tracker = HeadTracker(
            self.on_head_tracking_results,
        )

        self.hand_tracker = HandTracker(
            self.head_tracker,
            self.on_hand_tracking_results,
        )

        self.gesture_detector = GestureDetector(
            self.config, self.tracking_state, self.input_state
        )

        self.last_head_tracking_result = time.time()
        self.last_hand_tracking_result = time.time()

        self.gui = GUI(self.config, self.connection)
        self.gui.run()

    def on_frame(self, frame):
        now = time.time()

        if now - self.last_head_tracking_result > 0.05:
            self.last_head_tracking_result = now
            self.head_tracker.detect(frame)

        if now - self.last_hand_tracking_result > 0.05:
            self.last_hand_tracking_result = now
            self.hand_tracker.detect(frame)

        self.gui.update_camera_frame(frame)

    def on_head_tracking_results(self, state: HeadState):
        self.tracking_state.head = state

        self.input_state.headset_state.position = state.position
        self.input_state.headset_state.pitch = state.pitch
        self.input_state.headset_state.yaw = state.yaw
        
        self.connection.update_headset_state(self.input_state.headset_state)

    def on_hand_tracking_results(self, left_state: HandState, right_state: HandState):
        self.tracking_state.left_hand = left_state
        self.tracking_state.right_hand = right_state

        left_controller_state = self.input_state.left_controller_state
        right_controller_state = self.input_state.right_controller_state
        
        if left_state.visible:
            left_controller_state.position = left_state.position
            left_controller_state.orientation = left_state.orientation
            left_controller_state.timestamp = left_state.timestamp

        if right_state.visible:
            right_controller_state.position = right_state.position
            right_controller_state.orientation = right_state.orientation
            right_controller_state.timestamp = right_state.timestamp

        self.gesture_detector.detect()
        self.gui.update_camera_overlay(self.tracking_state)

        self.connection.update_controller_state(left_controller_state, right_controller_state)

    def close(self):
        self.connection.close()
        self.camera_capture.close()
        self.head_tracker.close()
        self.hand_tracker.close()


if __name__ == "__main__":
    try:
        app = Application()
    finally:
        app.close()
