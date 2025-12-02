import os
import subprocess
import platform
import shutil
from pathlib import Path

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)

    is_windows = platform.system() == "Windows"
    is_linux = platform.system() == "Linux"
    is_macos = platform.system() == "Darwin"

    if is_windows:
        banjo_target_name = "x86_64-windows-msvc"
    elif is_linux:
        banjo_target_name = "x86_64-linux-gnu"
    elif is_macos:
        banjo_target_name = "aarch64-macos"

    tracker_path = Path("tracker").absolute()
    venv_path = tracker_path / "venv"
    tracker_build_path = tracker_path / "build"

    tracker_build_path.mkdir(exist_ok=True)

    if is_windows:
        pyinstaller_path = venv_path / "Scripts" / "pyinstaller"
        tracker_packages_path = venv_path / "Lib" / "site-packages"
    else:
        pyinstaller_path = venv_path / "bin" / "pyinstaller"
        tracker_packages_path = venv_path / "lib" / "python3.12" / "site-packages"

    pyinstaller_command = [pyinstaller_path, "../aethervr_tracker.py", "--noconfirm"]

    if is_windows:
        pyinstaller_command = [
            pyinstaller_path,
            "../aethervr_tracker.py",
            "--windowed",
            "--icon",
            "NONE",
            "--noconfirm",
        ]
    elif is_linux:
        pyinstaller_command = [
            pyinstaller_path,
            "../aethervr_tracker.py",
        ]
    elif is_macos:
        pyinstaller_command = [
            pyinstaller_path,
            "../aethervr_tracker.py",
            "--windowed",
            "--noconfirm",
        ]

    subprocess.run(pyinstaller_command, cwd=str(tracker_build_path))

    if is_windows:
        package_path = Path("aethervr-x86_64-windows")
    elif is_linux:
        package_path = Path("aethervr-x86_64-linux")
    elif is_macos:
        package_path = Path("aethervr-aarch64-macos")

    if package_path.exists():
        shutil.rmtree(package_path)

    package_path.mkdir()

    tracker_dist_path = tracker_build_path / "dist"

    if is_windows:
        runtime_path = Path(
            "openxr_runtime",
            "out",
            f"{banjo_target_name}-debug/aethervr.dll",
        )

        runtime_json_path = Path("openxr_runtime", "openxr_runtime_windows.json")
        exe_path = tracker_dist_path / "aethervr_tracker" / "aethervr_tracker.exe"
        internal_path = tracker_dist_path / "aethervr_tracker" / "_internal"

        camera_capture_lib_path = Path(
            "camera_capture",
            "out",
            f"{banjo_target_name}-debug/aethervr_camera_capture.dll",
        )

        display_surface_lib_path = Path(
            "display_surface",
            "out",
            f"{banjo_target_name}-debug/aethervr_display_surface.dll",
        )

        runtime_path = Path(
            "openxr_runtime",
            "out",
            f"{banjo_target_name}-debug/aethervr.dll",
        )
    elif is_linux:
        runtime_path = Path(
            "openxr_runtime",
            "out",
            f"{banjo_target_name}-debug/libaethervr.so",
        )

        runtime_json_path = Path("openxr_runtime", "openxr_runtime_linux.json")
        exe_path = tracker_dist_path / "aethervr_tracker" / "aethervr_tracker"
        internal_path = tracker_dist_path / "aethervr_tracker" / "_internal"

        camera_capture_lib_path = Path(
            "camera_capture",
            "out",
            f"{banjo_target_name}-debug/libaethervr_camera_capture.so",
        )

        display_surface_lib_path = Path(
            "display_surface",
            "out",
            f"{banjo_target_name}-debug/libaethervr_display_surface.so",
        )
    elif is_macos:
        runtime_path = Path(
            "openxr_runtime",
            "out",
            f"{banjo_target_name}-debug/libaethervr.dylib",
        )

        runtime_json_path = Path("openxr_runtime", "openxr_runtime_macos.json")
        exe_path = tracker_dist_path / "aethervr_tracker" / "aethervr_tracker"
        internal_path = tracker_dist_path / "aethervr_tracker" / "_internal"

        camera_capture_lib_path = Path(
            "camera_capture",
            "out",
            f"{banjo_target_name}-debug/libaethervr_camera_capture.dylib",
        )

        display_surface_lib_path = Path(
            "display_surface",
            "out",
            f"{banjo_target_name}-debug/libaethervr_display_surface.dylib",
        )

    shutil.copy(runtime_path, package_path)
    shutil.copy(runtime_json_path, package_path / "openxr_runtime.json")
    shutil.copy(exe_path, package_path)
    shutil.copytree(internal_path, package_path / "_internal")
    shutil.copy(camera_capture_lib_path, package_path)
    shutil.copy(display_surface_lib_path, package_path)
