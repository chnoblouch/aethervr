# AetherVR

AetherVR is a tool to run VR games/applications on PC without a VR headset. The
system tracks your head and hands using nothing but a webcam and translates the
results into virtual headset and controller inputs that are passed on to VR
applications. This is done using a custom OpenXR runtime that tricks
applications into thinking they are connected to actual VR hardware.

> [!CAUTION]
> PLEASE NOTE: This is just a proof of concept and not a replacement
> for a real VR headset. The hand tracking is very janky and aiming at things or
> grabbing them is still pretty hard. Don't use this to play actual VR games.

<p align="center">
    <img src="https://marinohimself.ch/aethervr/screenshot.png" alt="AetherVR Screenshot">
</p>

## Setup

### System-Wide Installation

If you want to use AetherVR with standalone apps (e.g. from Steam), you can
install it globally by setting AetherVR as the system OpenXR runtime. Note that
this will replace your previous OpenXR runtime (if you had one) and that all
OpenXR apps will use AetherVR from now on.

1. Run `aethervr_tracker.exe` as administrator
2. Click `Set AetherVR as OpenXR Runtime`
3. Run your VR application

To use your previous OpenXR runtime, open the settings of your VR vendor's app
and look for a button that says something like 'set myself as the active OpenXR
runtime'.

### Unity Engine

If you don't want to change your OpenXR runtime globally, you can select
AetherVR in Unity for use as the play mode OpenXR runtime.

1. Make sure your graphics API is either Vulkan or D3D11
2. Go to `Edit > Project Settings > XR Plug-in Management > OpenXR`
3. Click `Play Mode OpenXR Runtime` and select `Other`
4. Enter the path to `openxr_runtime.json`
5. Run `aethervr_tracker.exe`
6. Enter play mode

### OpenComposite

AetherVR can be used to play SteamVR games by using
[OpenComposite](https://gitlab.com/znixian/OpenOVR) as a translation layer from
OpenVR calls to OpenXR calls. You should be able to install AetherVR and
OpenComposite on your system and it should just work, though crashes are to be
expected.

## Usage

See [this guide](docs/usage.md).

## Building Manually

These are the steps you need to follow to build and run AetherVR manually.

### Windows

#### Prerequisites

- Python
- Visual Studio Build Tools
- [Banjo](https://chnoblouch.github.io/banjo-lang/getting_started.html)

#### Building and Running

Clone this repository, open it in PowerShell, and run these commands:

```powershell
cd openxr_runtime
banjo2 build
cp openxr_runtime.json out\x86_64-windows-msvc\openxr_runtime.json
cd ..\display_surface
banjo2 build
cd ..\camera_capture
banjo2 build
cd ..\tracker
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python aethervr_tracker.py
```

## System Components

### OpenXR Runtime

The OpenXR runtime (`aethervr.dll`) is a shared library written in the [Banjo
programming language](https://chnoblouch.github.io/banjo-lang/). It currently
supports Windows and applications that use Vulkan or D3D11 as their graphics
API.

The runtime currently implements these extensions:

| Extension                                     | Version |
| --------------------------------------------- | ------- |
| XR_KHR_D3D11_enable                           | 9       |
| XR_KHR_vulkan_enable2                         | 2       |
| XR_KHR_win32_convert_performance_counter_time | 1       |
| XR_KHR_composition_layer_depth                | 6       |

### Tracker

The AetherVR tracker (`aethervr_tracker.exe`) is an application written in
Python that uses OpenCV, MediaPipe, and Qt. It tracks landmarks of the users
head and hands using MediaPipe, converts them to virtual headset and controller
inputs, and sends them to the OpenXR runtime over TCP.
