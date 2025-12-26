from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from aethervr.pose import Position, Orientation


@dataclass
class HeadsetState:
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    pitch: float = 0.0
    yaw: float = 0.0


class ControllerButton(Enum):
    TRIGGER = 0
    SQUEEZE = 1
    A_BUTTON = 2
    B_BUTTON = 3
    X_BUTTON = 4
    Y_BUTTON = 5
    MENU = 6
    SYSTEM = 7
    THUMBSTICK = 8


@dataclass
class ControllerState:
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    orientation: Orientation = field(default_factory=lambda: Orientation(0.0, 0.0, 0.0, 1.0))
    buttons: dict[ControllerButton, bool] = field(
        default_factory=lambda: {button: False for button in ControllerButton}
    )
    jostick_center: Optional[Position] = None
    thumbstick_x: float = 0.0
    thumbstick_y: float = 0.0
    timestamp: int = 0


@dataclass
class InputState:
    headset_state: HeadsetState = field(default_factory=lambda: HeadsetState())
    left_controller_state: ControllerState = field(default_factory=lambda: ControllerState())
    right_controller_state: ControllerState = field(default_factory=lambda: ControllerState())
