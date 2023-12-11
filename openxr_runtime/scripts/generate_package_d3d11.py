import subprocess
from pathlib import Path
import os
import shutil


def generate():
    os.chdir(Path(__file__).parent / "d3d11")
    subprocess.run(["banjo", "bindgen", "--generator", "bindgen.py", "d3d11.c"])
    
    package_dir = Path("../../packages/d3d11")
    package_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy("package.json", package_dir)

    src_dir = package_dir / "src"
    src_dir.mkdir(exist_ok=True)
    shutil.move("bindings.bnj", src_dir / "d3d11.bnj")


if __name__ == "__main__":
    generate()
