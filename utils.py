import os
import sys
import re

def get_ffmpeg_path():
    """
    Localiza o executável do FFmpeg de forma relativa (portátil).
    Funciona tanto rodando em Python (.py) quanto se você criar um executável (.exe) no futuro.
    """
    
    # Descobre o diretório base onde o programa está rodando
    if getattr(sys, 'frozen', False):
        # Se for um executável compilado (PyInstaller)
        base_path = os.path.dirname(sys.executable)
    else:
        # Se for script Python normal
        base_path = os.path.dirname(os.path.abspath(__file__))

    # Monta o caminho esperado: Pasta do Projeto > ffmpeg > bin > ffmpeg.exe
    caminho_ffmpeg = os.path.join(base_path, "ffmpeg", "bin", "ffmpeg.exe")

    if os.path.exists(caminho_ffmpeg):
        return caminho_ffmpeg
            
    # Última tentativa: verifica se está instalado no Windows globalmente
    return "ffmpeg"

class DownloadLogger:
    """
    Classe que serve de ponte entre o yt-dlp e a barra de progresso da interface.
    """
    def __init__(self, callback_func):
        self.callback_func = callback_func

    def hook(self, d):
        if d['status'] == 'downloading':
            p_str = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'Calculando...')
            
            # Limpa caracteres de cor (ANSI)
            p_str = re.sub(r'\x1b\[[0-9;]*m', '', p_str)
            speed = re.sub(r'\x1b\[[0-9;]*m', '', speed)

            if self.callback_func:
                self.callback_func({
                    'status': 'downloading',
                    '_percent_str': p_str,
                    '_speed_str': speed
                })
            
        elif d['status'] == 'finished':
            if self.callback_func:
                self.callback_func({
                    'status': 'finished',
                    '_percent_str': '100%',
                    '_speed_str': 'Processando...'
                })