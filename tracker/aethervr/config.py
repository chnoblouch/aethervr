from dataclasses import dataclass, field
from typing import Optional, Any, Dict

from aethervr.tracking_state import Gesture
from aethervr.input_state import ControllerButton


LEFT_HAND_TRACKING_ORIGIN = (0.2, 0.6)
LEFT_HAND_WORLD_ORIGIN = (-0.3, -0.2)
RIGHT_HAND_TRACKING_ORIGIN = (0.8, 0.6)
RIGHT_HAND_WORLD_ORIGIN = (0.3, -0.2)

DEFAULT_GESTURE_MAPPINGS = {
    Gesture.PINCH: ControllerButton.TRIGGER,
    Gesture.PALM_PINCH: ControllerButton.MENU,
    Gesture.FIST: ControllerButton.SQUEEZE,
}

GESTURE_NAMES = {
    (Gesture.PINCH, "pinch"),
    (Gesture.PALM_PINCH, "palm_pinch"),
    (Gesture.MIDDLE_PINCH, "middle_pinch"),
    (Gesture.FIST, "fist"),
}

CONTROLLER_BUTTON_NAMES = {
    (ControllerButton.TRIGGER, "trigger"),
    (ControllerButton.SQUEEZE, "squeeze"),
    (ControllerButton.A_BUTTON, "a"),
    (ControllerButton.B_BUTTON, "b"),
    (ControllerButton.X_BUTTON, "x"),
    (ControllerButton.Y_BUTTON, "y"),
    (ControllerButton.MENU, "menu"),
    (ControllerButton.SYSTEM, "system"),
    (ControllerButton.THUMBSTICK, "thumbstick"),
}


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
    gesture_mappings: Dict[Gesture, Optional[ControllerButton]] = field(
        default_factory=lambda: DEFAULT_GESTURE_MAPPINGS
    )
    thumbstick_enabled: bool = True
    press_thumbstick: bool = True

    def deserialize(self, data: Dict[str, Any]):
        gesture_mappings = {}

        for gesture_name, button_name in data["gesture_mappings"].items():
            gesture = next(value for value, name in GESTURE_NAMES if name == gesture_name)
            
            if button_name:
                button = next(value for value, name in CONTROLLER_BUTTON_NAMES if name == button_name)
            else:
                button = None

            gesture_mappings[gesture] = button

        self.gesture_mappings = gesture_mappings
        self.thumbstick_enabled = data["thumbstick_enabled"]
        self.press_thumbstick = data["press_thumbstick"]

    def serialize(self) -> Dict[str, Any]:
        gesture_mappings = {}

        for gesture, button in self.gesture_mappings.items():
            gesture_name = next(name for value, name in GESTURE_NAMES if value == gesture)
            
            if button:
                button_name = next(name for value, name in CONTROLLER_BUTTON_NAMES if value == button)
            else:
                button_name = None

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
    controller_pitch: int
    controller_yaw: int
    controller_roll: int
    controller_depth_offset: float
    left_controller_config: ControllerConfig
    right_controller_config: ControllerConfig

    def deserialize(self, data: Dict[str, Any]):
        self.capture_config.deserialize(data["capture"])
        self.tracking_fps_cap = int(data["tracking_fps_cap"])
        self.headset_pitch_deadzone = int(data["headset_pitch_deadzone"])
        self.headset_yaw_deadzone = int(data["headset_yaw_deadzone"])
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
            "controller_pitch": self.controller_pitch,
            "controller_yaw": self.controller_yaw,
            "controller_roll": self.controller_roll,
            "controller_depth_offset": self.controller_depth_offset,
            "left_controller": self.left_controller_config.serialize(),
            "right_controller": self.right_controller_config.serialize(),
        }
