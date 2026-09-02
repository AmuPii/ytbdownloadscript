"""Ponte de compatibilidade para os módulos ``engine_*`` antigos.

As engines públicas agora usam exatamente a mesma implementação robusta da
interface. Isso evita que chamadas externas ainda recebam a lógica antiga,
insegura e divergente.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .downloader import DownloadRequest, DownloaderEngine

LegacyHook = Callable[[dict[str, Any]], None] | None


def download_legacy(url: str, output_dir: str | Path, hook: LegacyHook, quality: str) -> dict[str, Any]:
    def emit(event: dict[str, Any]) -> None:
        if not hook:
            return
        if event.get("type") == "progress":
            hook({
                "status": "downloading",
                "_percent_str": event.get("percent_text", "0%"),
                "_speed_str": event.get("speed", "Calculando…"),
                "_eta_str": event.get("eta", "—"),
            })

    engine = DownloaderEngine()
    result = engine.download(DownloadRequest(url=url, output_dir=Path(output_dir), quality=quality), emit)
    if hook:
        hook({"status": "finished", "_percent_str": "100%", "_speed_str": "Concluído", "_eta_str": "—"})
    return result
