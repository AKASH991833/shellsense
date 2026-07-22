from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import ensure_shellsense_dir, get_db_path

logger = get_logger(__name__)

_TABLES: dict[str, str] = {
    "command_history": """
        CREATE TABLE IF NOT EXISTS command_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            command         TEXT NOT NULL,
            exit_code       INTEGER DEFAULT 0,
            working_directory TEXT DEFAULT '',
            session_id      TEXT DEFAULT '',
            timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_time_ms REAL DEFAULT 0.0
        )
    """,
    "command_suggestions": """
        CREATE TABLE IF NOT EXISTS command_suggestions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text      TEXT NOT NULL,
            suggestion      TEXT NOT NULL,
            confidence      REAL DEFAULT 0.0,
            source          TEXT DEFAULT '',
            invoked_count   INTEGER DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "correction_log": """
        CREATE TABLE IF NOT EXISTS correction_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            original        TEXT NOT NULL,
            corrected       TEXT NOT NULL,
            distance        REAL DEFAULT 0.0,
            applied         INTEGER DEFAULT 0,
            timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "error_analysis": """
        CREATE TABLE IF NOT EXISTS error_analysis (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            command         TEXT NOT NULL,
            error_message   TEXT NOT NULL,
            exit_code       INTEGER DEFAULT 0,
            analysis        TEXT DEFAULT '',
            suggestion      TEXT DEFAULT '',
            timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "learning_entries": """
        CREATE TABLE IF NOT EXISTS learning_entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            command         TEXT NOT NULL,
            frequency       INTEGER DEFAULT 1,
            last_used       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            category        TEXT DEFAULT '',
            tags            TEXT DEFAULT ''
        )
    """,
    "schema_version": """
        CREATE TABLE IF NOT EXISTS schema_version (
            version     INTEGER PRIMARY KEY,
            applied_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}

_KNOWLEDGE_TABLES: dict[str, str] = {
    "commands": """
        CREATE TABLE IF NOT EXISTS commands (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL UNIQUE,
            short_description   TEXT NOT NULL DEFAULT '',
            long_description    TEXT NOT NULL DEFAULT '',
            syntax              TEXT NOT NULL DEFAULT '',
            category            TEXT NOT NULL DEFAULT '',
            difficulty          TEXT NOT NULL DEFAULT 'beginner',
            risk_level          TEXT NOT NULL DEFAULT 'SAFE',
            availability        TEXT NOT NULL DEFAULT 'linux',
            official_docs       TEXT NOT NULL DEFAULT '',
            keywords            TEXT NOT NULL DEFAULT '',
            notes               TEXT NOT NULL DEFAULT '',
            warnings            TEXT NOT NULL DEFAULT ''
        )
    """,
    "aliases": """
        CREATE TABLE IF NOT EXISTS aliases (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id  INTEGER NOT NULL,
            alias       TEXT NOT NULL,
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
        )
    """,
    "examples": """
        CREATE TABLE IF NOT EXISTS examples (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id  INTEGER NOT NULL,
            title       TEXT NOT NULL DEFAULT '',
            command     TEXT NOT NULL,
            output      TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
        )
    """,
    "options": """
        CREATE TABLE IF NOT EXISTS options (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id  INTEGER NOT NULL,
            flag        TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
        )
    """,
    "subcommands": """
        CREATE TABLE IF NOT EXISTS subcommands (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id  INTEGER NOT NULL,
            subcommand  TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
        )
    """,
    "common_errors": """
        CREATE TABLE IF NOT EXISTS common_errors (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id      INTEGER NOT NULL,
            error_pattern   TEXT NOT NULL,
            explanation     TEXT NOT NULL DEFAULT '',
            solution        TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
        )
    """,
    "related_commands": """
        CREATE TABLE IF NOT EXISTS related_commands (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id          INTEGER NOT NULL,
            related_command_name TEXT NOT NULL,
            relationship        TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
        )
    """,
    "tags": """
        CREATE TABLE IF NOT EXISTS tags (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id  INTEGER NOT NULL,
            tag         TEXT NOT NULL,
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
        )
    """,
    "distro_compatibility": """
        CREATE TABLE IF NOT EXISTS distro_compatibility (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id  INTEGER NOT NULL,
            distro      TEXT NOT NULL,
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE
        )
    """,
    "topics": """
        CREATE TABLE IF NOT EXISTS topics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT ''
        )
    """,
    "command_topics": """
        CREATE TABLE IF NOT EXISTS command_topics (
            command_id  INTEGER NOT NULL,
            topic_id    INTEGER NOT NULL,
            PRIMARY KEY (command_id, topic_id),
            FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
    """,
}

