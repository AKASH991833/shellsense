from __future__ import annotations

import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import ensure_shellsense_dir, get_db_path

logger = get_logger(__name__)

SOCKET_PATH = "/tmp/shellsense-daemon.sock"
PID_PATH = "/tmp/shellsense-daemon.pid"


class DaemonServer:
    def __init__(self, socket_path: str = SOCKET_PATH) -> None:
        self._socket_path = socket_path
        self._server: socket.socket | None = None
        self._running = False
        self._engine: KnowledgeEngine | None = None
        self._start_time: float = 0.0
        self._lock = threading.Lock()

    def start(self) -> None:
        if os.path.exists(self._socket_path):
            os.unlink(self._socket_path)

        db = DatabaseManager(get_db_path())
        db.initialize()
        self._engine = KnowledgeEngine(db)
        self._engine.seed()

        from shellsense.knowledge.discovery_loader import get_discovered_count

        discovered = get_discovered_count(db)
        if discovered > 0:
            logger.info("Daemon loaded with %d discovered commands", discovered)

        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server.bind(self._socket_path)
        self._server.listen(5)
        self._server.settimeout(1.0)
        self._running = True
        self._start_time = time.time()

        os.umask(0)
        os.chmod(self._socket_path, 0o777)

        _write_pid()
        logger.info("Daemon started on %s", self._socket_path)

        self._handle_connections()

    def stop(self) -> None:
        self._running = False
        if self._server:
            try:
                self._server.close()
            except OSError:
                pass
        if os.path.exists(self._socket_path):
            os.unlink(self._socket_path)
        if os.path.exists(PID_PATH):
            os.unlink(PID_PATH)
        logger.info("Daemon stopped")

    def _handle_connections(self) -> None:
        while self._running:
            try:
                if self._server is None:
                    break
                conn, _ = self._server.accept()
                thread = threading.Thread(
                    target=self._handle_client, args=(conn,), daemon=True
                )
                thread.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, conn: socket.socket) -> None:
        try:
            data = conn.recv(65536)
            if not data:
                return
            request = json.loads(data.decode("utf-8"))
            response = self._process_request(request)
            conn.sendall(json.dumps(response).encode("utf-8"))
        except Exception as e:
            logger.error("Daemon handler error: %s", e)
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        req_type = request.get("type", "")

        if req_type == "ping":
            return {"status": "ok", "version": "1.0.0"}

        if req_type == "shutdown":
            threading.Thread(target=self.stop, daemon=True).start()
            return {"status": "shutting_down"}

        if req_type == "status":
            uptime = int(time.time() - self._start_time)
            return {
                "status": "running",
                "pid": os.getpid(),
                "uptime": uptime,
                "socket": self._socket_path,
            }

        if req_type == "stats":
            if not self._engine:
                return {"status": "error", "message": "Engine not loaded"}
            counts = {
                "seeded": 0,
                "discovered": 0,
                "total": 0,
            }
            try:
                cursor = self._engine.db.execute("SELECT COUNT(*) FROM commands")
                counts["seeded"] = int(cursor.fetchone()[0])
                cursor = self._engine.db.execute(
                    "SELECT COUNT(*) FROM discovered_commands"
                )
                counts["discovered"] = int(cursor.fetchone()[0])
            except Exception:
                pass
            counts["total"] = counts["seeded"] + counts["discovered"]
            uptime = int(time.time() - self._start_time)
            return {
                "status": "ok",
                "counts": counts,
                "uptime": uptime,
            }

        if req_type == "suggest":
            if not self._engine:
                return {"status": "error", "message": "Engine not loaded"}
            partial = request.get("partial", "")
            limit = request.get("limit", 5)
            suggestions = self._engine.suggest(partial, limit=limit)
            results: list[dict[str, object]] = []
            for s in suggestions:
                results.append(
                    {
                        "name": str(s.get("name", "")),
                        "description": str(s.get("short_description", "")),
                        "category": str(s.get("category", "")),
                        "match_type": str(s.get("_match_type", "")),
                    }
                )
            prediction = results[0]["name"] if results else ""
            return {
                "status": "ok",
                "suggestions": results,
                "prediction": prediction,
            }

        if req_type == "predict":
            if not self._engine:
                return {"status": "error", "message": "Engine not loaded"}
            partial = request.get("partial", "")
            limit = request.get("limit", 5)
            predictions = self._engine.predict(partial, limit=limit)
            results = []
            for p in predictions:
                results.append(
                    {
                        "name": str(p.get("name", "")),
                        "description": str(p.get("short_description", "")),
                        "category": str(p.get("category", "")),
                    }
                )
            return {
                "status": "ok",
                "predictions": results,
                "prediction": results[0]["name"] if results else "",
            }

        if req_type == "search":
            if not self._engine:
                return {"status": "error", "message": "Engine not loaded"}
            query = request.get("query", "")
            limit = request.get("limit", 10)
            results = self._engine.search(query, limit=limit)
            return {
                "status": "ok",
                "results": [
                    {
                        "name": str(r.get("name", "")),
                        "description": str(r.get("short_description", "")),
                        "category": str(r.get("category", "")),
                    }
                    for r in results
                ],
            }

        return {"status": "error", "message": f"Unknown type: {req_type}"}


def _write_pid() -> None:
    with open(PID_PATH, "w") as f:
        f.write(str(os.getpid()))


def is_running() -> bool:
    if not os.path.exists(PID_PATH):
        return False
    if not os.path.exists(SOCKET_PATH):
        return False
    try:
        with open(PID_PATH) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def get_daemon_pid() -> int | None:
    if not os.path.exists(PID_PATH):
        return None
    try:
        with open(PID_PATH) as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        return None
