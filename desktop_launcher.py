"""Desktop launcher used by the packaged macOS and Windows applications."""

import os
from pathlib import Path
import socket
import sys
import threading
import time
from urllib.request import urlopen


def data_directory() -> Path:
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.getenv("LOCALAPPDATA", Path.home()))
    else:
        root = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    directory = root / "Webmark"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def available_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_until_ready(url: str) -> None:
    for _ in range(100):
        try:
            with urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Webmark failed to start")


def main() -> None:
    os.environ.pop("TURSO_DATABASE_URL", None)
    os.environ.pop("TURSO_AUTH_TOKEN", None)
    os.environ["WEBMARK_DATA_DIR"] = str(data_directory())

    import uvicorn
    import webview
    from backend.app.main import app

    port = available_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{port}"
    wait_until_ready(f"{base_url}/webmark/health")
    webview.create_window("Webmark", base_url, width=1180, height=800, min_size=(760, 560))
    webview.start()

    server.should_exit = True
    server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
