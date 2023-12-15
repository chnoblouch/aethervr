from dataclasses import dataclass, field
import time

from aether.pose import Position, Rotation


@dataclass
class HeadState:
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    pitch: float = 0.0
    yaw: float = 0.0


@dataclass
class HandSnapshot:
    position: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
    orientation: Rotation = field(default_factory=lambda: Rotation(0.0, 0.0, 0.0, 1.0))
    time: int = 0


@dataclass
class HandState:
    last_state: HandSnapshot = field(default_factory=lambda: HandSnapshot())
    cur_state: HandSnapshot = field(default_factory=lambda: HandSnapshot())
    pinching: bool = False

    def add_snapshot(self, position, orientation):
        self.last_state.position, self.last_state.orientation = self.get_interpolated_pose()
        self.cur_state = HandSnapshot(position, orientation)

        self.last_state.time = time.time_ns()
        self.cur_state.time = time.time_ns() + 0.08 * 1e9

    def get_interpolated_pose(self) -> tuple[Position, Rotation]:
        now = time.time_ns() - self.last_state.time
        end = self.cur_state.time - self.last_state.time

        if end == 0:
            end = 10

        t = min(float(now) / float(end), 1.0)
        position = Position.lerp(self.last_state.position, self.cur_state.position, t)
        orientation = Rotation.slerp(self.last_state.orientation, self.cur_state.orientation, t)

        return position, orientation


@dataclass
class TrackingState:
    head: HeadState = field(default_factory=lambda: HeadState())
    left_hand: HandState = field(default_factory=lambda: HandState())
    right_hand: HandState = field(default_factory=lambda: HandState())
