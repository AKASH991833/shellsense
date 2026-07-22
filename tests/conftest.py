from __future__ import annotations

import json
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from shellsense.utils.config import DEFAULT_CONFIG, ConfigManager


@pytest.fixture(autouse=True)
def _temp_shellsense_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        monkeypatch.setattr(
            "shellsense.utils.paths.get_shellsense_dir", lambda: tmp_path
        )
        monkeypatch.setattr(
            "shellsense.utils.paths.get_config_path",
            lambda: tmp_path / "config.json",
        )
        monkeypatch.setattr(
            "shellsense.utils.paths.get_log_path",
            lambda: tmp_path / "shellsense.log",
        )
        monkeypatch.setattr(
            "shellsense.utils.paths.get_db_path",
            lambda: tmp_path / "shellsense.db",
        )
        yield tmp_path


@pytest.fixture
def config_manager() -> ConfigManager:
    return ConfigManager()


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
    return config_path
