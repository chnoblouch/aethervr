# AetherVR

AetherVR allows you to play VR applications on PC without a VR headset. Your webcam is used to track your movements, which are then translated into virtual headset and controller inputs. These inputs are passed to a VR application via the AetherVR OpenXR runtime.

## Usage

### System-Wide Installation

If you want to use AetherVR with standalone apps (e.g. from Steam), you can install it globally on your system by modifying a registry key. Notice that this will replace your previous OpenXR driver (if you had one). You can set the registry key to the previous value in order to use your previous OpenXR runtime.

1. Open the Windows Registry Editor
2. Navigate to the key ```HKEY_LOCAL_MACHINE\SOFTWARE\Khronos\OpenXR\1```
3. Set the value ```ActiveRuntime``` to the path to ```openxr_runtime.json```
4. Run ```aethervr_tracker.exe```
5. Run your VR application

### Unity Engine

If you don't want to change your OpenXR runtime globally, you can select AetherVR in Unity for use as the play mode OpenXR runtime.

1. Make sure your graphics API is either Vulkan or D3D11
2. Go to ```Edit > Project Settings > XR Plug-in Management > OpenXR```
3. Click ```Play Mode OpenXR Runtime``` and select ```Other```
4. Enter the path to ```openxr_runtime.json```
5. Run ```aethervr_tracker.exe```
6. Enter play mode

### OpenComposite

AetherVR can be used to play SteamVR games by using [OpenComposite](https://gitlab.com/znixian/OpenOVR) as a translation layer from OpenVR calls to OpenXR calls. You should be able to install AetherVR and OpenComposite on your system and it should Just Work. 

## OpenXR Runtime

The OpenXR runtime is a shared library (```aethervr.dll```) written in the Banjo programming language. It currently supports Windows and applications that use Vulkan or D3D11 as their graphics API.

The runtime currently supports these extensions:

| Extension                                     | Version |
| --------------------------------------------- | ------- |
| XR_KHR_D3D11_enable                           | 9       |
| XR_KHR_vulkan_enable                          | 8       |
| XR_KHR_vulkan_enable2                         | 2       |
| XR_KHR_win32_convert_performance_counter_time | 1       |

## Tracker

The AetherVR tracker (```aethervr_tracker.exe```) is a Python application written in Python that uses OpenCV and MediaPipe. It trackslandmarks of the user's head and hands using MediaPipe and sends them to the OpenXR runtime over TCP. The tracking application can be closed by pressing the Escape key.