"""
QAForge Windows Launcher
Starts the FastAPI backend and opens the app in the default browser.
Packaged by PyInstaller into a single .exe file.
"""

import sys
import os
import threading
import webbrowser
import time
import socket
from pathlib import Path


# ── Resolve paths whether running as .exe or raw Python ──────────────────────
if getattr(sys, "frozen", False):
    # Running inside PyInstaller bundle
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Running from source (for development)
    BASE_DIR = Path(__file__).parent.parent / "qaforge-v5"

# Add the project root to sys.path so backend imports work
sys.path.insert(0, str(BASE_DIR))

# Point frontend static files to the bundled location
os.environ.setdefault("QAFORGE_FRONTEND_DIR", str(BASE_DIR / "frontend"))


# ── Port availability check ───────────────────────────────────────────────────
def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) != 0


def _find_free_port(start: int = 8000) -> int:
    for port in range(start, start + 20):
        if _port_free(port):
            return port
    return start


# ── Server thread ─────────────────────────────────────────────────────────────
def run_server(port: int):
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=port,
        log_level="error",
        reload=False,
    )


# ── Wait for server then open browser ────────────────────────────────────────
def open_browser(port: int, delay: float = 1.5):
    time.sleep(delay)
    webbrowser.open(f"http://127.0.0.1:{port}")


# ── Optional: System tray icon (requires pystray + Pillow) ───────────────────
def run_tray(port: int):
    try:
        import pystray
        from PIL import Image, ImageDraw

        # Draw a simple coloured square as the tray icon
        img = Image.new("RGB", (64, 64), color="#6C47FF")
        draw = ImageDraw.Draw(img)
        draw.text((14, 20), "QA", fill="white")

        def on_open(_icon, _item):
            webbrowser.open(f"http://127.0.0.1:{port}")

        def on_quit(icon, _item):
            icon.stop()
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Open QAForge", on_open, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit),
        )
        icon = pystray.Icon("QAForge", img, "QAForge is running", menu)
        icon.run()
    except ImportError:
        # pystray not installed — just keep the process alive
        while True:
            time.sleep(60)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PORT = _find_free_port(8000)

    # Start server in background thread
    server_thread = threading.Thread(target=run_server, args=(PORT,), daemon=True)
    server_thread.start()

    # Open browser after short delay
    browser_thread = threading.Thread(target=open_browser, args=(PORT,), daemon=True)
    browser_thread.start()

    # Run tray icon on main thread (blocking)
    run_tray(PORT)
