from pathlib import Path
import generate_package_xr as xr


if not Path("packages/xr").is_dir():
    print("Generating OpenXR package")
    xr.generate()
