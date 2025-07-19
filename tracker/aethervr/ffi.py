import sys
import ctypes
from pathlib import Path

from aethervr import platform


camera_capture = None
display_surface = None


class FFIResolution(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
    ]


class FFICamera(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("name", ctypes.c_char_p),
        ("resolutions", ctypes.POINTER(FFIResolution)),
        ("num_resolutions", ctypes.c_uint32),
    ]


class FFICameraList(ctypes.Structure):
    _fields_ = [
        ("cameras", ctypes.POINTER(FFICamera)),
        ("num_cameras", ctypes.c_uint32),
    ]


class FFICameraCaptureFrame(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("pixels", ctypes.POINTER(ctypes.c_uint8)),
    ]


def load_shared_libraries():
    global camera_capture
    global display_surface

    camera_capture = load_camera_capture_library()
    display_surface = load_display_surface_library()


def load_camera_capture_library() -> ctypes.CDLL:
    print("Loading camera capture library...")

    library = load_shared_library("camera_capture")

    library.aethervr_camera_init.argtypes = ()
    library.aethervr_camera_init.restype = None

    library.aethervr_camera_enumerate.argtypes = ()
    library.aethervr_camera_enumerate.restype = ctypes.POINTER(FFICameraList)

    library.aethervr_camera_destroy_list.argtypes = (ctypes.POINTER(FFICameraList),)
    library.aethervr_camera_destroy_list.restype = None

    library.aethervr_camera_open.argtypes = (ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32)
    library.aethervr_camera_open.restype = ctypes.c_void_p

    library.aethervr_camera_capture_frame.argtypes = (ctypes.c_void_p,)
    library.aethervr_camera_capture_frame.restype = ctypes.POINTER(FFICameraCaptureFrame)

    library.aethervr_camera_destroy_frame.argtypes = (ctypes.POINTER(FFICameraCaptureFrame),)
    library.aethervr_camera_destroy_frame.restype = None

    library.aethervr_camera_close.argtypes = (ctypes.c_void_p,)
    library.aethervr_camera_close.restype = None

    library.aethervr_camera_deinit.argtypes = ()
    library.aethervr_camera_deinit.restype = None

    return library


def load_display_surface_library() -> ctypes.CDLL:
    print("Loading display surface library...")

    library = load_shared_library("display_surface")

    library.aethervr_display_surface_create.argtypes = (
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )
    library.aethervr_display_surface_create.restype = ctypes.c_void_p

    library.aethervr_display_surface_register_image.argtypes = (
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_size_t,
        ctypes.c_int64,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint64,
        ctypes.c_uint64,
    )
    library.aethervr_display_surface_register_image.restype = None

    library.aethervr_display_surface_present_image.argtypes = (
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
    )
    library.aethervr_display_surface_present_image.restype = None

    library.aethervr_display_surface_destroy.argtypes = (ctypes.c_void_p,)
    library.aethervr_display_surface_destroy.restype = None

    return library


def load_shared_library(name: str) -> ctypes.CDLL:
    if getattr(sys, "frozen", False):
        directory = Path(sys.executable).parent
    else:
        build_dir_name = f"{platform.banjo_target_name()}-debug"
        project_root = Path(__file__).parents[2]
        directory = project_root / name / "out" / build_dir_name

    if platform.is_windows:
        path = directory / f"aethervr_{name}.dll"
    elif platform.is_linux:
        path = directory / f"libaethervr_{name}.so"
    else:
        path = None

    return ctypes.CDLL(str(path))
