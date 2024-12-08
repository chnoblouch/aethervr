from aether.pose import Position, Orientation
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any


@dataclass
class HeadState:
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    pitch: float = 0.0
    yaw: float = 0.0


class Gesture(Enum):
    PINCH = 0
    PALM_PINCH = 1
    FIST = 2


@dataclass
class HandState:
    visible: bool = False
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    orientation: Orientation = field(default_factory=lambda: Orientation(0.0, 0.0, 0.0, 1.0))
    timestamp: int = 0
    landmarks: Optional[Any] = None
    gesture: Optional[Gesture] = None


@dataclass
class TrackingState:
    head: HeadState = field(default_factory=lambda: HeadState())
    left_hand: HandState = field(default_factory=lambda: HandState())
    right_hand: HandState = field(default_factory=lambda: HandState())
