from dataclasses import dataclass, field
from typing import Optional

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


@dataclass
class ControllerConfig:
    gesture_mappings: dict[Gesture, Optional[ControllerButton]] = field(
        default_factory=lambda: DEFAULT_GESTURE_MAPPINGS
    )


@dataclass
class Config:
    tracking_running: bool
    tracking_fps_cap: int
    left_controller_config: ControllerConfig
    right_controller_config: ControllerConfig
