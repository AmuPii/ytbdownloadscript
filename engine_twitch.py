import yt_dlp
import os
import utils

def baixar(url, output_dir, hook_progresso, qualidade):
    """
    Engine dedicada para Twitch (Clips e VODs).
    Versão Estável: Sem conversão de GIF.
    """
    
    # 1. Definição da Qualidade
    if qualidade == "MP3":
        format_str = 'bestaudio/best'
    else:
        format_str = 'bestvideo+bestaudio/best'

    # 2. Localiza o FFmpeg (Essencial para não dar erro de conversão)
    caminho_ffmpeg = utils.get_ffmpeg_path()
    ffmpeg_location = None
    if "ffmpeg.exe" in caminho_ffmpeg and os.path.exists(caminho_ffmpeg):
        ffmpeg_location = os.path.dirname(caminho_ffmpeg)

    # 3. Configurações do yt-dlp
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(output_dir, 'Twitch_%(title)s [%(id)s].%(ext)s'),
        'progress_hooks': [utils.DownloadLogger(hook_progresso).hook],
        'quiet': True,
        'no_warnings': True,
        
        # Injeta o caminho do FFmpeg para garantir que o yt-dlp o encontre
        'ffmpeg_location': ffmpeg_location,

        # Conversão de áudio se for MP3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if qualidade == "MP3" else [],
        
        # Se for vídeo, garante MP4
        'merge_output_format': 'mp4' if qualidade != "MP3" else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            
    except Exception as e:
        # Repassa o erro para a interface mostrar o popup vermelho
        raise e