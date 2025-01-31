from threading import Thread, Lock, Condition
from dataclasses import dataclass
import socket
import struct
import errno
import time

from aethervr.input_state import InputState, HeadsetState, ControllerState, ControllerButton


@dataclass
class RegisterImageData:
    id: int
    process_id: int
    shared_handle: int
    format: int
    width: int
    height: int
    array_size: int
    mip_count: int
    opaque_value_0: int
    opaque_value_1: int


@dataclass
class PresentImageData:
    id: int
    x: int
    y: int
    width: int
    height: int
    array_index: int


class RuntimeConnection:

    TIMEOUT = 1.0

    def __init__(self, port: int):
        self.on_connected = lambda: None
        self.on_disconnected = lambda: None
        self.on_runtime_info: lambda application_name, graphics_api: None
        self.on_register_image = lambda _: None 
        self.on_present_image = lambda _: None

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

            self.communicate()

            print("OpenXR runtime disconnected")
            self.connected = False
            self.on_disconnected()

        self.socket.close()

    def communicate(self):
        while self.running and self.connected:
            try:
                request = self.stream.recv(1)
                if len(request) == 0:
                    break

                if request == b"\x00":
                    self.send_tracking_state()
                elif request == b"\x01":
                    self.receive_runtime_info()
                elif request == b"\x02":
                    self.receive_register_image()
                elif request == b"\x03":
                    self.receive_present_image()
                else:
                    print(f"Warning: Unknown request from runtime: {request}")
            except OSError as error:
                if error.errno == errno.EAGAIN or error.errno == errno.EWOULDBLOCK:
                    pass
                else:
                    break

    def send_tracking_state(self):
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

    def receive_runtime_info(self):
        name_length = struct.unpack("I", self.stream.recv(4))[0]
        name = self.stream.recv(name_length).decode("utf-8")
        graphics_api = struct.unpack("I", self.stream.recv(4))[0]

        self.on_runtime_info(name, graphics_api)

    def receive_register_image(self):
        message = RegisterImageData(*struct.unpack("IINqIIIIQQ", self.stream.recv(56)))
        self.on_register_image(message)

    def receive_present_image(self):
        image_id = PresentImageData(*struct.unpack("IIIIII", self.stream.recv(24)))
        self.on_present_image(image_id)

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
