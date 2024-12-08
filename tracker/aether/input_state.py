from aether.pose import Position, Orientation
from enum import Enum
from dataclasses import dataclass, field


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


@dataclass
class ControllerState:
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    orientation: Orientation = field(default_factory=lambda: Orientation(0.0, 0.0, 0.0, 1.0))
    buttons: dict[ControllerButton, bool] = field(default_factory=lambda: {button: False for button in ControllerButton})
    timestamp: float = 0.0


@dataclass
class InputState:
    headset_state: HeadsetState = field(default_factory=lambda: HeadsetState())
    left_controller_state: ControllerState = field(default_factory=lambda: ControllerState())
    right_controller_state: ControllerState = field(default_factory=lambda: ControllerState())
