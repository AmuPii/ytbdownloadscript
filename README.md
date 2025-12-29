# 📥 Downloader do Herickão - Multi-Platform Video Downloader

Um aplicativo desktop moderno, desenvolvido em Python com **CustomTkinter**, para baixar vídeos e áudios das principais redes sociais com alta qualidade. O projeto foca em simplicidade, design limpo (Dark Mode) e organização automática de arquivos.

## 🚀 Funcionalidades

- **Multi-Plataforma:** Suporte para YouTube, TikTok, Instagram, Facebook, Twitter (X) e Twitch.
- **Organização Inteligente:** Cria pastas separadas automaticamente para cada plataforma (ex: `Downloads/TikTok`, `Downloads/YouTube`).
- **Seleção de Qualidade:** Escolha entre "Melhor Qualidade", "1080p", "720p" ou apenas áudio "MP3".
- **Conversão Automática:** Converte vídeos para áudio MP3 automaticamente utilizando FFmpeg.
- **Interface Moderna:** UI amigável e responsiva com tema escuro (Dark Mode).
- **Sem Anúncios:** Download direto e rápido, sem pop-ups ou limitações de sites web.

## 📋 Plataformas Suportadas

| Plataforma | Vídeo | Áudio (MP3) | Obs. |
| :--- | :---: | :---: | :--- |
| **YouTube** | ✅ | ✅ | Suporta playlists e vídeos longos. |
| **TikTok** | ✅ | ✅ | Baixa sem marca d'água (via API). |
| **Instagram** | ✅ | ✅ | Reels e vídeos do feed. |
| **Facebook** | ✅ | ✅ | Vídeos públicos. |
| **Twitter (X)** | ✅ | ✅ | |
| **Twitch** | ✅ | ✅ | Clips e VODs. |

## 🛠️ Instalação e Uso (Para Usuários)

1. Baixe o arquivo `.zip` ou o executável fornecido.
2. **Importante:** Mantenha a pasta `ffmpeg` no mesmo local do arquivo `.exe`. A estrutura deve ser:
   ```text
   📁 Pasta do App/
    ├── DownloaderHerickao.exe
    └── 📁 ffmpeg/
         └── 📁 bin/
              └── ffmpeg.exe
              
Execute o DownloaderHerickao.exe.

Selecione a plataforma, cole o link e clique em BAIXAR AGORA.

💻 Configuração para Desenvolvedores
Se você deseja rodar o código fonte ou modificá-lo:

Pré-requisitos
Python 3.8 ou superior.

FFmpeg instalado no sistema ou na pasta raiz do projeto.

1. Clonar e Instalar Dependências
Crie um ambiente virtual (recomendado) e instale as bibliotecas necessárias:

Bash

pip install customtkinter yt-dlp requests
(Ou use o arquivo requirements.txt se tiver criado um)

2. Estrutura de Arquivos Necessária
Certifique-se de que o executável do FFmpeg esteja em ffmpeg/bin/ffmpeg.exe na raiz do projeto para garantir a portabilidade.

3. Rodar o App
Bash

python youtube_downloader_window.py
🏗️ Como Compilar (Criar .exe)
Para transformar o script Python em um executável Windows portátil:

Instale o PyInstaller:

Bash

pip install pyinstaller
Utilize o script de build incluso ou rode o comando abaixo (ajustando o caminho do CustomTkinter):

Bash

pyinstaller --noconsole --onefile --windowed --add-data "CAMINHO_DO_CUSTOMTKINTER;customtkinter" youtube_downloader_window.py
Após compilar, copie manualmente a pasta ffmpeg para dentro da pasta dist criada, ao lado do executável gerado.

🧩 Estrutura do Código
O projeto é modularizado para facilitar a manutenção:

youtube_downloader_window.py: Interface Gráfica (GUI) e lógica principal.

utils.py: Funções utilitárias (logger, busca de FFmpeg, conversões).

engine_*.py: Módulos específicos para lidar com a lógica de download de cada plataforma (YouTube, TikTok, etc.).

⚖️ Aviso Legal
Este software foi desenvolvido para fins educacionais e de uso pessoal. O download de conteúdo protegido por direitos autorais sem permissão pode violar os termos de serviço das plataformas. Utilize com responsabilidade.

Desenvolvido por Herickão.
            