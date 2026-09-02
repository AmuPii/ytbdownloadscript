"""Interface CustomTkinter do Downloader do Herickão.

As operações demoradas são executadas em ``ThreadPoolExecutor``. Workers nunca
tocam widgets: enviam eventos a uma fila, consumida pela thread do Tk.
"""
from __future__ import annotations

import logging
import os
import queue
import re
import subprocess
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

import customtkinter as ctk
from PIL import Image
from tkinter import filedialog, messagebox

from core.downloader import (
    DownloadCancelled,
    DownloadRequest,
    DownloaderEngine,
    platform_from_url,
    validate_url,
)
from core.history import HistoryStore
from core.logging_setup import configure_logging
from core.settings import SettingsStore
from core.utils import find_ffmpeg

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "inactive": "#474444", "youtube": "#FF0000", "facebook": "#0D09FD",
    "instagram": "#B82455", "twitter": "#222222", "twitch": "#9146FF",
    "tiktok": "#111111", "hover_tiktok": "#25F4EE", "download": "#00C853",
    "folder": "#2980B9", "update": "#E67E22", "gif": "#6A5ACD", "stop": "#D32F2F",
    "card": "#1F1F1F",
}
PLATFORMS = (("YouTube", "youtube"), ("Facebook", "facebook"), ("Instagram", "instagram"), ("Twitter", "twitter"), ("Twitch", "twitch"), ("TikTok", "tiktok"))
GIF_QUALITY = {"Alta": (25, 720), "Média": (15, 480), "Baixa": (10, 320)}


def short_text(text: str, length: int = 90) -> str:
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"


def format_duration(seconds: Any) -> str:
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        return "Não informada"
    hours, remaining = divmod(total, 3600)
    minutes, seconds = divmod(remaining, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:d}:{seconds:02d}"


