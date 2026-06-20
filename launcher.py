"""
Outreach Console — entry point for both native run and PyInstaller bundle.

  Native:     python launcher.py
  Bundled:    ./OutreachConsole   (Linux)
              OutreachConsole.exe (Windows)
"""
import sys
import os
import time
import threading
import webbrowser
import logging

# When frozen by PyInstaller, _MEIPASS holds extracted files.
# Ensure the project root is on sys.path so `app` is importable.
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)

from app.paths import DATA_DIR, LOGS_DIR  # noqa: E402 — must come after path fix

PORT = 5000

# Log to both console and a persistent file in the user's data dir
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOGS_DIR / "outreach.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _open_browser():
    time.sleep(2.5)
    webbrowser.open(f"http://localhost:{PORT}")


def main():
    from app.main import app  # import here so logging is set up first

    logger.info("Starting Outreach Console on port %d ...", PORT)
    logger.info("Data directory: %s", DATA_DIR)

    t = threading.Thread(target=_open_browser, daemon=True)
    t.start()

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║       TKT Outreach Console           ║")
    print(f"  ║   Running at http://localhost:{PORT}   ║")
    print("  ║   Close this window to quit.         ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    app.run(
        host="127.0.0.1",
        port=PORT,
        debug=False,
        threaded=True,
        use_reloader=False,   # must be False inside a frozen exe
    )


if __name__ == "__main__":
    main()
