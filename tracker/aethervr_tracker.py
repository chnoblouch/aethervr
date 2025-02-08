from threading import Lock
import time
import os

from aethervr.gui import GUI
from aethervr.camera_capture import CameraCapture
from aethervr.runtime_connection import RuntimeConnection
from aethervr.head_tracker import HeadTracker
from aethervr.hand_tracker import HandTracker
from aethervr.tracking_state import TrackingState, HeadState, HandState
from aethervr.input_state import InputState
from aethervr.gesture_detector import GestureDetector
from aethervr.config import Config, ControllerConfig
from aethervr.system_openxr_config import SystemOpenXRConfig


class Application:

    def __init__(self):
        self.config = Config(
            tracking_running=True,
            tracking_fps_cap=20,
            left_controller_config=ControllerConfig(),
            right_controller_config=ControllerConfig(),
        )

        self.tracking_state = TrackingState()
        self.input_state = InputState()

        self.camera_capture = CameraCapture(self.on_frame)
        self.connection = RuntimeConnection(38057)

        self.head_tracker = HeadTracker(self.on_head_tracking_results)
        self.hand_tracker = HandTracker(self.head_tracker, self.on_hand_tracking_results)
        self.gesture_detector = GestureDetector(self.config, self.tracking_state, self.input_state)

        self.last_head_tracking_time = time.time()
        self.last_hand_tracking_time = time.time()
        self.head_tracking_queue_size = 0
        self.hand_tracking_queue_size = 0
        self.head_tracking_lock = Lock()
        self.hand_tracking_lock = Lock()

        self.system_openxr_config = SystemOpenXRConfig()

        try:
            self.gui = GUI(self.config, self.connection, self.system_openxr_config)
            self.gui.run()
        except Exception as e:
            print(e)
            os._exit(1)

    def on_frame(self, frame):
        self.gui.update_camera_frame(frame)

        if not self.config.tracking_running:
            self.gui.clear_camera_overlay()
            return

        now = time.time()
        min_tracking_delay = 1.0 / self.config.tracking_fps_cap

        if self.head_tracking_queue_size < 2 and now - self.last_head_tracking_time >= min_tracking_delay:
            with self.head_tracking_lock:
                self.last_head_tracking_time = now
                self.head_tracking_queue_size += 1
                self.head_tracker.detect(frame)

        if self.hand_tracking_queue_size < 2 and now - self.last_hand_tracking_time >= min_tracking_delay:
            with self.hand_tracking_lock:
                self.last_hand_tracking_time = now
                self.hand_tracking_queue_size += 1
                self.hand_tracker.detect(frame)

    def on_head_tracking_results(self, state: HeadState):
        with self.head_tracking_lock:
            self.head_tracking_queue_size -= 1

        self.tracking_state.head = state

        if state.visible:
            self.input_state.headset_state.position = state.position
            self.input_state.headset_state.pitch = state.pitch
            self.input_state.headset_state.yaw = state.yaw
        else:
            self.input_state.headset_state.pitch = 0.0
            self.input_state.headset_state.yaw = 0.0

        self.connection.update_headset_state(self.input_state.headset_state)

    def on_hand_tracking_results(self, left_state: HandState, right_state: HandState):
        with self.hand_tracking_lock:
            self.hand_tracking_queue_size -= 1
        
        previous_left_gesture = self.tracking_state.left_hand.gesture
        self.tracking_state.left_hand = left_state
        self.tracking_state.left_hand.previous_gesture = previous_left_gesture

        previous_right_gesture = self.tracking_state.right_hand.gesture
        self.tracking_state.right_hand = right_state
        self.tracking_state.right_hand.previous_gesture = previous_right_gesture

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
