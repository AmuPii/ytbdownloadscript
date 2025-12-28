import PyInstaller.__main__
import customtkinter
import os

# 1. Localiza onde o CustomTkinter está instalado no seu PC
path_ctk = os.path.dirname(customtkinter.__file__)

# 2. Define o nome do arquivo principal e do executável
arquivo_principal = "youtube_downloader_window.py" # <--- VERIFIQUE SE O NOME DO SEU ARQUIVO É ESSE
nome_app = "DownloaderHerickao"

# 3. Executa o PyInstaller com as configurações corretas
print("Iniciando a compilação... Isso pode demorar uns minutos.")

PyInstaller.__main__.run([
    arquivo_principal,
    '--name=%s' % nome_app,
    '--onefile',               # Cria um único arquivo .exe
    '--noconsole',             # Não mostra a tela preta do CMD ao fundo
    '--windowed',              # Modo janela
    f'--add-data={path_ctk};customtkinter', # Importante: Inclui os temas do CustomTkinter
    '--clean',                 # Limpa cache anterior
    # '--icon=icone.ico'       # Se tiver um ícone (.ico), descomente esta linha
])

print("\nCompilação finalizada! Verifique a pasta 'dist'.")