from __future__ import annotations

import json
import os
import signal
import socket
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import ensure_shellsense_dir, get_db_path

logger = get_logger(__name__)

SOCKET_PATH = "/tmp/shellsense-daemon.sock"
PID_PATH = "/tmp/shellsense-daemon.pid"


def _to_score(val: object, default: float = 0.0) -> float:
    try:
        return float(str(val)) if val is not None else default
    except (ValueError, TypeError):
        return default


class DaemonServer:
    def __init__(self, socket_path: str = SOCKET_PATH) -> None:
        self._socket_path = socket_path
        self._server: socket.socket | None = None
        self._running = False
        self._engine: KnowledgeEngine | None = None
        self._start_time: float = 0.0
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()

    def start(self) -> None:
        if os.path.exists(PID_PATH):
            try:
                with open(PID_PATH) as f:
                    old_pid = int(f.read().strip())
                os.kill(old_pid, 0)
                logger.error("Daemon already running (PID %d)", old_pid)
                sys.exit(1)
            except (OSError, ValueError):
                logger.warning("Stale PID file found, cleaning up")
                self._cleanup_stale()

        if os.path.exists(self._socket_path):
            try:
                conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                conn.settimeout(0.5)
                conn.connect(self._socket_path)
                conn.close()
                logger.error("Daemon socket already in use")
                sys.exit(1)
            except (socket.error, OSError):
                logger.warning("Stale socket found, cleaning up")
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

        os.chmod(self._socket_path, 0o777)

        self._write_pid()
        logger.info("Daemon started on %s", self._socket_path)

        self._handle_connections()

    def stop(self) -> None:
        self._running = False
        self._shutdown_event.set()
        if self._server:
            try:
                self._server.close()
            except OSError:
                pass
        self._cleanup_stale()

    def _cleanup_stale(self) -> None:
        if os.path.exists(self._socket_path):
            try:
                os.unlink(self._socket_path)
            except OSError:
                pass
        if os.path.exists(PID_PATH):
            try:
                os.unlink(PID_PATH)
            except OSError:
                pass
        logger.info("Cleaned up stale daemon artifacts")

    def _write_pid(self) -> None:
        with open(PID_PATH, "w") as f:
            f.write(str(os.getpid()))

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

    def _send_response(self, conn: socket.socket, data: dict[str, Any]) -> None:
        try:
            conn.sendall(json.dumps(data).encode("utf-8"))
        except Exception:
            pass

    def _handle_client(self, conn: socket.socket) -> None:
        try:
            data = conn.recv(65536)
            if not data:
                self._send_response(conn, {"success": False, "error": "Empty request"})
                return
            try:
                request = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError as e:
                self._send_response(
                    conn, {"success": False, "error": f"Invalid JSON: {e}"}
                )
                return
            response = self._process_request(request)
            self._send_response(conn, response)
        except socket.timeout:
            self._send_response(conn, {"success": False, "error": "Socket timeout"})
        except Exception as e:
            logger.error("Daemon handler error: %s\n%s", e, traceback.format_exc())
            self._send_response(conn, {"success": False, "error": str(e)})
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        req_type = request.get("type") or request.get("action", "")
        query = request.get("partial") or request.get("query") or ""
        start = time.time()

        try:
            if req_type == "ping":
                result = {"success": True, "status": "ok", "version": "1.0.0"}

            elif req_type == "shutdown":
                self._running = False
                self._shutdown_event.set()
                if self._server:
                    try:
                        self._server.close()
                    except OSError:
                        pass
                self._cleanup_stale()

                def delayed_stop() -> None:
                    time.sleep(0.5)
                    for _ in range(10):
                        if not self._running:
                            break
                        time.sleep(0.1)

                threading.Thread(target=delayed_stop, daemon=True).start()
                result = {"success": True, "status": "shutting_down"}

            elif req_type == "status":
                uptime = int(time.time() - self._start_time)
                result = {
                    "success": True,
                    "status": "running",
                    "pid": os.getpid(),
                    "uptime": uptime,
                    "socket": self._socket_path,
                }

            elif req_type == "stats":
                if not self._engine:
                    return {"success": False, "error": "Engine not loaded"}
                counts = {"seeded": 0, "discovered": 0, "total": 0}
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
                result = {
                    "success": True,
                    "counts": counts,
                    "uptime": uptime,
                }

            elif req_type == "suggest":
                if not self._engine:
                    return {"success": False, "error": "Engine not loaded"}
                partial = request.get("partial", "")
                limit = request.get("limit", 5)
                suggestions = self._engine.suggest(partial, limit=limit)
                results: list[dict[str, object]] = []
                for s in suggestions:
                    results.append(
                        {
                            "text": str(s.get("name", "")),
                            "score": _to_score(s.get("_score", 0)),
                            "description": str(s.get("short_description", "")),
                            "category": str(s.get("category", "")),
                            "match_type": str(s.get("_match_type", "")),
                        }
                    )
                prediction = results[0]["text"] if results else ""
                result = {
                    "success": True,
                    "query": partial,
                    "suggestions": results,
                    "prediction": prediction,
                }

            elif req_type == "predict":
                if not self._engine:
                    return {"success": False, "error": "Engine not loaded"}
                partial = request.get("partial", "")
                limit = request.get("limit", 5)
                predictions = self._engine.predict(partial, limit=limit)
                results = []
                for p in predictions:
                    results.append(
                        {
                            "text": str(p.get("name", "")),
                            "score": _to_score(p.get("_score", 0)),
                            "description": str(p.get("short_description", "")),
                            "category": str(p.get("category", "")),
                        }
                    )
                result = {
                    "success": True,
                    "query": partial,
                    "suggestions": results,
                    "prediction": results[0]["text"] if results else "",
                }

            elif req_type == "search":
                if not self._engine:
                    return {"success": False, "error": "Engine not loaded"}
                query_text = request.get("query", "")
                limit = request.get("limit", 10)
                search_results = self._engine.search(query_text, limit=limit)
                result = {
                    "success": True,
                    "query": query_text,
                    "results": [
                        {
                            "text": str(r.get("name", "")),
                            "score": _to_score(r.get("_score", 0)),
                            "description": str(r.get("short_description", "")),
                            "category": str(r.get("category", "")),
                        }
                        for r in search_results
                    ],
                }

            elif req_type == "learn":
                if not self._engine:
                    return {"success": False, "error": "Engine not loaded"}
                command = request.get("command", "")
                if command:
                    self._engine.record_usage(command)
                    result = {"success": True, "learned": command}
                else:
                    result = {"success": False, "error": "No command provided"}

            elif req_type == "history_search":
                if not self._engine:
                    return {"success": False, "error": "Engine not loaded"}
                partial = request.get("partial", "")
                limit = request.get("limit", 10)
                from shellsense.knowledge.history import search_history

                history_results = search_history(self._engine.db, partial, limit=limit)
                result = {
                    "success": True,
                    "query": partial,
                    "results": [
                        {
                            "text": str(r.get("command", "")),
                            "score": _to_score(r.get("frequency", 0)),
                        }
                        for r in history_results
                    ],
                }

            else:
                result = {"success": False, "error": f"Unknown type: {req_type}"}

            elapsed = time.time() - start
            logger.debug("Request %s processed in %.2fms", req_type, elapsed * 1000)
            return result

        except Exception as e:
            logger.error(
                "Request %s failed: %s\n%s", req_type, e, traceback.format_exc()
            )
            elapsed = time.time() - start
            logger.debug("Request %s failed in %.2fms", req_type, elapsed * 1000)
            return {"success": False, "error": str(e)}


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
