from __future__ import annotations

import json
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Optional

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def get_app_base() -> Path:
    """Retorna a pasta do script ou do executável empacotado."""
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]


def find_ffmpeg(base_path: Optional[Path] = None) -> Optional[Path]:
    """Procura o FFmpeg local, inclusive nas duas estruturas de distribuição."""
    base = base_path or get_app_base()
    executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    candidates = [base / "ffmpeg" / "bin" / executable, base / executable, base / "ffmpeg"]
    # No modo --onefile, recursos ficam em _MEIPASS; os downloads continuam
    # ao lado do executável (``base``), mas o FFmpeg pode estar empacotado.
    bundle_path = getattr(sys, "_MEIPASS", None)
    if bundle_path:
        candidates.append(Path(bundle_path) / "ffmpeg" / "bin" / executable)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    system_ffmpeg = shutil.which("ffmpeg")
    return Path(system_ffmpeg) if system_ffmpeg else None


def get_ffmpeg_path() -> Optional[str]:
    """Compatibilidade com as engines antigas."""
    ffmpeg = find_ffmpeg()
    return str(ffmpeg) if ffmpeg else None


def clean_ansi(value: Any, fallback: str = "—") -> str:
    """Remove formatação ANSI e normaliza valores vazios do yt-dlp."""
    if value is None:
        return fallback
    result = ANSI_RE.sub("", str(value)).strip()
    return result or fallback


def format_bytes(value: Any) -> str:
    try:
        size = float(value)
    except (TypeError, ValueError):
        return "—"
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return "—"


def write_json_atomic(path: Path, value: Any) -> bool:
    """Grava JSON sem deixar um arquivo parcialmente escrito em caso de queda."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
        return True
    except OSError as exc:
        logging.getLogger(__name__).warning("Não foi possível gravar %s: %s", path, exc)
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return False


class DownloadLogger:
    """Adaptador de progresso mantido para os módulos de engine legados."""

    def __init__(self, callback_func: Optional[Callable[[dict], None]]):
        self.callback_func = callback_func

    def hook(self, data: dict) -> None:
        if not self.callback_func:
            return
        status = data.get("status")
        if status == "downloading":
            self.callback_func({
                "status": status,
                "_percent_str": clean_ansi(data.get("_percent_str"), "0%"),
                "_speed_str": clean_ansi(data.get("_speed_str"), "Calculando…"),
                "_eta_str": clean_ansi(data.get("_eta_str"), "—"),
            })
        elif status == "finished":
            self.callback_func({"status": status, "_percent_str": "100%", "_speed_str": "Processando…", "_eta_str": "—"})
