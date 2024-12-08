from aether.tracking_state import Gesture
from aether.input_state import ControllerButton
from dataclasses import dataclass, field
from typing import Optional


LEFT_HAND_TRACKING_ORIGIN = (0.2, 0.6)
LEFT_HAND_WORLD_ORIGIN = (-0.3, -0.2)
RIGHT_HAND_TRACKING_ORIGIN = (0.8, 0.6)
RIGHT_HAND_WORLD_ORIGIN = (0.3, -0.2)


@dataclass
class ControllerConfig:
    gesture_mappings: dict[Gesture, Optional[ControllerButton]] = field(default_factory=lambda: {
        Gesture.PINCH: ControllerButton.TRIGGER,
        Gesture.PALM_PINCH: ControllerButton.MENU,
        Gesture.FIST: ControllerButton.SQUEEZE,
    })


@dataclass
class Config:
    left_controller_config: ControllerConfig
    right_controller_config: ControllerConfig
