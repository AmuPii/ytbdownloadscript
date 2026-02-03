import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import subprocess
import threading
import sys
import json
import shutil
import time # Adicionado import explicitamente para evitar erros no GIF
from typing import Dict, Optional

# Bibliotecas para Preview e Metadados
import yt_dlp
import requests
from PIL import Image, ImageTk
from io import BytesIO

# === CONFIGURAÇÕES GERAIS ===
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_DIR = os.path.join(BASE_PATH, "downloads")
CONFIG_FILE = os.path.join(BASE_PATH, "settings.json")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DEFAULT_GIF_CONFIG = {"fps": "15", "width": "480", "start": 0, "duration": 5}

CORES = {
    "inativo": "#474444", "texto_inativo": "#FFFFFF",
    "youtube": "#FF0000", "facebook": "#0D09FD", "instagram": "#B82455",
    "twitter": "#000000", "twitch": "#9146FF", "tiktok": "#000000",
    "hover_tiktok": "#25F4EE", "download_btn": "#00C853", "folder_btn": "#2980B9", 
    "fix_btn": "#E67E22", "gif_btn": "#6A5ACD", "stop_btn": "#D32F2F",
    "card_bg": "#1F1F1F"
}

class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Downloader Pro v3.0")
        self.geometry("600x600")
        self.resizable(False, False)
        
        # Garante fechamento completo
        self.protocol("WM_DELETE_WINDOW", self._encerrar_app)

        # Estado
        self.ffmpeg_path = self._check_ffmpeg()
        self.plataforma_atual = "YouTube"
        self.video_gif_path = ""
        self.is_downloading = False
        self.gif_config = DEFAULT_GIF_CONFIG.copy()
        
        # Variáveis de Controle de Loop (Para não travar o preview)
        self.ultimo_url_verificado = ""
        self.verificando_agora = False

        # UI Elements
        self.plataforma_botoes = {}

        self._setup_header()
        self._setup_platforms()
        self._setup_inputs()
        self._setup_preview_area()
        self._setup_download_area()
        self._setup_gif_converter()

        self._load_config()

        # Bind apenas no Enter
        self.entry_url.bind("<Return>", lambda event: self._iniciar_verificacao_url())

    def _encerrar_app(self):
        self.destroy()
        os._exit(0)

    # --- SETUP UI ---
    def _setup_header(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=(15, 5), padx=20, fill="x")
        ctk.CTkLabel(frame, text="Downloader Pro", font=("Roboto Black", 24)).pack(side="left")
        ctk.CTkButton(frame, text="🛠 Atualizar Libs", width=110, fg_color=CORES["fix_btn"], 
                      command=self._thread_atualizar_libs).pack(side="right")

    def _setup_platforms(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=10, padx=10, fill="x")
        btn_config = [
            ("YouTube", CORES["youtube"], 0, 0), ("Facebook", CORES["facebook"], 0, 1),
            ("Instagram", CORES["instagram"], 0, 2), ("Twitter", CORES["twitter"], 1, 0),
            ("Twitch", CORES["twitch"], 1, 1), ("TikTok", CORES["tiktok"], 1, 2)
        ]
        frame.grid_columnconfigure((0,1,2), weight=1)
        for name, color, r, c in btn_config:
            hover = CORES["hover_tiktok"] if name == "TikTok" else None
            btn = ctk.CTkButton(frame, text=name.upper(), height=45, font=("Arial", 13, "bold"),
                                command=lambda n=name, cl=color, h=hover: self._selecionar_plataforma(n, cl, h))
            btn.grid(row=r, column=c, sticky="ew", padx=3, pady=3)
            self.plataforma_botoes[name] = btn

    def _setup_inputs(self):
        frame_inp = ctk.CTkFrame(self, fg_color="transparent")
        frame_inp.pack(pady=(5, 0), padx=20, fill="x")
        
        self.entry_url = ctk.CTkEntry(frame_inp, height=45, placeholder_text="Cole o link aqui...", font=("Arial", 14))
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Auto-Detecção ao colar
        self.entry_url.bind("<Control-v>", lambda e: self.after(100, self._iniciar_verificacao_url))
        self.entry_url.bind("<ButtonRelease-3>", lambda e: self.after(100, self._iniciar_verificacao_url))

        ctk.CTkButton(frame_inp, text="📋", width=50, height=45, fg_color="#444444", 
                      command=self._colar_area_transferencia).pack(side="right")

        frame_ops = ctk.CTkFrame(self, fg_color="transparent")
        frame_ops.pack(pady=5)
        ctk.CTkLabel(frame_ops, text="Qualidade:", font=("Arial", 12)).pack(side="left", padx=5)
        self.combo_qualidade = ctk.CTkComboBox(frame_ops, values=["Melhor", "1080p", "720p", "MP3"], width=130)
        self.combo_qualidade.pack(side="left")

    def _setup_preview_area(self):
        self.frame_preview = ctk.CTkFrame(self, fg_color=CORES["card_bg"], corner_radius=10)
        self.frame_preview.pack(pady=10, padx=20, fill="x")
        self.frame_preview.pack_propagate(False)
        self.frame_preview.configure(height=0) 

        self.inner_preview = ctk.CTkFrame(self.frame_preview, fg_color="transparent")
        self.inner_preview.pack(fill="both", expand=True, padx=10, pady=10)

        self.lbl_thumb = ctk.CTkLabel(self.inner_preview, text="", width=160, height=90, fg_color="#333")
        self.lbl_thumb.pack(side="left", padx=(0, 15))

        self.frame_info = ctk.CTkFrame(self.inner_preview, fg_color="transparent")
        self.frame_info.pack(side="left", fill="both", expand=True)
        
        self.lbl_titulo = ctk.CTkLabel(self.frame_info, text="Carregando...", font=("Arial", 14, "bold"), anchor="w", wraplength=400)
        self.lbl_titulo.pack(fill="x", pady=(5,0))
        
        self.lbl_info_extra = ctk.CTkLabel(self.frame_info, text="", font=("Arial", 12), text_color="gray", anchor="w")
        self.lbl_info_extra.pack(fill="x")

    def _setup_download_area(self):
        self.lbl_status = ctk.CTkLabel(self, text="Pronto", text_color="gray")
        self.lbl_status.pack(pady=(5, 0))
        self.progress_bar = ctk.CTkProgressBar(self, height=12, progress_color=CORES["download_btn"])
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5, padx=20, fill="x")

        frame_act = ctk.CTkFrame(self, fg_color="transparent")
        frame_act.pack(pady=10, padx=20, fill="x")
        frame_act.grid_columnconfigure((0,1), weight=1)
        
        self.btn_download = ctk.CTkButton(frame_act, text="BAIXAR AGORA", height=55, font=("Arial", 16, "bold"), 
                                          fg_color=CORES["download_btn"], command=self._start_download_thread)
        self.btn_download.grid(row=0, column=0, padx=5, sticky="ew")
        
        ctk.CTkButton(frame_act, text="PASTA", height=55, font=("Arial", 16, "bold"), 
                      fg_color=CORES["folder_btn"], command=lambda: subprocess.Popen(f'explorer "{DOWNLOAD_DIR}"')).grid(row=0, column=1, padx=5, sticky="ew")

    def _setup_gif_converter(self):
        ctk.CTkFrame(self, height=2, fg_color="#333333").pack(fill="x", pady=15, padx=20)
        frame_gif = ctk.CTkFrame(self, fg_color="transparent")
        frame_gif.pack(padx=20, fill="x")
        
        head = ctk.CTkFrame(frame_gif, fg_color="transparent")
        head.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(head, text="🎞 Criador de GIF", font=("Arial", 15, "bold")).pack(side="left")
        
        ctk.CTkButton(head, text="⚙️ Opções", width=80, height=25, fg_color="#555", 
                      command=self._abrir_opcoes_gif).pack(side="right")
        
        frame_input = ctk.CTkFrame(frame_gif, fg_color="#2B2B2B", height=45)
        frame_input.pack(fill="x", pady=5)
        frame_input.pack_propagate(False)
        
        self.lbl_arquivo_gif = ctk.CTkLabel(frame_input, text="Selecione um vídeo...", text_color="gray")
        self.lbl_arquivo_gif.pack(side="left", padx=15)
        ctk.CTkButton(frame_input, text="📂", width=40, fg_color="#444444", command=self._selecionar_video_local).pack(side="right", padx=5, pady=5)
        
        self.btn_converter_gif = ctk.CTkButton(frame_gif, text="CONVERTER PARA GIF", height=45, font=("Arial", 14, "bold"), 
                                               fg_color=CORES["gif_btn"], command=self._thread_converter_gif)
        self.btn_converter_gif.pack(fill="x", pady=10)

    # --- LÓGICA DE METADADOS (SEM PLAYLIST POPUP) ---

    def _iniciar_verificacao_url(self):
        url = self.entry_url.get().strip()
        
        if not url: return
        if self.verificando_agora: return
        if url == self.ultimo_url_verificado: return

        self.verificando_agora = True
        threading.Thread(target=self._buscar_metadados, args=(url,), daemon=True).start()

    def _buscar_metadados(self, url):
        self.after(0, lambda: self.lbl_status.configure(text="Buscando informações...", text_color="white"))
        
        try:
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                # Forçamos noplaylist=True para evitar carregar listas gigantes
                'noplaylist': True, 
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            title = info.get('title', 'Vídeo Detectado')
            thumb_url = info.get('thumbnail') 
            if not thumb_url and 'thumbnails' in info:
                try: thumb_url = info['thumbnails'][-1]['url']
                except: pass
            
            self.ultimo_url_verificado = url
            
            # Atualiza UI
            if not isinstance(thumb_url, str): thumb_url = ""
            self.after(0, lambda: self._atualizar_preview_ui(title, thumb_url))

        except Exception as e:
            print(f"Erro Metadados: {e}")
            self.after(0, lambda: self.lbl_status.configure(text=f"Link inválido.", text_color="red"))
            self.ultimo_url_verificado = "" # Permite tentar de novo

        finally:
            self.verificando_agora = False

    def _atualizar_preview_ui(self, title, thumb_url):
        self.frame_preview.configure(height=130)
        self.lbl_titulo.configure(text=title)
        self.lbl_info_extra.configure(text="Vídeo Único Detectado ✅")
        self.lbl_status.configure(text="Pronto para baixar", text_color=CORES["download_btn"])
        
        if thumb_url:
            try:
                response = requests.get(thumb_url, timeout=5)
                img_data = Image.open(BytesIO(response.content))
                w, h = 160, 90
                img_data = img_data.resize((w, h), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(w, h))
                self.lbl_thumb.configure(image=ctk_img, text="")
            except:
                self.lbl_thumb.configure(text="Sem Imagem")

    # --- DOWNLOAD CORE ---

    def _start_download_thread(self):
        if self.is_downloading: return
        url = self.entry_url.get().strip()
        if not url: return

        self.is_downloading = True
        self.btn_download.configure(state="disabled", text="INICIANDO...", fg_color=CORES["inativo"])
        self.lbl_status.configure(text="Preparando...", text_color="white")
        
        threading.Thread(target=self._run_download, args=(url,), daemon=True).start()

    def _run_download(self, url):
        qualidade = self.combo_qualidade.get()
        
        if not self.ffmpeg_path:
             self.after(0, lambda: self._finalizar_download(False, "FFmpeg não encontrado."))
             return

        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'progress_hooks': [self._update_ui_progress],
            # IMPORTANTE: Força vídeo único para evitar baixar playlists gigantes por acidente
            'noplaylist': True, 
            'ffmpeg_location': self.ffmpeg_path,
        }

        if qualidade == "MP3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}],
            })
        elif qualidade == "Melhor":
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        elif qualidade == "1080p":
             ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: self._finalizar_download(True, "Download Completo!"))
        except Exception as e:
            self.after(0, lambda: self._finalizar_download(False, str(e)))

    def _update_ui_progress(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%','')
            try: val = float(p) / 100
            except: val = 0
            txt = f"{d.get('_percent_str')} | {d.get('_eta_str', '00:00')}"
            self.after(0, lambda: self.progress_bar.set(val))
            self.after(0, lambda: self.lbl_status.configure(text=txt))

    def _finalizar_download(self, sucesso, msg):
        self.is_downloading = False
        self.btn_download.configure(state="normal", text="BAIXAR AGORA", fg_color=CORES["download_btn"])
        self.progress_bar.set(1 if sucesso else 0)
        self.lbl_status.configure(text=msg, text_color=CORES["download_btn"] if sucesso else "red")
        if not sucesso: messagebox.showerror("Erro", msg)
        else:
             self.entry_url.delete(0, 'end')
             self.frame_preview.configure(height=0)

    # --- GIF CONVERTER ---
    
    def _abrir_opcoes_gif(self):
        top = ctk.CTkToplevel(self)
        top.title("Config GIF")
        top.geometry("400x350")
        top.resizable(False, False)
        top.attributes("-topmost", True)

        ctk.CTkLabel(top, text="Ajustes Finos", font=("Arial", 16, "bold")).pack(pady=15)

        # FPS
        f1 = ctk.CTkFrame(top, fg_color="transparent")
        f1.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(f1, text="FPS:").pack(side="left")
        cmb_fps = ctk.CTkComboBox(f1, values=["10", "15", "20", "25", "30"], width=80)
        cmb_fps.set(str(self.gif_config["fps"]))
        cmb_fps.pack(side="right")

        # Largura
        f2 = ctk.CTkFrame(top, fg_color="transparent")
        f2.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(f2, text="Largura (PX):").pack(side="left")
        ent_width = ctk.CTkEntry(f2, width=80)
        ent_width.insert(0, str(self.gif_config["width"]))
        ent_width.pack(side="right")

        ctk.CTkFrame(top, height=2, fg_color="#444").pack(fill="x", padx=20, pady=10)

        # Corte
        ctk.CTkLabel(top, text="Recorte de Tempo", font=("Arial", 12, "bold")).pack()
        f3 = ctk.CTkFrame(top, fg_color="transparent")
        f3.pack(pady=5)
        
        ctk.CTkLabel(f3, text="Início (s):").grid(row=0, column=0, padx=5)
        sl_start = ctk.CTkSlider(f3, from_=0, to=60, number_of_steps=60, width=150)
        sl_start.set(self.gif_config["start"])
        sl_start.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(f3, text="Duração (s):").grid(row=1, column=0, padx=5, pady=10)
        sl_dur = ctk.CTkSlider(f3, from_=1, to=15, number_of_steps=14, width=150)
        sl_dur.set(self.gif_config["duration"])
        sl_dur.grid(row=1, column=1, padx=5, pady=10)

        def salvar():
            self.gif_config["fps"] = cmb_fps.get()
            self.gif_config["width"] = ent_width.get()
            self.gif_config["start"] = int(sl_start.get())
            self.gif_config["duration"] = int(sl_dur.get())
            top.destroy()
            messagebox.showinfo("Salvo", "Configurações aplicadas!")

        ctk.CTkButton(top, text="SALVAR", fg_color=CORES["download_btn"], command=salvar).pack(pady=20)

    def _selecionar_video_local(self):
        f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")])
        if f:
            self.video_gif_path = f
            self.lbl_arquivo_gif.configure(text=os.path.basename(f), text_color="white")

    def _thread_converter_gif(self):
        if not self.video_gif_path: return
        self.btn_converter_gif.configure(state="disabled", text="PROCESSANDO...")
        
        fps = self.gif_config["fps"]
        width = self.gif_config["width"]
        start = self.gif_config["start"]
        dur = self.gif_config["duration"]
        
        outfile = os.path.splitext(self.video_gif_path)[0] + f"_cut_{int(time.time())}.gif"
        
        cmd = [
            self.ffmpeg_path, "-ss", str(start), "-t", str(dur),
            "-i", self.video_gif_path,
            "-vf", f"fps={fps},scale={width}:-1:flags=lanczos",
            "-y", outfile
        ]
        
        def run():
            try:
                subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                self.after(0, lambda: messagebox.showinfo("Sucesso", f"GIF Salvo:\n{os.path.basename(outfile)}"))
                self.after(0, lambda: self.btn_converter_gif.configure(state="normal", text="CONVERTER PARA GIF"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))
                self.after(0, lambda: self.btn_converter_gif.configure(state="normal"))

        threading.Thread(target=run, daemon=True).start()

    # --- UTILS ---
    def _check_ffmpeg(self):
        local_ffmpeg = os.path.join(BASE_PATH, "ffmpeg", "bin", "ffmpeg.exe")
        if os.path.exists(local_ffmpeg): return local_ffmpeg
        local_ffmpeg_alt = os.path.join(BASE_PATH, "ffmpeg.exe")
        if os.path.exists(local_ffmpeg_alt): return local_ffmpeg_alt
        return shutil.which("ffmpeg")

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f: 
                    d = json.load(f)
                    self._selecionar_plataforma(d.get("platform", "YouTube"), CORES.get(d.get("platform", "youtube").lower(), CORES["youtube"]))
            except: pass
        else: self._selecionar_plataforma("YouTube", CORES["youtube"])

    def _selecionar_plataforma(self, nome, cor, hover=None):
        self.plataforma_atual = nome
        for k, v in self.plataforma_botoes.items():
            v.configure(fg_color=CORES["inativo"], text_color=CORES["texto_inativo"])
        self.plataforma_botoes[nome].configure(fg_color=cor, text_color="white")
        self.entry_url.configure(placeholder_text=f"Link do {nome}...")
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump({"platform": nome}, f)
        except: pass

    def _colar_area_transferencia(self):
        try: 
            self.entry_url.delete(0, 'end')
            self.entry_url.insert(0, self.clipboard_get())
            self._iniciar_verificacao_url()
        except: pass

    def _thread_atualizar_libs(self):
        threading.Thread(target=lambda: subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"]), daemon=True).start()

if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()