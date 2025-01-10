from pathlib import Path
import json
import sys
import platform
import os


is_windows = platform.system() == "Windows"
is_linux = platform.system() == "Linux"


class SystemOpenXRConfig:
    _REG_KEY_NAME = "SOFTWARE\\Khronos\\OpenXR\\1"
    _REG_VALUE_NAME = "ActiveRuntime"

    def is_aethervr(self, runtime_name):
        return runtime_name == "AetherVR"

    def active_runtime_name(self):
        if is_windows:
            manifest_path = self._find_current_manifest_windows()
        elif is_linux:
            manifest_path = self._find_current_manifest_linux()
        else:
            manifest_path = None
        
        if not manifest_path:
            return None

        with open(manifest_path) as f:
            current_manifest = json.load(f)

        runtime_info = current_manifest["runtime"]
        name = runtime_info.get("name")
        library_path = Path(runtime_info["library_path"])

        if name is not None:
            return name
        elif library_path.suffix == ".dll":
            return str(library_path.stem)
        elif library_path.suffix == ".so" and library_path.name.startswith("lib"):
            return str(library_path.stem[3:])
        else:
            return str(library_path)

    def _find_current_manifest_windows(self):
        import winreg

        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKeyEx(reg, SystemOpenXRConfig._REG_KEY_NAME, 0, winreg.KEY_QUERY_VALUE)
            current_manifest_path, _ = winreg.QueryValueEx(key, SystemOpenXRConfig._REG_VALUE_NAME)
            winreg.CloseKey(key)

            return Path(current_manifest_path)
        except Exception:
            return None

    def _find_current_manifest_linux(self):
        search_dirs = [
            self._get_xdg_config_home(),
            *self._get_xdg_config_dirs(),
            Path("/etc"),
        ]
        
        for search_dir in search_dirs:
            path = search_dir / "openxr" / "1" / "active_runtime.x86_64.json"
            if path.is_file():
                return path

            path = search_dir / "openxr" / "1" / "active_runtime.json"
            if path.is_file():
                return path

        return None

    def activate_aethervr(self):
        if is_windows:
            return self._activate_aethervr_windows()
        elif is_linux:
            return self._activate_aethervr_linux()

    def _activate_aethervr_windows(self):
        import winreg

        path = self._aethervr_runtime_dir() / "openxr_runtime.json"

        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.CreateKeyEx(reg, SystemOpenXRConfig._REG_KEY_NAME, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, SystemOpenXRConfig._REG_VALUE_NAME, 0, winreg.REG_SZ, str(path))
            winreg.CloseKey(key)
            winreg.CloseKey(reg)

            return True
        except Exception:
            return False

    def _activate_aethervr_linux(self):
        manifest = {
            "file_format_version": "1.0.0",
            "runtime": {
                "name": "AetherVR",
                "library_path": str(self._aethervr_runtime_dir() / "libaethervr.so"),
            },
        }

        path = self._get_xdg_config_home() / "openxr" / "1" / "active_runtime.json"

        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        with open(path, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")

        return True

    def _aethervr_runtime_dir(self):
        if getattr(sys, "frozen", False):
            package_root = Path(sys.executable).parent
            return package_root
        else:
            if is_windows:
                build_dir_name = "x86_64-windows-msvc-debug"
            elif is_linux:
                build_dir_name = "x86_64-linux-gnu-debug"
            else:
                build_dir_name = None

            project_root = Path(__file__).parents[2]
            build_dir = project_root / "openxr_runtime" / "out" / build_dir_name
            return project_root / build_dir

    def _get_xdg_config_home(self):
        value = os.environ.get("XDG_CONFIG_HOME")

        if value is not None:
            return Path(value)
        else:
            return Path.home() / ".config"

    def _get_xdg_config_dirs(self):
        value = os.environ.get("XDG_CONFIG_DIRS")

        if value is not None:
            return [Path(path) for path in value.split(":")]
        else:
            return [Path("/etc/xdg")]
