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

    def copy(self):
        return Position(self.x, self.y, self.z)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass
class Rotation:
    x: float
    y: float
    z: float
    w: float

    def from_triangle(p1, p2, p3, flip):
        v1 = normalize(p2.to_np_array() - p1.to_np_array())
        v2 = normalize(p3.to_np_array() - p1.to_np_array())

        # z_axis = -v1
        # y_axis = normalize(np.cross(v1, v2))
        # x_axis = normalize(np.cross(y_axis, z_axis))

        y_axis = v1
        z_axis = normalize(np.cross(v1, v2))
        x_axis = normalize(np.cross(y_axis, z_axis))

        if flip:
            x_axis = -x_axis
            z_axis = -z_axis

        matrix = np.array([x_axis, y_axis, z_axis])
        q = quaternion.from_rotation_matrix(matrix)

        return Rotation(q.x, q.y, q.z, q.w)


def normalize(vector):
    return vector / np.linalg.norm(vector)
