import yt_dlp
import os
import utils

def baixar(url, output_dir, hook_progresso, qualidade):
    """
    Engine dedicada para YouTube.
    Versão Estável: Sem conversão de GIF.
    """
    
    # 1. Definição da Qualidade
    if qualidade == "MP3":
        format_str = 'bestaudio/best'
    elif qualidade == "1080p":
        format_str = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif qualidade == "720p":
        format_str = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    else: # "Melhor"
        format_str = "bestvideo+bestaudio/best"

    # 2. Localiza a pasta do FFmpeg
    caminho_ffmpeg = utils.get_ffmpeg_path()
    ffmpeg_location = None
    if "ffmpeg.exe" in caminho_ffmpeg and os.path.exists(caminho_ffmpeg):
        ffmpeg_location = os.path.dirname(caminho_ffmpeg)

    # 3. Configurações do yt-dlp
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s'),
        'progress_hooks': [utils.DownloadLogger(hook_progresso).hook],
        'quiet': True,
        'no_warnings': True,
        
        # Aponta para a pasta ./ffmpeg/bin/ para garantir que junte áudio+vídeo
        'ffmpeg_location': ffmpeg_location,

        # Conversão de áudio se for MP3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if qualidade == "MP3" else [],
        
        # Garante saída em MP4 para vídeo
        'merge_output_format': 'mp4' if qualidade != "MP3" else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

    except Exception as e:
        raise e