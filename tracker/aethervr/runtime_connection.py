from threading import Thread, Lock, Condition
import socket
import struct
import errno

from aethervr.input_state import InputState, HeadsetState, ControllerState, ControllerButton


class RuntimeConnection:

    TIMEOUT = 1.0

    def __init__(self, port: int):
        self.on_connected = lambda: None
        self.on_disconnected = lambda: None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(RuntimeConnection.TIMEOUT)
        self.socket.bind(("127.0.0.1", port))
        self.socket.listen()

        self.stream = None

        self.lock = Lock()
        self.state = InputState()
        self.headset_state_available = False
        self.controller_state_available = False

        print("Starting OpenXR runtime connection...")

        self.running = True
        self.connected = False

        thread = Thread(target=self.loop)
        thread.start()

    def loop(self):
        while self.running:
            print("Waiting for OpenXR runtime to connect")

            while self.running and not self.connected:
                try:
                    self.stream, _ = self.socket.accept()
                    self.connected = True
                except socket.timeout:
                    continue

            print("OpenXR runtime connected")
            self.on_connected()

            while self.running and self.connected:
                try:
                    self.stream.recv(1)

                    with self.lock:
                        if self.headset_state_available and self.controller_state_available:
                            self.stream.send(b"\x03")
                            self.stream.send(self.serialize_headset_state())
                            self.stream.send(self.serialize_controller_state())
                        elif self.headset_state_available:
                            self.stream.send(b"\x01")
                            self.stream.send(self.serialize_headset_state())
                        elif self.controller_state_available:
                            self.stream.send(b"\x02")
                            self.stream.send(self.serialize_controller_state())
                        else:
                            self.stream.send(b"\x00")

                        self.headset_state_available = False
                        self.controller_state_available = False
                except OSError as error:
                    if error.errno == errno.EAGAIN or error.errno == errno.EWOULDBLOCK:
                        pass
                    else:
                        print("OpenXR runtime disconnected")
                        self.connected = False
                        self.on_disconnected()

        self.socket.close()

    def update_headset_state(self, state: HeadsetState):
        with self.lock:
            self.state.headset_state = state
            self.headset_state_available = True

    def update_controller_state(self, left_state: ControllerState, right_state: ControllerState):
        with self.lock:
            self.state.left_controller_state = left_state
            self.state.right_controller_state = right_state
            self.controller_state_available = True

    def serialize_headset_state(self):
        values = [
            self.state.headset_state.position.x,
            self.state.headset_state.position.y,
            self.state.headset_state.position.z,
            self.state.headset_state.pitch,
            self.state.headset_state.yaw,
        ]

        format = "fffff"
        return struct.pack(format, *values)

    def serialize_controller_state(self):
        values = [
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
            self.state.left_controller_state.thumbstick_x,
            self.state.left_controller_state.thumbstick_y,
            self.state.right_controller_state.thumbstick_x,
            self.state.right_controller_state.thumbstick_y,
        ]

        format = "fffffff" + "fffffff" + "BBBBBBBB" + "BBBBBBBB" + "ff" + "ff"
        return struct.pack(format, *values)

    def close(self):
        self.running = False
        print("OpenXR runtime connection closed")
