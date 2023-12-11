from urllib.request import urlretrieve
from pathlib import Path


MODELS_DIR = Path("models")


def download(file_name, url):
    file_path = MODELS_DIR / file_name

    if file_path.is_file():
        return file_path

    if not MODELS_DIR.is_dir():
        MODELS_DIR.mkdir()

    print(f"Downloading {file_name}...")
    print(f"  URL: {url}")
    print(f"  File path: {file_path}")
    
    urlretrieve(url, file_path)

    print("Done")

    return file_path