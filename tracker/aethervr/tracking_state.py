from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

from aethervr.pose import Position, Orientation


@dataclass
class HeadState:
    visible: bool = False
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    pitch: float = 0.0
    yaw: float = 0.0
    landmarks: Optional[Any] = None


class Gesture(Enum):
    PINCH = 0
    PALM_PINCH = 1
    MIDDLE_PINCH = 2
    FIST = 3


@dataclass
class HandState:
    visible: bool = False
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    orientation: Orientation = field(default_factory=lambda: Orientation(0.0, 0.0, 0.0, 1.0))
    timestamp: int = 0
    landmarks: Optional[Any] = None
    world_landmarks: Optional[Any] = None
    gesture: Optional[Gesture] = None
    previous_gesture: Optional[Gesture] = None


@dataclass
class TrackingState:
    head: HeadState = field(default_factory=lambda: HeadState())
    left_hand: HandState = field(default_factory=lambda: HandState())
    right_hand: HandState = field(default_factory=lambda: HandState())
