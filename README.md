# 🚀 Downloader do Herickão

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Enabled-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

**Sua suíte completa para baixar mídias da internet e converter vídeos.** Uma aplicação desktop moderna, rápida e com tema escuro, desenvolvida para facilitar o download de vídeos em alta qualidade e a criação de GIFs.

---

## ✨ Funcionalidades Principais

### 📥 Download Multiplataforma
Baixe vídeos e áudios das maiores redes sociais com apenas um link:
| Plataforma | Suporte |
| :--- | :--- |
| **YouTube** | ✅ Vídeo (4K/1080p) & Áudio (MP3) |
| **TikTok** | ✅ Sem marca d'água |
| **Instagram** | ✅ Reels e Vídeos |
| **Facebook** | ✅ Vídeos Públicos |
| **Twitter / X** | ✅ Clipes e Mídias |
| **Twitch** | ✅ Clipes e VODs |

### 🎞️ [NOVO] Conversor de GIF Integrado
Transforme seus vídeos locais em GIFs animados diretamente pelo app!
* **Qualidade:** Utiliza filtro *Lanczos* para máxima fidelidade de cor.
* **Performance:** Processamento em segundo plano (não trava a tela).
* **Simples:** Basta selecionar o arquivo MP4/MKV e clicar em converter.

### ⚙️ Outros Recursos
* **Seletor de Qualidade:** Escolha entre "Melhor Qualidade", "1080p", "720p" ou extraia apenas o áudio "MP3".
* **Abertura Rápida:** Botão direto para abrir a pasta de Downloads.
* **Auto-Update:** Ferramenta integrada para atualizar as bibliotecas de download (`yt-dlp`).

---

## 🚀 O que há de novo na v2.0?

Esta versão traz uma refatoração completa focada em estabilidade e novas ferramentas:

* ✅ **Nova Interface:** Janela expandida e harmonizada com tema *Dark Blue*.
* ✅ **Módulo GIF:** Nova seção dedicada para conversão de mídia local.
* ✅ **Fix de Foco:** Corrigido bug onde a janela perdia o foco ao alternar entre plataformas.
* ✅ **Multithreading:** Downloads e conversões agora rodam em *threads* separadas, garantindo que o app nunca congele.
* ✅ **Portabilidade:** Estrutura de pastas otimizada para execução fácil no Windows.

---

## 📦 Como Instalar e Rodar

Não é necessário instalar Python se você estiver usando a versão compilada (`.exe`).

1.  Baixe o arquivo `.zip` da última versão.
2.  Extraia a pasta em qualquer lugar do seu computador.
3.  **IMPORTANTE:** Certifique-se de que o arquivo `ffmpeg.exe` esteja dentro da mesma pasta do `DownloaderHerickao.exe`.
4.  Execute o `DownloaderHerickao.exe`.

### Estrutura da Pasta
```
📂 DownloaderHerickao/
 ├── 📄 DownloaderHerickao.exe  (Clique aqui para abrir)
 ├── 📄 ffmpeg.exe              (Motor de conversão - NÃO APAGUE)
 └── 📂 Download               (será criado após rodar o .exe pela primeira vez)
```
## 🛠️ Tecnologias Utilizadas
Este projeto foi construído com ferramentas open-source poderosas:

Linguagem: Python 3

Interface Gráfica: CustomTkinter (Modern UI)

Engine de Download: yt-dlp 

Processamento de Mídia: FFmpeg

## 📝 Licença
Desenvolvido por Herickão.

Uso livre para fins pessoais.

<img width="702" height="812" alt="image" src="https://github.com/user-attachments/assets/68e008c5-2e92-4218-b718-6a030f1505be" />
