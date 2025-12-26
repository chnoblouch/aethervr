from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from enum import Enum

from aethervr.tracking_state import Gesture
from aethervr.input_state import ControllerButton
from aethervr.event_source import EventSource


class HandTrackingMode(Enum):
    DIRECT = 0
    SMOOTH = 1


LEFT_HAND_TRACKING_ORIGIN = (0.2, 0.6)
LEFT_HAND_WORLD_ORIGIN = (-0.3, -0.2)
RIGHT_HAND_TRACKING_ORIGIN = (0.8, 0.6)
RIGHT_HAND_WORLD_ORIGIN = (0.3, -0.2)

DEFAULT_GESTURE_MAPPINGS = {
    Gesture.PINCH: ControllerButton.TRIGGER,
    Gesture.PALM_PINCH: ControllerButton.MENU,
    Gesture.FIST: ControllerButton.SQUEEZE,
}

GESTURE_NAMES = (
    (Gesture.PINCH, "pinch"),
    (Gesture.PALM_PINCH, "palm_pinch"),
    (Gesture.MIDDLE_PINCH, "middle_pinch"),
    (Gesture.FIST, "fist"),
)

CONTROLLER_BUTTON_NAMES = (
    (ControllerButton.TRIGGER, "trigger"),
    (ControllerButton.SQUEEZE, "squeeze"),
    (ControllerButton.A_BUTTON, "a"),
    (ControllerButton.B_BUTTON, "b"),
    (ControllerButton.X_BUTTON, "x"),
    (ControllerButton.Y_BUTTON, "y"),
    (ControllerButton.MENU, "menu"),
    (ControllerButton.SYSTEM, "system"),
    (ControllerButton.THUMBSTICK, "thumbstick"),
)

HAND_TRACKING_MODE_NAMES = (
    (HandTrackingMode.DIRECT, "direct"),
    (HandTrackingMode.SMOOTH, "smooth"),
)


@dataclass
class CaptureConfig:
    camera: Any
    frame_width: int
    frame_height: int

    def deserialize(self, data: Dict[str, Any]):
        self.camera = data["camera"]
        self.frame_width = data["frame_width"]
        self.frame_height = data["frame_height"]

    def serialize(self) -> Dict[str, Any]:
        return {
            "camera": self.camera.name if self.camera else None,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
        }


@dataclass
class ControllerConfig:
    gesture_mappings: Dict[Gesture, Optional[ControllerButton]]
    thumbstick_enabled: bool
    press_thumbstick: bool

    def set_to_default(self):
        self.gesture_mappings = DEFAULT_GESTURE_MAPPINGS.copy()
        self.thumbstick_enabled = True
        self.press_thumbstick = True

    def deserialize(self, data: Dict[str, Any]):
        gesture_mappings = {}

        for gesture_name, button_name in data["gesture_mappings"].items():
            gesture = _deserialize_enum(gesture_name, GESTURE_NAMES)
            button = _deserialize_enum(button_name, CONTROLLER_BUTTON_NAMES)
            gesture_mappings[gesture] = button

        self.gesture_mappings = gesture_mappings
        self.thumbstick_enabled = data["thumbstick_enabled"]
        self.press_thumbstick = data["press_thumbstick"]

    def serialize(self) -> Dict[str, Any]:
        gesture_mappings = {}

        for gesture, button in self.gesture_mappings.items():
            gesture_name = _serialize_enum(gesture, GESTURE_NAMES)
            button_name = _serialize_enum(button, CONTROLLER_BUTTON_NAMES)
            gesture_mappings[gesture_name] = button_name

        return {
            "gesture_mappings": gesture_mappings,
            "thumbstick_enabled": self.thumbstick_enabled,
            "press_thumbstick": self.press_thumbstick,
        }


@dataclass
class Config:
    tracking_running: bool
    capture_config: CaptureConfig
    tracking_fps_cap: int
    headset_pitch_deadzone: int
    headset_yaw_deadzone: int
    hand_tracking_mode: HandTrackingMode
    controller_pitch: int
    controller_yaw: int
    controller_roll: int
    controller_depth_offset: float
    left_controller_config: ControllerConfig
    right_controller_config: ControllerConfig
    on_updated: EventSource = field(default_factory=lambda: EventSource())

    def set_to_default(self):
        self.tracking_fps_cap = 20
        self.headset_pitch_deadzone = 8
        self.headset_yaw_deadzone = 8
        self.hand_tracking_mode = HandTrackingMode.SMOOTH
        self.controller_pitch = 0
        self.controller_yaw = 0
        self.controller_roll = 0
        self.controller_depth_offset = 0
        self.left_controller_config.set_to_default()
        self.right_controller_config.set_to_default()

    def deserialize(self, data: Dict[str, Any]):
        self.capture_config.deserialize(data["capture"])
        self.tracking_fps_cap = int(data["tracking_fps_cap"])
        self.headset_pitch_deadzone = int(data["headset_pitch_deadzone"])
        self.headset_yaw_deadzone = int(data["headset_yaw_deadzone"])
        self.hand_tracking_mode = _deserialize_enum(data["hand_tracking_mode"], HAND_TRACKING_MODE_NAMES)
        self.controller_pitch = int(data["controller_pitch"])
        self.controller_yaw = int(data["controller_yaw"])
        self.controller_roll = int(data["controller_roll"])
        self.controller_depth_offset = float(data["controller_depth_offset"])
        self.left_controller_config.deserialize(data["left_controller"])
        self.right_controller_config.deserialize(data["right_controller"])

    def serialize(self) -> Dict[str, Any]:
        return {
            "capture": self.capture_config.serialize(),
            "tracking_fps_cap": self.tracking_fps_cap,
            "headset_pitch_deadzone": self.headset_pitch_deadzone,
            "headset_yaw_deadzone": self.headset_yaw_deadzone,
            "hand_tracking_mode": _serialize_enum(self.hand_tracking_mode, HAND_TRACKING_MODE_NAMES),
            "controller_pitch": self.controller_pitch,
            "controller_yaw": self.controller_yaw,
            "controller_roll": self.controller_roll,
            "controller_depth_offset": self.controller_depth_offset,
            "left_controller": self.left_controller_config.serialize(),
            "right_controller": self.right_controller_config.serialize(),
        }


def _deserialize_enum(name, names):
    iter = (value for value, candidate_name in names if candidate_name == name)
    return next(iter, None)


def _serialize_enum(value, names):
    iter = (name for candidate_value, name in names if candidate_value == value)
    return next(iter, None)
