from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CommandHistory:
    id: int = 0
    command: str = ""
    exit_code: int = 0
    working_directory: str = ""
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0


@dataclass
class CommandSuggestion:
    id: int = 0
    input_text: str = ""
    suggestion: str = ""
    confidence: float = 0.0
    source: str = ""
    invoked_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CorrectionLog:
    id: int = 0
    original: str = ""
    corrected: str = ""
    distance: float = 0.0
    applied: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ErrorAnalysis:
    id: int = 0
    command: str = ""
    error_message: str = ""
    exit_code: int = 0
    analysis: str = ""
    suggestion: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LearningEntry:
    id: int = 0
    command: str = ""
    frequency: int = 1
    last_used: datetime = field(default_factory=datetime.utcnow)
    category: str = ""
    tags: str = ""
