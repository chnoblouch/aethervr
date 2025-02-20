from urllib.request import urlretrieve
from pathlib import Path
from threading import Thread


MODELS_DIR = Path("models")
FACE_LANDMARKER_PATH = MODELS_DIR / "face_landmarker.task"
HAND_LANDMARKER_PATH = MODELS_DIR / "hand_landmarker.task"

BASE_URL = "https://storage.googleapis.com/mediapipe-models"
FACE_LANDMARKER_URL = f"{BASE_URL}/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
HAND_LANDMARKER_URL = f"{BASE_URL}/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

MODELS = [
    (FACE_LANDMARKER_PATH, FACE_LANDMARKER_URL),
    (HAND_LANDMARKER_PATH, HAND_LANDMARKER_URL),
]


def are_all_models_cached():
    for file_path, _ in MODELS:
        if not file_path.exists():
            return False

    return True


def download(on_done):
    thread = Thread(target=lambda: download_sync(on_done))
    thread.start()


def download_sync(on_done):
    for file_path, url in MODELS:
        if file_path.is_file():
            return file_path

        if not MODELS_DIR.is_dir():
            MODELS_DIR.mkdir()

        print(f"Downloading {file_path}...")
        print(f"  URL: {url}")
        print(f"  File path: {file_path}")

        urlretrieve(url, file_path)

    on_done()
