from pathlib import Path
import ctypes


class DisplaySurface:
    _library = None

    def __init__(self, graphics_api, window):
        if not DisplaySurface._library:
            print("Loading display surface library...")
            DisplaySurface._library = DisplaySurface._load_library()

        self.handle = DisplaySurface._library.aethervr_display_surface_create(
            graphics_api, window
        )

    def register_image(self, data):
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
        path = (
            Path(__file__).parents[2]
            / "display_surface"
            / "out"
            / "x86_64-windows-msvc-debug"
            / "aethervr_display_surface.dll"
        )
        library = ctypes.CDLL(str(path))

        library.aethervr_display_surface_create.argtypes = (
            ctypes.c_uint32,
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
