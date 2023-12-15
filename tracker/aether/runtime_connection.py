import socket
import struct
from threading import Thread, Lock
import traceback

from aether.tracking_state import *


# class Keys:
#     HEAD_X = 0
#     HEAD_Y = 1
#     HEAD_Z = 2
#     HEAD_PITCH = 3
#     HEAD_YAW = 4
#     LEFT_HAND_POSITION_X = 5
#     LEFT_HAND_POSITION_Y = 6
#     LEFT_HAND_POSITION_Z = 7
#     LEFT_HAND_ORIENTATION_X = 8
#     LEFT_HAND_ORIENTATION_Y = 9
#     LEFT_HAND_ORIENTATION_Z = 10
#     LEFT_HAND_ORIENTATION_W = 11
#     RIGHT_HAND_POSITION_X = 12
#     RIGHT_HAND_POSITION_Y = 13
#     RIGHT_HAND_POSITION_Z = 14
#     RIGHT_HAND_ORIENTATION_X = 15
#     RIGHT_HAND_ORIENTATION_Y = 16
#     RIGHT_HAND_ORIENTATION_Z = 17
#     RIGHT_HAND_ORIENTATION_W = 18
#     LEFT_HAND_SELECT = 19
#     RIGHT_HAND_SELECT = 20


class RuntimeConnection:

    TIMEOUT = 0.1

    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(RuntimeConnection.TIMEOUT)
        self.socket.bind(("0.0.0.0", port))
        self.socket.listen()

        self.stream = None
        self.running = False
        self.lock = Lock()

        self.state = TrackingState()

        # self.state = [
        #     0.0, 0.0, 0.0,       # head position
        #     0.0, 0.0,            # head rotation
        #     0.0, 0.0, 0.0,       # left hand position
        #     0.0, 0.0, 0.0, 1.0,  # left hand orientation
        #     0.0, 0.0, 0.0,       # right hand position
        #     0.0, 0.0, 0.0, 1.0,  # right hand orientation
        #     0, 0,                # buttons
        # ]

    def run(self):
        print("Starting OpenXR runtime connection...")

        self.running = True
        thread = Thread(target=self.loop, args=())
        thread.start()

    def loop(self):
        connected = False

        while self.running:
            print("Waiting for OpenXR runtime to connect")
            
            while self.running and not connected:
                try:
                    self.stream, _ = self.socket.accept()
                    self.stream.settimeout(RuntimeConnection.TIMEOUT)
                    connected = True
                except socket.timeout:
                    continue

            print("OpenXR runtime connected")

            while self.running and connected:
                try:
                    self.stream.recv(1)
                    
                    self.lock.acquire()
                    
                    left_hand_position, left_hand_orientation = self.state.left_hand.get_interpolated_pose()
                    right_hand_position, right_hand_orientation = self.state.right_hand.get_interpolated_pose()

                    values = [
                        self.state.head.position.x,
                        self.state.head.position.y,
                        self.state.head.position.z,
                        self.state.head.pitch,
                        self.state.head.yaw,
                        left_hand_position.x, left_hand_position.y, left_hand_position.z,
                        left_hand_orientation.x, left_hand_orientation.y, left_hand_orientation.z, left_hand_orientation.w,
                        right_hand_position.x, right_hand_position.y, right_hand_position.z,
                        right_hand_orientation.x, right_hand_orientation.y, right_hand_orientation.z, right_hand_orientation.w,
                        1 if self.state.left_hand.pinching else 0,
                        1 if self.state.right_hand.pinching else 0,
                    ]

                    format = "fff" + "ff" + "fff" + "ffff" + "fff" + "ffff" + "BB" + "xx"
                    data = struct.pack(format, *values)
                    self.stream.send(data)
                    
                    self.lock.release()
                except socket.timeout:
                    continue
                except:
                    print("OpenXR runtime disconnected")
                    connected = False

        self.socket.close()

    def set_state(self, key, value):
        self.lock.acquire()
        self.state[key] = value
        self.lock.release()

    def close(self):
        self.lock.acquire()
        self.running = False
        self.lock.release()

        print("OpenXR runtime connection closed")