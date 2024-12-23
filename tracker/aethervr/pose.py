from dataclasses import dataclass
import math

import numpy as np
import quaternion


@dataclass
class Position:
    x: float
    y: float
    z: float

    def to_np_array(self):
        return np.array([self.x, self.y, self.z])

    def distance(self, other):
        dx = other.x - self.x
        dy = other.y = self.y
        dz = other.z = self.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def lerp(self, other, t):
        return Position(
            self.x + t * (other.x - self.x), self.y + t * (other.y - self.y), self.z + t * (other.z - self.z)
        )

    def copy(self):
        return Position(self.x, self.y, self.z)

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass
class Orientation:
    x: float
    y: float
    z: float
    w: float

    def slerp(self, other, t):
        q = quaternion.slerp(self.to_np_array(), other.to_np_array(), 0.0, 1.0, t)
        return Orientation(q.x, q.y, q.z, q.w)

    def to_np_array(self):
        return quaternion.quaternion(self.w, self.x, self.y, self.z)

    def from_triangle(p1, p2, p3, flip):
        v1 = normalize(p2.to_np_array() - p1.to_np_array())
        v2 = normalize(p3.to_np_array() - p1.to_np_array())

        y_axis = v1
        z_axis = normalize(np.cross(v2, v1))
        x_axis = normalize(np.cross(y_axis, z_axis))

        if flip:
            x_axis = -x_axis
            z_axis = -z_axis

        matrix = np.array([x_axis, y_axis, z_axis])
        q = quaternion.from_rotation_matrix(matrix)

        return Orientation(q.x, q.y, q.z, q.w)

    def copy(self):
        return Orientation(self.x, self.y, self.z, self.w)


def normalize(vector):
    return vector / np.linalg.norm(vector)