class DownloaderApp(ctk.CTk):
    def __init__(self) -> None:
        configure_logging()
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.title("Downloader Pro v4.0")
        self.geometry("680x735")
        self.minsize(580, 620)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._close_app)

        self._closing = False
        self._events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="downloader")
        self._download_future: Future[Any] | None = None
        self._preview_future: Future[Any] | None = None
        self._gif_future: Future[Any] | None = None
        self._update_future: Future[Any] | None = None
        self._queue: list[DownloadRequest] = []
        self._platform_forced = False
        self._preview_url = ""
        self._preview_after: str | None = None
        self.settings = SettingsStore()
        self.config = self.settings.load()
        self.appearance = str(self.config.get("appearance", "Dark"))
        if self.appearance not in {"Dark", "Light", "System"}:
            self.appearance = "Dark"
        ctk.set_appearance_mode(self.appearance)
        self._startup_warning = ""
        self.download_dir = self._usable_download_dir(Path(str(self.config["download_dir"])).expanduser())
        self.history = HistoryStore()
        self.engine = DownloaderEngine(find_ffmpeg())
        self.video_gif_path: Path | None = None
        self.gif_output_dir = self.download_dir
        self.gif_quality = "Média"

        self.platform_buttons: dict[str, ctk.CTkButton] = {}
        self._setup_header()
        self._setup_platforms()
        self._setup_inputs()
        self._setup_preview()
        self._setup_downloads()
        self._setup_gif()
        self._select_platform(str(self.config.get("platform", "YouTube")), manual=False)
        self._set_ffmpeg_notice()
        if self._startup_warning:
            self._set_status(self._startup_warning, error=True)
        self.after(80, self._drain_events)

    # ---------- UI setup ----------
    def _setup_header(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=(14, 4), padx=20, fill="x")
        ctk.CTkLabel(frame, text="Downloader Pro", font=("Roboto Black", 24)).pack(side="left")
        self.theme_button = ctk.CTkButton(frame, text=f"Tema: {self.appearance}", width=88, command=self._cycle_appearance)
        self.theme_button.pack(side="right", padx=(6, 0))
        ctk.CTkButton(frame, text="Histórico", width=88, command=self._open_history).pack(side="right", padx=(6, 0))
        self.update_button = ctk.CTkButton(frame, text="🛠 Atualizar", width=100, fg_color=COLORS["update"], command=self._update_yt_dlp)
        self.update_button.pack(side="right")

    def _setup_platforms(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=7, padx=16, fill="x")
        for col in range(3):
            frame.grid_columnconfigure(col, weight=1)
        for index, (name, color_key) in enumerate(PLATFORMS):
            button = ctk.CTkButton(frame, text=name.upper(), height=38, font=("Arial", 12, "bold"), command=lambda n=name: self._select_platform(n, manual=True))
            button.grid(row=index // 3, column=index % 3, sticky="ew", padx=3, pady=3)
            self.platform_buttons[name] = button

    def _setup_inputs(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(pady=(4, 0), padx=20, fill="x")
        row = ctk.CTkFrame(wrapper, fg_color="transparent")
        row.pack(fill="x")
        self.entry_url = ctk.CTkEntry(row, height=42, placeholder_text="Cole o link aqui…", font=("Arial", 14))
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_url.bind("<Return>", lambda _event: self._request_preview())
        self.entry_url.bind("<KeyRelease>", self._on_url_changed)
        self.entry_url.bind("<Control-v>", lambda _event: self.after(80, self._on_paste))
        ctk.CTkButton(row, text="📋", width=45, height=42, fg_color="#444444", command=self._paste_url).pack(side="right")

        options = ctk.CTkFrame(wrapper, fg_color="transparent")
        options.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(options, text="Qualidade:").pack(side="left", padx=(0, 5))
        self.quality_combo = ctk.CTkComboBox(options, values=["Melhor", "1080p", "720p", "MP3"], width=110)
        self.quality_combo.pack(side="left")
        self.cookies_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options, text="Usar cookies do Chrome", variable=self.cookies_var).pack(side="left", padx=13)
        ctk.CTkButton(options, text="AUTO", width=58, height=26, command=self._enable_auto_platform).pack(side="right")

        self.filename_entry = ctk.CTkEntry(wrapper, height=34, placeholder_text="Renomear arquivo (opcional)")
        self.filename_entry.pack(fill="x", pady=(6, 0))

    def _setup_preview(self) -> None:
        self.preview = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=10, height=128)
        self.preview.pack(pady=9, padx=20, fill="x")
        self.preview.pack_propagate(False)
        self.thumb = ctk.CTkLabel(self.preview, text="Preview", width=160, height=90, fg_color="#333333")
        self.thumb.pack(side="left", padx=12, pady=14)
        info = ctk.CTkFrame(self.preview, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)
        self.title_label = ctk.CTkLabel(info, text="Cole um link para ver os detalhes.", font=("Arial", 14, "bold"), anchor="w", justify="left", wraplength=420)
        self.title_label.pack(fill="x")
        self.details_label = ctk.CTkLabel(info, text="", text_color="#B5B5B5", anchor="w", justify="left", wraplength=420)
        self.details_label.pack(fill="x", pady=(5, 0))

    def _setup_downloads(self) -> None:
        self.status_label = ctk.CTkLabel(self, text="Pronto", text_color="#B5B5B5", wraplength=620)
        self.status_label.pack(pady=(2, 0), padx=20)
        self.progress = ctk.CTkProgressBar(self, height=12, progress_color=COLORS["download"])
        self.progress.set(0)
        self.progress.pack(pady=5, padx=20, fill="x")
        self.queue_label = ctk.CTkLabel(self, text="Fila: 0 item(ns)", text_color="#B5B5B5")
        self.queue_label.pack()

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(pady=8, padx=20, fill="x")
        for col in range(4):
            actions.grid_columnconfigure(col, weight=1)
        self.download_button = ctk.CTkButton(actions, text="BAIXAR AGORA", height=48, font=("Arial", 14, "bold"), fg_color=COLORS["download"], command=self._add_download)
        self.download_button.grid(row=0, column=0, padx=3, sticky="ew")
        self.stop_button = ctk.CTkButton(actions, text="PARAR", height=48, fg_color=COLORS["stop"], command=self._cancel_download, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=3, sticky="ew")
        ctk.CTkButton(actions, text="PASTA", height=48, fg_color=COLORS["folder"], command=lambda: self._open_folder(self.download_dir)).grid(row=0, column=2, padx=3, sticky="ew")
        ctk.CTkButton(actions, text="ESCOLHER", height=48, fg_color="#456A88", command=self._choose_download_dir).grid(row=0, column=3, padx=3, sticky="ew")

    def _setup_gif(self) -> None:
        ctk.CTkFrame(self, height=2, fg_color="#333333").pack(fill="x", pady=10, padx=20)
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(padx=20, fill="x", pady=(0, 8))
        heading = ctk.CTkFrame(frame, fg_color="transparent")
        heading.pack(fill="x")
        ctk.CTkLabel(heading, text="🎞 Criador de GIF", font=("Arial", 15, "bold")).pack(side="left")
        ctk.CTkButton(heading, text="Opções", width=74, height=25, command=self._gif_options).pack(side="right")
        choose = ctk.CTkFrame(frame, fg_color="#2B2B2B", height=39)
        choose.pack(fill="x", pady=5)
        choose.pack_propagate(False)
        self.gif_file_label = ctk.CTkLabel(choose, text="Selecione um vídeo…", text_color="#B5B5B5")
        self.gif_file_label.pack(side="left", padx=12)
        ctk.CTkButton(choose, text="📂", width=42, command=self._select_gif_source).pack(side="right", padx=4, pady=4)
        self.gif_name_label = ctk.CTkLabel(frame, text="Saída: selecione um vídeo", text_color="#B5B5B5", anchor="w")
        self.gif_name_label.pack(fill="x")
        self.gif_button = ctk.CTkButton(frame, text="CONVERTER PARA GIF", height=40, font=("Arial", 13, "bold"), fg_color=COLORS["gif"], command=self._convert_gif)
        self.gif_button.pack(fill="x", pady=(5, 0))

    # ---------- platform, preview and folder ----------
    def _select_platform(self, name: str, manual: bool = True) -> None:
        if name not in self.platform_buttons:
            name = "YouTube"
        previous_platform = getattr(self, "current_platform", "")
        self._platform_forced = manual
        for platform, color_key in PLATFORMS:
            self.platform_buttons[platform].configure(fg_color=COLORS[color_key] if platform == name else COLORS["inactive"])
        self.entry_url.configure(placeholder_text=f"Link do {name}…")
        self.current_platform = name
        if name != previous_platform and not self.settings.save({"platform": name, "download_dir": str(self.download_dir)}):
            self.log.warning("Não foi possível salvar a plataforma selecionada")

    def _enable_auto_platform(self) -> None:
        self._platform_forced = False
        self._detect_platform()
        self._set_status("Detecção automática de plataforma ativada.")

    def _detect_platform(self) -> None:
        if not self._platform_forced:
            detected = platform_from_url(self.entry_url.get().strip())
            if detected:
                self._select_platform(detected, manual=False)

    def _on_url_changed(self, _event: Any = None) -> None:
        self._detect_platform()
        if self._preview_after:
            self.after_cancel(self._preview_after)
        self._preview_after = self.after(700, self._request_preview)

    def _on_paste(self) -> None:
        self._detect_platform()
        self._request_preview()

    def _paste_url(self) -> None:
        try:
            self.entry_url.delete(0, "end")
            self.entry_url.insert(0, self.clipboard_get())
            self._on_paste()
        except Exception:
            self._set_status("Não foi possível ler a área de transferência.", error=True)

    def _request_preview(self) -> None:
        url = self.entry_url.get().strip()
        if not url or url == self._preview_url:
            return
        if not validate_url(url):
            self._set_status("Link inválido: cole uma URL que comece com http:// ou https://", error=True)
            return
        self._preview_url = url
        self.title_label.configure(text="⏳ Buscando informações…")
        self.details_label.configure(text="Isso pode levar alguns segundos.")
        self._preview_future = self._executor.submit(self._metadata_worker, url)

    def _metadata_worker(self, url: str) -> None:
        try:
            info = self.engine.metadata(url)
            image = self.engine.load_thumbnail(info["thumbnail"])
            self._events.put({"type": "preview", "url": url, "info": info, "image": image})
        except Exception as exc:
            self.log.exception("Falha ao obter metadados")
            self._events.put({"type": "preview_error", "url": url, "message": "Não foi possível ler este link. Verifique se ele é público e tente novamente."})

    def _choose_download_dir(self) -> None:
        chosen = filedialog.askdirectory(initialdir=str(self.download_dir), title="Escolha a pasta de downloads")
        if chosen:
            try:
                self.download_dir = self._usable_download_dir(Path(chosen))
            except OSError:
                self._set_status("Não foi possível usar esta pasta. Escolha outra com permissão de escrita.", error=True)
                return
            self.gif_output_dir = self.download_dir
            saved = self.settings.save({"download_dir": str(self.download_dir)})
            message = f"Pasta de downloads: {self.download_dir}"
            self._set_status(message if saved else f"{message} (não foi possível salvar a preferência)", success=saved, error=not saved)

    def _usable_download_dir(self, requested: Path) -> Path:
        """Cria a pasta escolhida; em instalação protegida usa Downloads do usuário."""
        try:
            requested.mkdir(parents=True, exist_ok=True)
            if requested.is_dir():
                return requested
        except OSError as exc:
            self.log.warning("Pasta de download indisponível (%s): %s", requested, exc)
        fallback = Path.home() / "Downloads" / "DownloaderHerickao"
        fallback.mkdir(parents=True, exist_ok=True)
        self._startup_warning = f"A pasta configurada não pôde ser usada. Usando: {fallback}"
        return fallback

    # ---------- downloads and queue ----------
    def _add_download(self) -> None:
        if self._gif_future and not self._gif_future.done():
            self._set_status("Aguarde a conversão de GIF terminar antes de iniciar downloads.", error=True)
            return
        if self._update_future and not self._update_future.done():
            self._set_status("Aguarde a atualização do yt-dlp terminar.", error=True)
            return
        # CTkEntry é uma linha só: aceitar links separados por espaço, vírgula
        # ou quebra de linha torna possível colar vários itens de uma vez.
        urls = [value.strip() for value in re.split(r"[\s,]+", self.entry_url.get()) if value.strip()]
        if not urls:
            self._set_status("Cole ao menos um link antes de baixar.", error=True)
            return
        invalid = [url for url in urls if not validate_url(url)]
        if invalid:
            self._set_status("Há um link inválido na fila.", error=True)
            return
        filename = self.filename_entry.get().strip()
        if len(urls) > 1:
            filename = ""  # um nome único seria ambíguo para vários links
        for url in urls:
            self._queue.append(DownloadRequest(url, self.download_dir, self.quality_combo.get(), filename, self.cookies_var.get()))
        self._update_queue_label()
        self.entry_url.delete(0, "end")
        self.filename_entry.delete(0, "end")
        self._start_next_download()

    def _start_next_download(self) -> None:
        if self._download_future and not self._download_future.done():
            return
        if not self._queue:
            self.download_button.configure(state="normal", text="BAIXAR AGORA", fg_color=COLORS["download"])
            self.stop_button.configure(state="disabled")
            if not (self._gif_future and not self._gif_future.done()):
                self.gif_button.configure(state="normal")
            if not (self._update_future and not self._update_future.done()):
                self.update_button.configure(state="normal", text="🛠 Atualizar")
            self.engine.clear_cancellation()
            return
        request = self._queue.pop(0)
        self._update_queue_label()
        self.progress.set(0)
        # A fila continua recebendo links enquanto um item é processado.
        self.download_button.configure(state="normal", text="ADICIONAR À FILA", fg_color=COLORS["download"])
        self.stop_button.configure(state="normal")
        self.gif_button.configure(state="disabled")
        self.update_button.configure(state="disabled")
        self._set_status("Preparando download…")
        self.engine.clear_cancellation()
        self._download_future = self._executor.submit(self._download_worker, request)

    def _download_worker(self, request: DownloadRequest) -> None:
        try:
            result = self.engine.download(request, self._events.put)
            self._events.put({"type": "download_done", "request": request, "result": result})
        except DownloadCancelled:
            self._events.put({"type": "download_cancelled"})
        except Exception as exc:
            self.log.exception("Download falhou")
            self._events.put({"type": "download_error", "message": self._friendly_error(exc)})

    def _cancel_download(self) -> None:
        if self._download_future and not self._download_future.done():
            self.engine.cancel()
            self.stop_button.configure(state="disabled")
            self._set_status("Cancelando download atual…")

    @staticmethod
    def _friendly_error(error: Exception) -> str:
        if isinstance(error, FileNotFoundError):
            return str(error)
        if isinstance(error, (PermissionError, NotADirectoryError)):
            return "Não foi possível gravar na pasta escolhida. Escolha uma pasta com permissão de escrita."
        text = str(error)
        if "cookies" in text.lower():
            return "Não foi possível ler os cookies do Chrome. Feche o Chrome ou desmarque a opção."
        if "ffmpeg" in text.lower():
            return "O FFmpeg falhou. Confirme se os arquivos em ffmpeg/bin estão completos."
        return "Não foi possível concluir o download. Verifique o link, sua conexão e app.log para detalhes."

    def _update_queue_label(self) -> None:
        self.queue_label.configure(text=f"Fila: {len(self._queue)} item(ns) restante(s)")

    # ---------- GIF ----------
    def _select_gif_source(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Vídeos", "*.mp4 *.mkv *.avi *.mov *.webm")])
        if path:
            self.video_gif_path = Path(path)
            self.gif_file_label.configure(text=short_text(self.video_gif_path.name, 55), text_color="white")
            self._update_gif_name()

    def _gif_options(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Opções do GIF")
        dialog.geometry("420x225")
        dialog.transient(self)
        ctk.CTkLabel(dialog, text="Qualidade e pasta de saída", font=("Arial", 16, "bold")).pack(pady=(18, 10))
        quality = ctk.CTkComboBox(dialog, values=list(GIF_QUALITY), width=140)
        quality.set(self.gif_quality)
        quality.pack(pady=5)
        folder_label = ctk.CTkLabel(dialog, text=short_text(str(self.gif_output_dir), 52), text_color="#B5B5B5")
        folder_label.pack(pady=5)
        def choose_folder() -> None:
            selected = filedialog.askdirectory(initialdir=str(self.gif_output_dir), parent=dialog)
            if selected:
                self.gif_output_dir = Path(selected)
                folder_label.configure(text=short_text(selected, 52))
        ctk.CTkButton(dialog, text="Escolher pasta", command=choose_folder).pack(pady=4)
        def save() -> None:
            self.gif_quality = quality.get()
            self._update_gif_name()
            dialog.destroy()
        ctk.CTkButton(dialog, text="SALVAR", fg_color=COLORS["download"], command=save).pack(pady=8)

    def _gif_target(self) -> Path | None:
        return self.gif_output_dir / f"{self.video_gif_path.stem}_gif_{int(time.time())}.gif" if self.video_gif_path else None

    def _update_gif_name(self) -> None:
        if self.video_gif_path:
            preview = self.gif_output_dir / f"{self.video_gif_path.stem}_gif_{{data}}.gif"
            self.gif_name_label.configure(text=f"Saída: {short_text(str(preview), 80)}")

    def _convert_gif(self) -> None:
        if self._download_future and not self._download_future.done():
            self._set_status("Aguarde a fila de downloads terminar antes de converter um GIF.", error=True)
            return
        if self._update_future and not self._update_future.done():
            self._set_status("Aguarde a atualização do yt-dlp terminar.", error=True)
            return
        if not self.video_gif_path:
            self._set_status("Escolha um vídeo para criar o GIF.", error=True)
            return
        if not self.engine.ffmpeg_path:
            self._set_status("FFmpeg não encontrado. A conversão de GIF não está disponível.", error=True)
            return
        output = self._gif_target()
        assert output is not None
        fps, width = GIF_QUALITY[self.gif_quality]
        self.gif_button.configure(state="disabled", text="PROCESSANDO…")
        self.download_button.configure(state="disabled")
        self.update_button.configure(state="disabled")
        self.engine.clear_cancellation()
        self._gif_future = self._executor.submit(self._gif_worker, self.video_gif_path, output, fps, width)

    def _gif_worker(self, source: Path, output: Path, fps: int, width: int) -> None:
        try:
            result = self.engine.convert_gif(source, output, fps, width, 0, 5, self._events.put)
            self._events.put({"type": "gif_done", "path": result})
        except DownloadCancelled:
            self._events.put({"type": "gif_cancelled"})
        except Exception as exc:
            self.log.exception("Conversão de GIF falhou")
            self._events.put({"type": "gif_error", "message": self._friendly_error(exc)})

    # ---------- update, history, and lifecycle ----------
    def _update_yt_dlp(self) -> None:
        if self._download_future and not self._download_future.done():
            self._set_status("A atualização não pode rodar durante um download.", error=True)
            return
        if self._gif_future and not self._gif_future.done():
            self._set_status("A atualização não pode rodar durante a conversão de GIF.", error=True)
            return
        self.update_button.configure(state="disabled", text="ATUALIZANDO…")
        self.download_button.configure(state="disabled")
        self.gif_button.configure(state="disabled")
        self._update_future = self._executor.submit(self._update_worker)

    def _update_worker(self) -> None:
        try:
            message = DownloaderEngine.update_yt_dlp(self._events.put)
            self._events.put({"type": "update_done", "message": message})
        except Exception as exc:
            self.log.exception("Atualização do yt-dlp falhou")
            self._events.put({"type": "update_error", "message": "Não foi possível atualizar o yt-dlp. Veja app.log para detalhes."})

    def _open_history(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Histórico de downloads")
        dialog.geometry("650x480")
        dialog.minsize(540, 360)
        container = ctk.CTkScrollableFrame(dialog)
        container.pack(fill="both", expand=True, padx=12, pady=12)
        entries = self.history.list()
        if not entries:
            ctk.CTkLabel(container, text="Ainda não há downloads no histórico.").pack(pady=30)
            return
        for item in entries:
            card = ctk.CTkFrame(container)
            card.pack(fill="x", pady=4)
            ctk.CTkLabel(card, text=short_text(item.get("title", "Sem título"), 75), anchor="w", font=("Arial", 13, "bold")).pack(fill="x", padx=9, pady=(7, 0))
            ctk.CTkLabel(card, text=f"{item.get('date', '')}\n{short_text(item.get('path', ''), 78)}", anchor="w", justify="left", text_color="#B5B5B5").pack(fill="x", padx=9, pady=(2, 6))
            buttons = ctk.CTkFrame(card, fg_color="transparent")
            buttons.pack(fill="x", padx=7, pady=(0, 7))
            path = Path(item.get("path") or self.download_dir)
            ctk.CTkButton(buttons, text="Abrir pasta", width=94, command=lambda p=path: self._open_folder(p.parent if p.suffix else p)).pack(side="left")
            ctk.CTkButton(buttons, text="Copiar caminho", width=104, command=lambda p=path: self._copy_path(p)).pack(side="left", padx=5)

    def _copy_path(self, path: Path) -> None:
        self.clipboard_clear()
        self.clipboard_append(str(path))
        self._set_status("Caminho copiado para a área de transferência.", success=True)

    def _open_folder(self, folder: Path) -> None:
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except OSError:
            self._set_status("Não foi possível abrir a pasta selecionada.", error=True)

    def _set_ffmpeg_notice(self) -> None:
        if not self.engine.ffmpeg_path:
            self._set_status("FFmpeg não encontrado. Vídeo, MP3 e GIF exigem ffmpeg/bin/ffmpeg.exe ou FFmpeg no PATH.", error=True)

    def _cycle_appearance(self) -> None:
        modes = ("Dark", "Light", "System")
        self.appearance = modes[(modes.index(self.appearance) + 1) % len(modes)]
        ctk.set_appearance_mode(self.appearance)
        self.theme_button.configure(text=f"Tema: {self.appearance}")
        self.settings.save({"appearance": self.appearance})

    def _set_status(self, message: str, error: bool = False, success: bool = False) -> None:
        color = "red" if error else COLORS["download"] if success else "#E5E5E5"
        self.status_label.configure(text=message, text_color=color)

    def _close_app(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.engine.cancel()
        self._executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()

    # ---------- event bridge: runs only in the Tk thread ----------
    def _drain_events(self) -> None:
        if self._closing:
            return
        try:
            while True:
                self._handle_event(self._events.get_nowait())
        except queue.Empty:
            pass
        self.after(80, self._drain_events)

    def _handle_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type == "progress":
            self.progress.set(float(event.get("progress", 0)))
            self._set_status(str(event.get("text", "Baixando…")))
        elif event_type == "status":
            self._set_status(str(event.get("text", "")))
        elif event_type == "preview" and event["url"] == self.entry_url.get().strip():
            info = event["info"]
            views = info["view_count"]
            views_text = f"{int(views):,}".replace(",", ".") if isinstance(views, int) else "Não informado"
            self.title_label.configure(text=short_text(info["title"]))
            self.details_label.configure(text=f"Duração: {format_duration(info['duration'])}\nCanal: {short_text(info['uploader'], 45)} • Visualizações: {views_text}")
            image = event.get("image")
            if isinstance(image, Image.Image):
                image.thumbnail((160, 90))
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(160, 90))
                self.thumb.configure(image=ctk_image, text="")
                self.thumb.image = ctk_image
            else:
                self.thumb.configure(image=None, text="Sem imagem")
            if not (self._download_future and not self._download_future.done()) and not (self._gif_future and not self._gif_future.done()):
                self._set_status("Pronto para baixar", success=True)
        elif event_type == "preview_error" and event["url"] == self.entry_url.get().strip():
            self._preview_url = ""  # Permite tentar o mesmo link novamente.
            self.title_label.configure(text="Não foi possível mostrar o preview.")
            self.details_label.configure(text="Confirme se o link está correto e é público.")
            self._set_status(event["message"], error=True)
        elif event_type == "download_done":
            result = event["result"]
            self.history.add(result["title"], event["request"].url, result["path"])
            self.progress.set(1)
            self._set_status("Download completo!", success=True)
            self._download_future = None
            self._start_next_download()
        elif event_type == "download_cancelled":
            self.progress.set(0)
            self._set_status("Download cancelado.", error=True)
            self._download_future = None
            self._start_next_download()
        elif event_type == "download_error":
            self.progress.set(0)
            self._set_status(event["message"], error=True)
            messagebox.showerror("Erro no download", event["message"], parent=self)
            self._download_future = None
            self._start_next_download()
        elif event_type == "gif_progress":
            self.progress.set(float(event.get("progress", 0)))
            self._set_status(str(event["text"]))
        elif event_type == "gif_done":
            self._gif_future = None
            self.gif_button.configure(state="normal", text="CONVERTER PARA GIF")
            self.download_button.configure(state="normal", text="BAIXAR AGORA", fg_color=COLORS["download"])
            self.update_button.configure(state="normal", text="🛠 Atualizar")
            self.progress.set(1)
            self._set_status(f"GIF salvo em {event['path'].name}", success=True)
            messagebox.showinfo("GIF criado", f"GIF salvo em:\n{event['path']}", parent=self)
        elif event_type == "gif_error":
            self._gif_future = None
            self.gif_button.configure(state="normal", text="CONVERTER PARA GIF")
            self.download_button.configure(state="normal", text="BAIXAR AGORA", fg_color=COLORS["download"])
            self.update_button.configure(state="normal", text="🛠 Atualizar")
            self._set_status(event["message"], error=True)
            messagebox.showerror("Erro na conversão", event["message"], parent=self)
        elif event_type == "gif_cancelled":
            self._gif_future = None
            self.gif_button.configure(state="normal", text="CONVERTER PARA GIF")
            self.download_button.configure(state="normal", text="BAIXAR AGORA", fg_color=COLORS["download"])
            self.update_button.configure(state="normal", text="🛠 Atualizar")
            self.progress.set(0)
            self._set_status("Conversão de GIF cancelada.", error=True)
        elif event_type == "update_done":
            self._update_future = None
            self.update_button.configure(state="normal", text="🛠 Atualizar")
            self.download_button.configure(state="normal", text="BAIXAR AGORA", fg_color=COLORS["download"])
            self.gif_button.configure(state="normal")
            self._set_status(event["message"], success=True)
            messagebox.showinfo("Atualização", event["message"], parent=self)
        elif event_type == "update_error":
            self._update_future = None
            self.update_button.configure(state="normal", text="🛠 Atualizar")
            self.download_button.configure(state="normal", text="BAIXAR AGORA", fg_color=COLORS["download"])
            self.gif_button.configure(state="normal")
            self._set_status(event["message"], error=True)
            messagebox.showerror("Atualização", event["message"], parent=self)


if __name__ == "__main__":
    DownloaderApp().mainloop()
