from dataclasses import dataclass
from threading import Thread, Event
from copy import copy
from typing import Callable

import numpy as np
import numpy.typing

from aethervr import ffi
from aethervr.config import CaptureConfig


@dataclass
class Camera:
    id: int
    name: str
    resolutions: list["Resolution"]


@dataclass
class Resolution:
    width: int
    height: int


class CameraCapture2:

    def __init__(
        self,
        config: CaptureConfig,
        on_frame: Callable[[numpy.typing.ArrayLike], None],
        on_error: Callable[[], None],
    ):
        self.source_config = config
        self.on_frame = on_frame
        self.on_error = on_error

        self.active_config: CaptureConfig = None
        self.running = Event()
        self.thread = None

        self.cameras = self._enumerate_cameras()

    def start(self):
        print("Opening capture device...")

        if self.running.is_set():
            self.close()

        self.active_config = copy(self.source_config)
        self.running.set()

        self.thread = Thread(target=self._capture_images)
        self.thread.start()

    def close(self):
        if not self.running.is_set():
            return

        print("Closing capture device...")
        self.running.clear()
        self.thread.join()

    def _enumerate_cameras(self) -> list[Camera]:
        ffi_cameras = ffi.camera_capture.aethervr_camera_enumerate()
        cameras = []

        for i in range(ffi_cameras.contents.num_cameras):
            ffi_camera = ffi_cameras.contents.cameras[i]

            resolutions = []

            for j in range(ffi_camera.num_resolutions):
                ffi_resolution = ffi_camera.resolutions[j]
                
                resolution = Resolution(
                    width=ffi_resolution.width,
                    height=ffi_resolution.height,
                )
                
                resolutions.append(resolution)

            camera = Camera(
                id=ffi_camera.id,
                name=ffi_camera.name.decode("utf-8"),
                resolutions=resolutions,
            )

            cameras.append(camera)

        ffi.camera_capture.aethervr_camera_destroy_list(ffi_cameras)
        return cameras

    def _capture_images(self):
        capture = ffi.camera_capture.aethervr_camera_open(
            self.active_config.camera.id,
            self.active_config.frame_width,
            self.active_config.frame_height,
        )

        if not capture:
            print("Failed to open capture device")
            self.running.clear()
            return

        print("Capture device opened")

        while self.running.is_set():
            frame = ffi.camera_capture.aethervr_camera_capture_frame(capture)

            if not frame:
                continue

            width = frame.contents.width
            height = frame.contents.height
            pixels = frame.contents.pixels
            np_array = np.ctypeslib.as_array(pixels, (height, width, 3))

            np_array = np.flip(np_array, 1)
            self.on_frame(np_array.copy())

            ffi.camera_capture.aethervr_camera_destroy_frame(frame)

        ffi.camera_capture.aethervr_camera_close(capture)
        print("Capture device closed")
