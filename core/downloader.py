from __future__ import annotations

import logging
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock
from typing import Any, Callable, Optional
from urllib.parse import urlparse

import requests
import yt_dlp
from PIL import Image
from io import BytesIO

from .utils import clean_ansi, find_ffmpeg, format_bytes, get_app_base

ProgressCallback = Callable[[dict[str, Any]], None]


class DownloadCancelled(Exception):
    """Usada pelo hook do yt-dlp para interromper um download em curso."""


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    output_dir: Path
    quality: str = "Melhor"
    filename: str = ""
    use_chrome_cookies: bool = False


def validate_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def platform_from_url(url: str) -> Optional[str]:
    hostname = urlparse(url).netloc.lower().removeprefix("www.")
    mapping = {
        "youtube.com": "YouTube", "youtu.be": "YouTube", "facebook.com": "Facebook",
        "fb.watch": "Facebook", "instagram.com": "Instagram", "twitter.com": "Twitter",
        "x.com": "Twitter", "twitch.tv": "Twitch", "tiktok.com": "TikTok",
    }
    return next((platform for domain, platform in mapping.items() if hostname == domain or hostname.endswith("." + domain)), None)


def _safe_stem(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", value).strip(" .")
    return cleaned[:150]


class DownloaderEngine:
    """Operações bloqueantes do yt-dlp/FFmpeg, sem qualquer dependência da UI."""

    def __init__(self, ffmpeg_path: Optional[Path] = None) -> None:
        self.ffmpeg_path = ffmpeg_path if ffmpeg_path is not None else find_ffmpeg()
        self.cancel_event = Event()
        self._process_lock = Lock()
        self._active_process: subprocess.Popen[str] | None = None
        self.log = logging.getLogger(__name__)

    def cancel(self) -> None:
        self.cancel_event.set()

        # FFmpeg não usa hooks do yt-dlp. Interromper o processo torna o
        # fechamento e o botão Parar efetivos também durante um GIF.
        with self._process_lock:
            process = self._active_process
        if process and process.poll() is None:
            process.terminate()

    def clear_cancellation(self) -> None:
        self.cancel_event.clear()

    def metadata(self, url: str) -> dict[str, Any]:
        if not validate_url(url):
            raise ValueError("Cole um link HTTP ou HTTPS válido.")
        options = {"quiet": True, "skip_download": True, "noplaylist": True, "no_warnings": True}
        if self.cancel_event.is_set():
            raise DownloadCancelled("Operação cancelada.")
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        thumbnails = info.get("thumbnails") or []
        thumbnail = info.get("thumbnail") or (thumbnails[-1].get("url") if thumbnails else "")
        return {
            "title": str(info.get("title") or "Vídeo detectado"),
            "duration": info.get("duration"),
            "uploader": str(info.get("uploader") or info.get("channel") or "Não informado"),
            "view_count": info.get("view_count"),
            "thumbnail": thumbnail if isinstance(thumbnail, str) else "",
        }

    @staticmethod
    def load_thumbnail(url: str) -> Optional[Image.Image]:
        if not url:
            return None
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.load()
        return image.convert("RGB")

    def _progress_hook(self, callback: ProgressCallback) -> Callable[[dict[str, Any]], None]:
        def hook(data: dict[str, Any]) -> None:
            if self.cancel_event.is_set():
                raise DownloadCancelled("Download cancelado pelo usuário.")
            status = data.get("status")
            if status == "downloading":
                percent_text = clean_ansi(data.get("_percent_str"), "0%").replace("%", "").strip()
                try:
                    percent = max(0.0, min(1.0, float(percent_text) / 100))
                except ValueError:
                    percent = 0.0
                speed = clean_ansi(data.get("_speed_str"), "Calculando…")
                eta = clean_ansi(data.get("_eta_str"), "—")
                downloaded = data.get("downloaded_bytes")
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                size_text = f"{format_bytes(downloaded)} / {format_bytes(total)}" if total else format_bytes(downloaded)
                callback({
                    "type": "progress", "progress": percent,
                    "percent_text": f"{percent * 100:.1f}%", "speed": speed, "eta": eta,
                    "text": f"{percent * 100:.1f}% | {speed} | ETA {eta} | {size_text}",
                })
            elif status == "finished":
                callback({"type": "progress", "progress": 1.0, "text": "100.0% | Processando arquivo… | ETA —"})
        return hook

    def download(self, request: DownloadRequest, callback: ProgressCallback) -> dict[str, Any]:
        if not validate_url(request.url):
            raise ValueError("Cole um link HTTP ou HTTPS válido.")
        if request.quality not in {"Melhor", "1080p", "720p", "MP3"}:
            raise ValueError("Qualidade de download inválida.")
        if not self.ffmpeg_path:
            raise FileNotFoundError("FFmpeg não foi encontrado. Coloque-o em ffmpeg/bin, ao lado do programa, ou instale-o no PATH.")

        if self.cancel_event.is_set():
            raise DownloadCancelled("Download cancelado antes de iniciar.")
        if request.output_dir.exists() and not request.output_dir.is_dir():
            raise NotADirectoryError(f"A pasta de saída não é uma pasta: {request.output_dir}")
        request.output_dir.mkdir(parents=True, exist_ok=True)
        formats = {
            "Melhor": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "MP3": "bestaudio/best",
        }
        stem = _safe_stem(request.filename)
        template = str(request.output_dir / (f"{stem}.%(ext)s" if stem else "%(title)s.%(ext)s"))
        options: dict[str, Any] = {
            "format": formats[request.quality], "outtmpl": template, "noplaylist": True,
            "quiet": True, "no_warnings": True, "ffmpeg_location": str(self.ffmpeg_path.parent),
            "progress_hooks": [self._progress_hook(callback)],
            "merge_output_format": "mp4" if request.quality != "MP3" else None,
        }
        if request.quality == "MP3":
            options["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
        if request.use_chrome_cookies:
            options["cookiesfrombrowser"] = ("chrome",)

        self.log.info("Iniciando download: %s (%s)", request.url, request.quality)
        before_download = {path.resolve() for path in request.output_dir.iterdir() if path.is_file()}
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(request.url, download=True)
                expected_filename = Path(ydl.prepare_filename(info))
            created = [path for path in request.output_dir.iterdir() if path.is_file() and path.resolve() not in before_download and not path.name.endswith((".part", ".ytdl"))]
            filename = max(created, key=lambda path: path.stat().st_mtime) if created else expected_filename
            return {"title": str(info.get("title") or filename.stem), "path": filename}
        except DownloadCancelled:
            self.log.info("Download cancelado: %s", request.url)
            raise
        except Exception:
            self.log.exception("Falha no download: %s", request.url)
            raise

    def convert_gif(self, source: Path, output: Path, fps: int, width: int, start: int, duration: int, callback: ProgressCallback) -> Path:
        if not self.ffmpeg_path:
            raise FileNotFoundError("FFmpeg não foi encontrado para converter o GIF.")
        if not source.is_file():
            raise FileNotFoundError("O vídeo selecionado para o GIF não existe mais.")
        if self.cancel_event.is_set():
            raise DownloadCancelled("Conversão cancelada antes de iniciar.")
        output.parent.mkdir(parents=True, exist_ok=True)
        command = [str(self.ffmpeg_path), "-hide_banner", "-ss", str(start), "-t", str(duration), "-i", str(source), "-vf", f"fps={fps},scale={width}:-1:flags=lanczos", "-y", str(output)]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", creationflags=flags)
        with self._process_lock:
            self._active_process = process
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")
        try:
            assert process.stderr is not None
            for line in process.stderr:
                match = time_pattern.search(line)
                if match:
                    elapsed = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
                    callback({"type": "gif_progress", "progress": min(1.0, elapsed / max(duration, 1)), "text": f"Gerando GIF: {min(100, elapsed / max(duration, 1) * 100):.0f}%"})
            if self.cancel_event.is_set():
                raise DownloadCancelled("Conversão de GIF cancelada.")
            if process.wait() != 0:
                raise RuntimeError("O FFmpeg não conseguiu converter este arquivo. Consulte app.log para detalhes.")
            return output
        finally:
            with self._process_lock:
                self._active_process = None

    @staticmethod
    def update_yt_dlp(callback: ProgressCallback) -> str:
        """Atualiza o pacote no modo script; no .exe baixa o standalone para diagnóstico."""
        if getattr(sys, "frozen", False):
            target = get_app_base() / "yt-dlp.exe"
            temporary = target.with_suffix(".new.exe")
            callback({"type": "status", "text": "Baixando yt-dlp standalone…"})
            try:
                with requests.get("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe", stream=True, timeout=30) as response:
                    response.raise_for_status()
                    total = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    with temporary.open("wb") as file:
                        for chunk in response.iter_content(64 * 1024):
                            if chunk:
                                file.write(chunk)
                                downloaded += len(chunk)
                                callback({"type": "progress", "progress": downloaded / total if total else 0, "text": f"Atualizando yt-dlp standalone… {format_bytes(downloaded)}"})
                temporary.replace(target)
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
            return "Standalone do yt-dlp atualizado. A versão embutida no .exe só muda numa nova compilação."
        callback({"type": "status", "text": "Atualizando yt-dlp pelo pip…"})
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], capture_output=True, text=True, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "pip não conseguiu atualizar o yt-dlp.")
        return "yt-dlp atualizado com sucesso. Reinicie o aplicativo para usar a nova versão."
