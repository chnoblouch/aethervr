from pathlib import Path
import ctypes
import sys

from aethervr import platform


class DisplaySurface:
    _library = None

    def __init__(self):
        if not DisplaySurface._library:
            print("Loading display surface library...")
            DisplaySurface._library = DisplaySurface._load_library()

        self.handle = None
        self.graphics_api = None

    def create(self, graphics_api, display, window):
        if graphics_api == self.graphics_api:
            return
        
        if self.handle is not None:
            DisplaySurface._library.aethervr_display_surface_destroy(self.handle)

        self.handle = DisplaySurface._library.aethervr_display_surface_create(
            graphics_api,
            display,
            window,
        )

        self.graphics_api = graphics_api

    def register_image(self, data):
        assert self.handle

        DisplaySurface._library.aethervr_display_surface_register_image(
            self.handle,
            data.id,
            data.process_id,
            data.shared_handle,
            data.format,
            data.width,
            data.height,
            data.array_size,
            data.mip_count,
            data.opaque_value_0,
            data.opaque_value_1,
        )

    def present_image(self, data):
        assert self.handle

        DisplaySurface._library.aethervr_display_surface_present_image(
            self.handle,
            data.id,
            data.x,
            data.y,
            data.width,
            data.height,
            data.array_index,
        )

    @staticmethod
    def _load_library():
        if getattr(sys, "frozen", False):
            directory = Path(sys.executable).parent
        else:
            build_dir_name = f"{platform.banjo_target_name()}-debug"
            project_root = Path(__file__).parents[2]
            directory = project_root / "display_surface" / "out" / build_dir_name

        if platform.is_windows:
            path = directory / "aethervr_display_surface.dll"
        elif platform.is_linux:
            path = directory / "libaethervr_display_surface.so"
        else:
            path = None

        library = ctypes.CDLL(str(path))

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
