import tkinter as tk
from tkinter import messagebox
import yt_dlp
import os
import subprocess
import threading
import sys

# Pasta onde os vídeos serão salvos
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
FFMPEG_PATH = r"C:\ffmpeg\bin"

def caminho_ffmpeg():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "ffmpeg", "bin")
    else:
        return r"C:\ffmpeg\bin"

FFMPEG_PATH = caminho_ffmpeg()


def baixar_video():
    url = entry_url.get().strip()

    if not url:
        messagebox.showwarning("Aviso", "Insira o link do YouTube.")
        return

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    opcoes = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "ffmpeg_location": FFMPEG_PATH,
        "quiet": True,
        "no_warnings": True
    }

    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
        messagebox.showinfo("Sucesso", "Download concluído com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao baixar o vídeo:\n{e}")
    finally:
        btn_download.config(state=tk.NORMAL)


def iniciar_download():
    btn_download.config(state=tk.DISABLED)
    thread = threading.Thread(target=baixar_video)
    thread.start()


def abrir_pasta():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    subprocess.Popen(f'explorer "{DOWNLOAD_DIR}"')


# ---------------- INTERFACE ----------------

janela = tk.Tk()
janela.title("YouTube Downloader")
janela.geometry("520x180")
janela.resizable(False, False)

lbl = tk.Label(janela, text="Cole o link do vídeo do YouTube:")
lbl.pack(pady=(15, 5))

entry_url = tk.Entry(janela, width=65)
entry_url.pack(pady=5)

frame = tk.Frame(janela)
frame.pack(pady=20)

btn_download = tk.Button(
    frame,
    text="Baixar Vídeo",
    width=18,
    command=iniciar_download
)
btn_download.pack(side=tk.LEFT, padx=10)

btn_open = tk.Button(
    frame,
    text="Abrir Pasta",
    width=18,
    command=abrir_pasta
)
btn_open.pack(side=tk.LEFT, padx=10)

janela.mainloop()
