from __future__ import annotations

import json
import os
import socket
from typing import Any

from shellsense.daemon.server import SOCKET_PATH

TIMEOUT = 5.0


class DaemonClient:
    def __init__(self, socket_path: str = SOCKET_PATH) -> None:
        self._socket_path = socket_path

    def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        if not os.path.exists(self._socket_path):
            return {"status": "error", "message": "Daemon not running"}
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT)
            sock.connect(self._socket_path)
            sock.sendall(json.dumps(request).encode("utf-8"))
            data = sock.recv(65536)
            sock.close()
            result: dict[str, Any] = json.loads(data.decode("utf-8"))
            return result
        except socket.timeout:
            return {"status": "error", "message": "Daemon timed out"}
        except ConnectionRefusedError:
            return {"status": "error", "message": "Daemon not running"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def ping(self) -> dict[str, Any]:
        return self.send_request({"type": "ping"})

    def status(self) -> dict[str, Any]:
        return self.send_request({"type": "status"})

    def stats(self) -> dict[str, Any]:
        return self.send_request({"type": "stats"})

    def shutdown(self) -> dict[str, Any]:
        return self.send_request({"type": "shutdown"})

    def suggest(self, partial: str, limit: int = 5) -> dict[str, Any]:
        return self.send_request(
            {"type": "suggest", "partial": partial, "limit": limit}
        )

    def predict(self, partial: str, limit: int = 5) -> dict[str, Any]:
        return self.send_request(
            {"type": "predict", "partial": partial, "limit": limit}
        )

    def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        return self.send_request({"type": "search", "query": query, "limit": limit})

    def get_prediction(self, partial: str) -> str:
        resp = self.suggest(partial, limit=1)
        if resp.get("status") == "ok" and resp.get("prediction"):
            prediction = str(resp["prediction"])
            if prediction.lower().startswith(partial.lower()):
                return prediction
            return ""
        return ""
