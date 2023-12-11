from pathlib import Path

import generate_package_xr as xr
import generate_package_d3d11 as d3d11


if not Path("packages/xr").is_dir():
    print("Generating OpenXR package")
    xr.generate()

if not Path("packages/d3d11").is_dir():
    print("Generating D3D11 package")
    d3d11.generate()
