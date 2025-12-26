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
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self):
        inv_length = 1.0 / self.length()
        return Position(self.x * inv_length, self.y * inv_length, self.z * inv_length)

    def lerp(self, other, t):
        return Position(
            self.x + t * (other.x - self.x),
            self.y + t * (other.y - self.y),
            self.z + t * (other.z - self.z),
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

    def from_np_array(q):
        return Orientation(q.x, q.y, q.z, q.w)

    def from_euler_angles(pitch, yaw, roll):
        # Thanks to: https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles

        cos_r = math.cos(0.5 * roll)
        sin_r = math.sin(0.5 * roll)
        cos_p = math.cos(0.5 * pitch)
        sin_p = math.sin(0.5 * pitch)
        cos_y = math.cos(0.5 * yaw)
        sin_y = math.sin(0.5 * yaw)

        return Orientation(
            sin_p * cos_y * cos_r - cos_p * sin_y * sin_r,
            cos_p * sin_y * cos_r + sin_p * cos_y * sin_r,
            cos_p * cos_y * sin_r - sin_p * sin_y * cos_r,
            cos_p * cos_y * cos_r + sin_p * sin_y * sin_r,
        )

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

        return Orientation.from_np_array(q)

    def inverse(self) -> "Orientation":
        return Orientation(-self.x, -self.y, -self.z, self.w)

    def angle_to(self, other: "Orientation") -> float:
        # Thanks to: https://stackoverflow.com/a/23263233

        d = self.inverse() * other
        y = math.sqrt(float(d.x ** 2 + d.y ** 2 + d.z ** 2))
        x = float(d.w)
        angle = abs(2.0 * math.atan2(y, x))

        if angle <= math.pi:
            return angle
        else:
            return 2.0 * math.pi - angle

    def copy(self):
        return Orientation(self.x, self.y, self.z, self.w)

    def __mul__(self, rhs: "Orientation"):
        return Orientation.from_np_array(self.to_np_array() * rhs.to_np_array())


def normalize(vector):
    return vector / np.linalg.norm(vector)
