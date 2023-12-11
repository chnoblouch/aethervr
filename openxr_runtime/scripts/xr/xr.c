#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#define D3D11_NO_HELPERS
#define CINTERFACE
#include <d3d11_1.h>

#define XR_DEFINE_HANDLE(object) typedef void *object;
#include "loader_interfaces.h"

#define XR_USE_GRAPHICS_API_OPENGL
#define XR_USE_GRAPHICS_API_VULKAN
#define XR_USE_GRAPHICS_API_D3D11
#define XR_USE_PLATFORM_WIN32
#define XR_USE_PLATFORM_XLIB
#define XR_USE_PLATFORM_XCB

#include "vulkan/vulkan.h"
#include "openxr/openxr_platform.h"
