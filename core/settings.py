from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .utils import get_app_base, write_json_atomic

DEFAULT_SETTINGS: dict[str, Any] = {"platform": "YouTube", "download_dir": str(get_app_base() / "downloads"), "theme": "dark-blue", "appearance": "Dark"}


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_app_base() / "settings.json"

    def load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Configuração não é um objeto JSON")
        except FileNotFoundError:
            data = {}
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logging.getLogger(__name__).warning("Não foi possível ler settings.json: %s", exc)
            data = {}
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged

    def save(self, values: dict[str, Any]) -> bool:
        current = self.load()
        current.update(values)
        return write_json_atomic(self.path, current)
