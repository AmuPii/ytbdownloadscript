import os
import sys
import yt_dlp

# ------------------ CAMINHOS ------------------

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "ffmpeg", "bin")
    else:
        return r"C:\ffmpeg\bin"

FFMPEG_PATH = get_ffmpeg_path()

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

# ------------------ DOWNLOAD ------------------

url = input("Cole a URL do vídeo ou playlist do YouTube: ").strip()

if not url:
    print("URL inválida.")
    exit()

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

opcoes = {
    "format": "bv*[ext=mp4]+ba*[ext=m4a]/b[ext=mp4]",
    "merge_output_format": "mp4",
    "outtmpl": os.path.join(
        DOWNLOAD_DIR,
        "%(playlist_title|single)s",
        "%(title)s.%(ext)s"
    ),
    "ffmpeg_location": FFMPEG_PATH,
    "ignoreerrors": True
}

with yt_dlp.YoutubeDL(opcoes) as ydl:
    ydl.download([url])

print("Download concluído!")
