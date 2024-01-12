#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#define D3D11_NO_HELPERS
#define CINTERFACE
#include <d3d11_1.h>

#define XR_DEFINE_HANDLE(object) typedef void *object;
#define XR_USE_GRAPHICS_API_OPENGL
#define XR_USE_GRAPHICS_API_VULKAN
#define XR_USE_GRAPHICS_API_D3D11
#define XR_USE_PLATFORM_WIN32
#define XR_USE_PLATFORM_XLIB
#define XR_USE_PLATFORM_XCB

#include "openxr/openxr.h"
#include "openxr/openxr_loader_negotiation.h"
#include "vulkan/vulkan.h"
#include "openxr/openxr_platform.h"
