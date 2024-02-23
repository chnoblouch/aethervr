import unittest
from aether.pose import Position


class TestPosition(unittest.TestCase):

    def test_position_init(self):
        position = Position(328.192, -12831.2, 0.1221)
        self.assertEqual(position.x, 328.192)
        self.assertEqual(position.y, -12831.2)
        self.assertEqual(position.z, 0.1221)


if __name__ == "__main__":
    unittest.main()