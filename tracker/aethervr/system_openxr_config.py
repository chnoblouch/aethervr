from pathlib import Path
import winreg
import json
import sys


class SystemOpenXRConfig:
    _REG_KEY_NAME = "SOFTWARE\\Khronos\\OpenXR\\1"
    _REG_VALUE_NAME = "ActiveRuntime"
    _AETHERVR_MANIFEST_NAME = "openxr_runtime.json"

    def active_runtime_name(self):
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKeyEx(reg, SystemOpenXRConfig._REG_KEY_NAME, 0, winreg.KEY_QUERY_VALUE)
            current_manifest_path, _ = winreg.QueryValueEx(key, SystemOpenXRConfig._REG_VALUE_NAME)
            winreg.CloseKey(key)

            with open(current_manifest_path) as f:
                current_manifest = json.load(f)

            return current_manifest["runtime"]["name"]
        except Exception:
            return None

    def is_aethervr(self, runtime_name):
        return runtime_name == "AetherVR"

    def activate_aethervr(self):
        path = self._path_to_aethervr_manifest()

        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.CreateKeyEx(reg, SystemOpenXRConfig._REG_KEY_NAME, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, SystemOpenXRConfig._REG_VALUE_NAME, 0, winreg.REG_SZ, str(path))
            winreg.CloseKey(key)
            winreg.CloseKey(reg)

            return True
        except Exception:
            return False

    def _path_to_aethervr_manifest(self):
        if getattr(sys, "frozen", False):
            package_root = Path(sys.executable).parent
            return package_root / SystemOpenXRConfig._AETHERVR_MANIFEST_NAME
        else:
            project_root = Path(__file__).parents[2]
            build_dir = project_root / "openxr_runtime" / "out" / "x86_64-windows-msvc-debug"
            return project_root / build_dir / SystemOpenXRConfig._AETHERVR_MANIFEST_NAME