_SUGGESTION_TABLES: dict[str, str] = {
    "suggestion_history": """
        CREATE TABLE IF NOT EXISTS suggestion_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            query       TEXT NOT NULL,
            suggestion  TEXT NOT NULL,
            rank        INTEGER DEFAULT 0,
            confidence  REAL DEFAULT 0.0,
            source      TEXT DEFAULT '',
            timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "search_history": """
        CREATE TABLE IF NOT EXISTS search_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            query        TEXT NOT NULL,
            result_count INTEGER DEFAULT 0,
            timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "explanation_history": """
        CREATE TABLE IF NOT EXISTS explanation_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            command   TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "usage_stats": """
        CREATE TABLE IF NOT EXISTS usage_stats (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            command_name  TEXT NOT NULL UNIQUE,
            search_count  INTEGER DEFAULT 0,
            suggest_count INTEGER DEFAULT 0,
            explain_count INTEGER DEFAULT 0,
            example_count INTEGER DEFAULT 0,
            category      TEXT DEFAULT '',
            last_used     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "learning_data": """
        CREATE TABLE IF NOT EXISTS learning_data (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            command_name   TEXT NOT NULL,
            frequency      INTEGER DEFAULT 1,
            last_accessed  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_type      TEXT NOT NULL DEFAULT 'search',
            metadata       TEXT DEFAULT ''
        )
    """,
    "cache_meta": """
        CREATE TABLE IF NOT EXISTS cache_meta (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key   TEXT NOT NULL UNIQUE,
            result_count INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at  TIMESTAMP
        )
    """,
    "discovered_commands": """
        CREATE TABLE IF NOT EXISTS discovered_commands (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL UNIQUE,
            short_description   TEXT NOT NULL DEFAULT '',
            long_description    TEXT NOT NULL DEFAULT '',
            syntax              TEXT NOT NULL DEFAULT '',
            category            TEXT NOT NULL DEFAULT '',
            difficulty          TEXT NOT NULL DEFAULT 'intermediate',
            risk_level          TEXT NOT NULL DEFAULT 'SAFE',
            availability        TEXT NOT NULL DEFAULT 'linux',
            keywords            TEXT NOT NULL DEFAULT '',
            tags                TEXT NOT NULL DEFAULT '',
            options_json        TEXT NOT NULL DEFAULT '[]',
            binary_path         TEXT NOT NULL DEFAULT '',
            source              TEXT NOT NULL DEFAULT 'man',
            discovered_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}

_CURRENT_SCHEMA_VERSION = 4


class DatabaseManager:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self._path = Path(db_path) if db_path else get_db_path()
        self._lock = Lock()
        self._connection: sqlite3.Connection | None = None

    @property
    def path(self) -> Path:
        return self._path

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            ensure_shellsense_dir()
            self._connection = sqlite3.connect(
                str(self._path),
                timeout=5.0,
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
            logger.info("Connected to database at %s", self._path)
        return self._connection

    def initialize(self) -> None:
        with self._lock:
            conn = self.connect()
            for table_name, ddl in _TABLES.items():
                conn.execute(ddl)
                logger.debug("Ensured table '%s' exists", table_name)
            for table_name, ddl in _KNOWLEDGE_TABLES.items():
                conn.execute(ddl)
                logger.debug("Ensured table '%s' exists", table_name)
            for table_name, ddl in _SUGGESTION_TABLES.items():
                conn.execute(ddl)
                logger.debug("Ensured table '%s' exists", table_name)
            self._ensure_schema_version(conn)
            conn.commit()
            logger.info("Database initialized at %s", self._path)

    def _ensure_schema_version(self, conn: sqlite3.Connection) -> None:
        cursor = conn.execute("SELECT MAX(version) FROM schema_version")
        row = cursor.fetchone()
        current_version = row[0] if row and row[0] else 0
        if current_version < _CURRENT_SCHEMA_VERSION:
            conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (_CURRENT_SCHEMA_VERSION,),
            )
            logger.info(
                "Schema version updated from %d to %d",
                current_version,
                _CURRENT_SCHEMA_VERSION,
            )

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
                logger.info("Database connection closed")

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor:
        with self._lock:
            conn = self.connect()
            return conn.execute(sql, params)

    def executemany(
        self, sql: str, params_list: list[tuple[object, ...]]
    ) -> sqlite3.Cursor:
        with self._lock:
            conn = self.connect()
            return conn.executemany(sql, params_list)

    def commit(self) -> None:
        with self._lock:
            if self._connection:
                self._connection.commit()

    def is_seeded(self) -> bool:
        with self._lock:
            try:
                conn = self.connect()
                cursor = conn.execute("SELECT COUNT(*) FROM commands")
                count: int = cursor.fetchone()[0]
                return count > 0
            except Exception:
                return False

    def __enter__(self) -> DatabaseManager:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
