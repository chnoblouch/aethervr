from aethervr import ffi
from aethervr import platform


class DisplaySurface:
    def __init__(self):
        self.handle = None
        self.graphics_api = None

    def create(self, graphics_api, display, window):
        if not DisplaySurface.is_supported():
            return

        if graphics_api == self.graphics_api:
            return
        
        if self.handle is not None:
            ffi.display_surface.aethervr_display_surface_destroy(self.handle)

        self.handle = ffi.display_surface.aethervr_display_surface_create(
            graphics_api,
            display,
            window,
        )

        self.graphics_api = graphics_api

    def register_image(self, data):
        if not DisplaySurface.is_supported():
            return

        assert self.handle

        ffi.display_surface.aethervr_display_surface_register_image(
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
        if not DisplaySurface.is_supported():
            return

        assert self.handle

        ffi.display_surface.aethervr_display_surface_present_image(
            self.handle,
            data.id,
            data.x,
            data.y,
            data.width,
            data.height,
            data.array_index,
        )

    @staticmethod
    def is_supported():
        return platform.is_windows or platform.is_linux
