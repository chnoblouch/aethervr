from aether.input_state import InputState, ControllerButton
from threading import Thread, Lock
from typing import Optional
import socket
import struct
import errno


class RuntimeConnection:

    TIMEOUT = 1.0

    def __init__(self, port: int, input_state: InputState):
        self.state = input_state

        self.on_connected = lambda: None
        self.on_disconnected = lambda: None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(RuntimeConnection.TIMEOUT)
        self.socket.bind(("127.0.0.1", port))
        self.socket.listen()

        self.stream = None
        self.lock = Lock()

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
                    # self.stream.settimeout(RuntimeConnection.TIMEOUT)
                    self.stream.setblocking(False)
                    connected = True
                except socket.timeout:
                    continue

            print("OpenXR runtime connected")
            self.on_connected()

            while self.running and connected:
                try:
                    self.stream.recv(1)

                    self.lock.acquire()
                    self.stream.send(self.serialize_state())
                    self.lock.release()
                except OSError as error:
                    if error.errno == errno.EAGAIN or error.errno == errno.EWOULDBLOCK:
                        pass
                    else:
                        print("OpenXR runtime disconnected")
                        connected = False
                        self.on_disconnected()

        self.socket.close()

    def serialize_state(self):
        values = [
            self.state.headset_state.position.x,
            self.state.headset_state.position.y,
            self.state.headset_state.position.z,
            self.state.headset_state.pitch,
            self.state.headset_state.yaw,
            self.state.left_controller_state.position.x,
            self.state.left_controller_state.position.y,
            self.state.left_controller_state.position.z,
            self.state.left_controller_state.orientation.x,
            self.state.left_controller_state.orientation.y,
            self.state.left_controller_state.orientation.z,
            self.state.left_controller_state.orientation.w,
            self.state.right_controller_state.position.x,
            self.state.right_controller_state.position.y,
            self.state.right_controller_state.position.z,
            self.state.right_controller_state.orientation.x,
            self.state.right_controller_state.orientation.y,
            self.state.right_controller_state.orientation.z,
            self.state.right_controller_state.orientation.w,
            int(self.state.left_controller_state.buttons[ControllerButton.TRIGGER]),
            int(self.state.left_controller_state.buttons[ControllerButton.SQUEEZE]),
            int(self.state.left_controller_state.buttons[ControllerButton.A_BUTTON]),
            int(self.state.left_controller_state.buttons[ControllerButton.B_BUTTON]),
            int(self.state.left_controller_state.buttons[ControllerButton.X_BUTTON]),
            int(self.state.left_controller_state.buttons[ControllerButton.Y_BUTTON]),
            int(self.state.left_controller_state.buttons[ControllerButton.MENU]),
            int(self.state.left_controller_state.buttons[ControllerButton.SYSTEM]),
            int(self.state.right_controller_state.buttons[ControllerButton.TRIGGER]),
            int(self.state.right_controller_state.buttons[ControllerButton.SQUEEZE]),
            int(self.state.right_controller_state.buttons[ControllerButton.A_BUTTON]),
            int(self.state.right_controller_state.buttons[ControllerButton.B_BUTTON]),
            int(self.state.right_controller_state.buttons[ControllerButton.X_BUTTON]),
            int(self.state.right_controller_state.buttons[ControllerButton.Y_BUTTON]),
            int(self.state.right_controller_state.buttons[ControllerButton.MENU]),
            int(self.state.right_controller_state.buttons[ControllerButton.SYSTEM]),
        ]

        format = "fff" + "ff" + "fff" + "ffff" + "fff" + "ffff" + "BBBBBBBB" + "BBBBBBBB"
        return struct.pack(format, *values)

    def set_state(self, key, value):
        self.lock.acquire()
        self.state[key] = value
        self.lock.release()

    def close(self):
        self.lock.acquire()
        self.running = False
        self.lock.release()

        print("OpenXR runtime connection closed")
