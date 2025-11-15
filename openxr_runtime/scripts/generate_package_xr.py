import subprocess
from pathlib import Path
import os
import shutil


def generate():
    os.chdir(Path(__file__).parent / "xr")

    for repo in ("OpenXR-SDK", "Vulkan-Headers"):
        if not Path(repo).exists():
            subprocess.run(["git", "clone", "https://github.com/KhronosGroup/" + repo])

    subprocess.run(
        [
            "banjo2",
            "bindgen",
            "--generator",
            "bindgen.py",
            "-IOpenXR-SDK/include",
            "-IVulkan-Headers/include",
            "xr.c",
        ]
    )

    package_dir = Path("../../packages/xr")
    package_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy("banjo.json", package_dir)

    src_dir = package_dir / "src"
    src_dir.mkdir(exist_ok=True)
    shutil.move("bindings.bnj", src_dir / "xr.bnj")


if __name__ == "__main__":
    generate()
