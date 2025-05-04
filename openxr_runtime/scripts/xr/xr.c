#if _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>

#  define D3D11_NO_HELPERS
#  define CINTERFACE
#  include <d3d11_1.h>
#elif __linux__
typedef signed char int8_t;
typedef unsigned char uint8_t;
typedef short int16_t;
typedef unsigned short uint16_t;
typedef int int32_t;
typedef unsigned int uint32_t;
typedef long long int64_t;
typedef unsigned long long uint64_t;
typedef unsigned long long size_t;
#endif

#define XR_DEFINE_HANDLE(object) typedef void *object;

#if _WIN32
#  define XR_USE_PLATFORM_WIN32
#  define XR_USE_GRAPHICS_API_D3D11
#  define XR_USE_GRAPHICS_API_VULKAN

#  include <vulkan/vulkan.h>
#elif __linux__
#  define XR_USE_PLATFORM_XLIB
#  define XR_USE_PLATFORM_XCB
#  define XR_USE_GRAPHICS_API_VULKAN

#  include <vulkan/vulkan.h>
#elif __APPLE__
#  define XR_USE_GRAPHICS_API_METAL
#endif

#include <openxr/openxr.h>
#include <openxr/openxr_platform.h>
#include <openxr/openxr_loader_negotiation.h>
