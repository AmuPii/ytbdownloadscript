from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .utils import get_app_base, write_json_atomic


class HistoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_app_base() / "history.json"

    def list(self) -> list[dict[str, Any]]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, list) else []
        except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
            if not isinstance(exc, FileNotFoundError):
                logging.getLogger(__name__).warning("Não foi possível ler o histórico: %s", exc)
            return []

    def add(self, title: str, url: str, file_path: Path | None) -> None:
        items = self.list()
        items.insert(0, {"title": title, "url": url, "date": datetime.now().astimezone().isoformat(timespec="seconds"), "path": str(file_path) if file_path else ""})
        write_json_atomic(self.path, items[:200])
