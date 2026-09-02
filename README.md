# 🚀 Downloader do Herickão

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Enabled-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

**Sua suíte completa para baixar mídias da internet e converter vídeos.** Um App Caseiro para desktop, rápida e com tema escuro, desenvolvida para facilitar o download de vídeos em alta qualidade e a criação de GIFs.

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
* **Performance:** Processamento em segundo plano (não trava o pc nem sobre-usa Recursos.).
* **Simples:** Basta selecionar o arquivo MP4/MKV e clicar em converter.

### ⚙️ Outros Recursos
* **Seletor de Qualidade:** Escolha entre "Melhor Qualidade", "1080p", "720p" ou extraia apenas o áudio "MP3".
* **Abertura Rápida:** Botão direto para abrir a pasta de Downloads.
* **Auto-Update:** Ferramenta integrada para atualizar as bibliotecas de download (`yt-dlp`).

---

## 🚀 O que há de novo na v4.0?

traz uma refatoração completa focada em estabilidade e novas ferramentas:

* ✅ **Nova Interface:** Janela expandida e harmonizada com tema *Dark Blue*.
* ✅ **Módulo GIF:** Nova seção dedicada para conversão de mídia local.
* ✅ **Fix de Foco:** Corrigido bug onde a janela perdia o foco ao alternar entre plataformas.
* ✅ **Multithreading:** Downloads e conversões agora rodam em *threads* separadas, garantindo que o app nunca congele.
* ✅ **Portabilidade:** Estrutura de pastas otimizada para execução fácil no Windows.
* ✅ **Fila, histórico e cancelamento:** vários links podem ser enfileirados e o download atual pode ser interrompido.
* ✅ **Preview informativo:** título, duração, canal e visualizações antes de baixar.
* ✅ **Atualizações seguras:** no script, o botão atualiza `yt-dlp` via pip; no `.exe`, baixa o standalone e informa a limitação da biblioteca embutida.

## 🔄 Manutenção do yt-dlp

Sites mudam com frequência. Use o botão **Atualizar** regularmente ou execute:

```powershell
python -m pip install --upgrade yt-dlp
```

Para preparar o ambiente de desenvolvimento: `python -m pip install -r requirements.txt`.
O aplicativo registra detalhes técnicos em `app.log`; a interface mostra uma mensagem curta e amigável em caso de erro.

---

## 📦 Como Instalar e Rodar

Não é necessário instalar Python se você estiver usando a versão compilada (`.exe`).

1.  Baixe o arquivo `.zip` da última versão. (`presente na aba Releases`)
2.  Extraia a pasta em qualquer lugar do seu computador.
3.  **IMPORTANTE:** A distribuição inclui `ffmpeg/bin/ffmpeg.exe`. Ao executar o script, mantenha essa pasta no projeto ou instale FFmpeg no `PATH`.
4.  Execute o `DownloaderHerickao.exe`.

### Estrutura da Pasta
```
📂 DownloaderHerickao/
 ├── 📄 DownloaderHerickao.exe  (Clique aqui para abrir)
 ├── 📄 ffmpeg.exe              (Motor de conversão - NÃO APAGUE)
 └── 📂 Download               (será criado após rodar o .exe pela primeira vez)
```
## 🛠️ Tecnologias Utilizadas
Este projeto foi construído com ferramentas open-source:

Linguagem: Python 3

Interface Gráfica: CustomTkinter (Modern UI)

Engine de Download: yt-dlp 

Processamento de Mídia: FFmpeg

## 📝 Licença
Desenvolvido por Herickão.

Uso livre para fins pessoais.

<img width="702" height="812" alt="image" src="https://github.com/user-attachments/assets/68e008c5-2e92-4218-b718-6a030f1505be" />
