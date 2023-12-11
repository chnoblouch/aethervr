import subprocess
from pathlib import Path
import os
import shutil


def generate():
    os.chdir(Path(__file__).parent / "xr")

    for repo in ("OpenXR-SDK", "OpenXR-SDK-Source", "Vulkan-Headers"):
        if not Path(repo).exists():
            subprocess.run(["git", "clone", "https://github.com/KhronosGroup/" + repo])

    subprocess.run(
        [
            "banjo",
            "bindgen",
            "--generator",
            "bindgen.py",
            "-IOpenXR-SDK/include",
            "-IOpenXR-SDK-Source/src/common",
            "-IVulkan-Headers/include",
            "xr.c",
        ]
    )

    package_dir = Path("../../packages/xr")
    package_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy("package.json", package_dir)

    src_dir = package_dir / "src"
    src_dir.mkdir(exist_ok=True)
    shutil.move("bindings.bnj", src_dir / "xr.bnj")


if __name__ == "__main__":
    generate()
