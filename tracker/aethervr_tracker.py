from threading import Lock
import time
import os
import math

from aethervr.gui import GUI
from aethervr.camera_capture import CameraCapture
from aethervr.camera_capture2 import CameraCapture2
from aethervr.runtime_connection import RuntimeConnection
from aethervr.head_tracker import HeadTracker
from aethervr.hand_tracker import HandTracker
from aethervr.tracking_state import TrackingState, HeadState, HandState
from aethervr.input_state import InputState
from aethervr.gesture_detector import GestureDetector
from aethervr.config import Config, CaptureConfig, ControllerConfig
from aethervr.system_openxr_config import SystemOpenXRConfig
from aethervr.pose import Orientation
from aethervr import mediapipe_models
from aethervr import ffi


class Application:

    def __init__(self):
        ffi.load_shared_libraries()
        ffi.camera_capture.aethervr_camera_init()

        self.config = Config(
            tracking_running=True,
            capture_config=CaptureConfig(
                camera=None,
                frame_width=860,
                frame_height=720,
            ),
            tracking_fps_cap=20,
            left_controller_config=ControllerConfig(),
            right_controller_config=ControllerConfig(),
            headset_pitch_deadzone=8,
            headset_yaw_deadzone=8,
            controller_pitch=0,
            controller_yaw=0,
            controller_roll=0,
        )

        self.tracking_state = TrackingState()
        self.input_state = InputState()

        self.camera_capture = CameraCapture(self.config.capture_config, self.on_frame, self.on_camera_error)
        self.camera_capture2 = CameraCapture2(self.config.capture_config, self.on_frame, self.on_camera_error)
        self.connection = RuntimeConnection(38057)
        self.system_openxr_config = SystemOpenXRConfig()

        self.head_tracker = None
        self.hand_tracker = None
        self.gesture_detector = None

        self.gui = GUI(self.config, self.system_openxr_config, self.connection, self.camera_capture, self.camera_capture2)

        self.last_head_tracking_time = time.time()
        self.last_hand_tracking_time = time.time()
        self.head_tracking_queue_size = 0
        self.hand_tracking_queue_size = 0
        self.head_tracking_lock = Lock()
        self.hand_tracking_lock = Lock()

        if mediapipe_models.are_all_models_cached():
           self.start()
        else:
            downloaded = self.gui.show_download_dialog(mediapipe_models.download)
            
            if downloaded and mediapipe_models.are_all_models_cached():
                self.start() 

    def start(self):
        self.head_tracker = HeadTracker(self.on_head_tracking_results)
        self.hand_tracker = HandTracker(self.head_tracker, self.on_hand_tracking_results)
        self.gesture_detector = GestureDetector(self.config, self.tracking_state, self.input_state)
        self.camera_capture2.start()
        self.gui.run()
    
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

    def on_camera_error(self):
        self.gui.display_camera_error()

    def on_head_tracking_results(self, state: HeadState):
        with self.head_tracking_lock:
            self.head_tracking_queue_size -= 1

        self.tracking_state.head = state

        if state.visible:
            self.input_state.headset_state.position = state.position
            self.input_state.headset_state.pitch = self.adjust_head_angle(state.pitch, self.config.headset_pitch_deadzone)
            self.input_state.headset_state.yaw = self.adjust_head_angle(state.yaw, self.config.headset_yaw_deadzone)
        else:
            self.input_state.headset_state.pitch = 0.0
            self.input_state.headset_state.yaw = 0.0

        self.connection.update_headset_state(self.input_state.headset_state)

    def adjust_head_angle(self, angle: float, deadzone: float):
        abs_angle_adjusted = abs(angle) - deadzone

        if abs_angle_adjusted > 0.0:
            return math.copysign(abs_angle_adjusted, angle)
        else:
            return 0.0

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

        pitch = math.radians(self.config.controller_pitch)
        yaw = math.radians(self.config.controller_yaw)
        roll = math.radians(self.config.controller_roll)

        if left_state.visible:
            delta_angle = left_controller_state.orientation.angle_to(left_state.orientation)
            
            if delta_angle > 1.0:
                left_state.orientation = left_controller_state.orientation.slerp(left_state.orientation, 0.5)

            left_controller_state.position = left_state.position
            left_controller_state.orientation = left_state.orientation * Orientation.from_euler_angles(pitch, yaw, roll)
            left_controller_state.timestamp = left_state.timestamp

        if right_state.visible:
            delta_angle = right_controller_state.orientation.angle_to(right_state.orientation)
            
            if delta_angle > 1.0:
                right_state.orientation = right_controller_state.orientation.slerp(right_state.orientation, 0.5)

            right_controller_state.position = right_state.position
            right_controller_state.orientation = right_state.orientation * Orientation.from_euler_angles(-pitch, -yaw, roll)
            right_controller_state.timestamp = right_state.timestamp

        self.gesture_detector.detect()
        self.gui.update_camera_overlay(self.tracking_state)

        self.connection.update_controller_state(left_controller_state, right_controller_state)

    def close(self):
        self.connection.close()
        self.camera_capture.close()
        self.camera_capture2.close()
        
        if self.head_tracker is not None:
            self.head_tracker.close()

        if self.hand_tracker is not None:
            self.hand_tracker.close()

        ffi.camera_capture.aethervr_camera_deinit()


if __name__ == "__main__":
    try:
        app = Application()
    except Exception as e:
        print(e)
        os._exit(1)
    finally:
        app.close()
