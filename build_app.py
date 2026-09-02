import PyInstaller.__main__
import customtkinter
import os
import sys

# 1. Localiza onde o CustomTkinter está instalado
path_ctk = os.path.dirname(customtkinter.__file__)

# 2. Configurações
arquivo_principal = "youtube_downloader_window.py" 
nome_app = "DownloaderHerickao"

# 3. Executa a compilação
print(">>> Iniciando a compilação...")
print(">>> Isso vai incluir todas as bibliotecas necessárias.")

# Lista de comandos do PyInstaller
comandos = [
    arquivo_principal,
    '--name=%s' % nome_app,
    '--onefile',               # Cria um único arquivo .exe
    '--noconsole',             # Remove a tela preta
    '--windowed',              
    '--clean',                 # Limpa cache antigo para evitar bugs
    
    # IMPORTANTE 1: Inclui o CustomTkinter
    f'--add-data={path_ctk};customtkinter', 
    
    # IMPORTANTE 2: Força o PyInstaller a pegar TUDO do yt-dlp 
    # (Evita erro de "extractor not found")
    '--collect-all=yt_dlp',
    '--add-data=ffmpeg;ffmpeg',  # Inclui FFmpeg no executável onefile
    
    # Opcional: Se tiver icone, tire a # da linha abaixo
    # '--icon=seu_icone.ico'   
]

PyInstaller.__main__.run(comandos)

print("\n>>> SUCESSO! Verifique a pasta 'dist'.")
print(">>> IMPORTANTE: Não esqueça de colocar o FFmpeg junto com o .exe!")
