from pathlib import Path
import sys
import os


def _data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home()
    d = base / "OutreachConsole"
    d.mkdir(parents=True, exist_ok=True)
    return d


DATA_DIR      = _data_dir()
UPLOADS_DIR   = DATA_DIR / "uploads"
IMAGES_DIR    = DATA_DIR / "images"
DOCUMENTS_DIR = DATA_DIR / "documents"
CHROME_DIR    = DATA_DIR / "chrome_profile"
LOGS_DIR      = DATA_DIR / "logs"
RESIZED_IMAGE = str(DATA_DIR / "resized_flyer.jpeg")

for _d in (UPLOADS_DIR, IMAGES_DIR, DOCUMENTS_DIR, CHROME_DIR, LOGS_DIR):
    _d.mkdir(exist_ok=True)
