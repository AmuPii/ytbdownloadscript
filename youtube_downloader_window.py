import customtkinter as ctk
import tkinter as tk 
from tkinter import messagebox
import os
import subprocess
import threading
import sys
import utils

# --- IMPORTAÇÃO DAS ENGINES ---
import engine_youtube
import engine_twitter
import engine_twitch
import engine_instagram
import engine_facebook
import engine_tiktok

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# === CORREÇÃO DE CAMINHO (PORTABILIDADE) ===
# Descobre onde o script/executável está rodando exatamente
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Define a pasta de downloads EXATAMENTE ao lado do script
DOWNLOAD_DIR = os.path.join(BASE_PATH, "downloads")

# Garante que a pasta existe agora
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_PATH = utils.get_ffmpeg_path()
PLATAFORMA_ATUAL = "YouTube" 

CORES = {
    "inativo": "#2B2B2B", "texto_inativo": "#AAAAAA",
    "youtube": "#FF0000", "facebook": "#1877F2", "instagram": "#E1306C",
    "twitter": "#000000", "twitch": "#9146FF", "tiktok": "#000000",
    "hover_tiktok": "#25F4EE", "download_btn": "#00C853", "folder_btn": "#2980B9", "fix_btn": "#E67E22"
}
def selecionar_plataforma(nome, cor_ativa, botao_ref, hover_cor=None):
    global PLATAFORMA_ATUAL
    PLATAFORMA_ATUAL = nome
    resetar_botoes()
    
    config = {
        "fg_color": cor_ativa, "text_color": "white",
        "border_width": 2 if cor_ativa == "#000000" else 0, 
        "border_color": "#444444" if cor_ativa == "#000000" else cor_ativa 
    }
    if hover_cor: config["hover_color"] = hover_cor
    botao_ref.configure(**config)
    
    # --- CORREÇÃO DE FOCO ---
    entry_url.delete(0, 'end') # Limpa qualquer link antigo
    entry_url.configure(placeholder_text=f"Cole seu link do {nome} aqui...")
    
    # Força o cursor a entrar na caixa de texto imediatamente
    app.after(50, lambda: entry_url.focus())

def atualizar_progresso_ui(dicionario_dados):
    if app:
        p_str = dicionario_dados.get('_percent_str', '0%').replace('%','')
        try: val_float = float(p_str) / 100
        except: val_float = 0
        texto_status = f"{dicionario_dados.get('_percent_str', '0%')} | {dicionario_dados.get('_speed_str', '')}"
        app.after(0, lambda: _set_ui(val_float, texto_status))

def _set_ui(val, txt):
    try: progress_bar.set(val); lbl_status.configure(text=txt)
    except: pass

def finalizar_download(sucesso, msg):
    if sucesso:
        progress_bar.set(1)
        lbl_status.configure(text="Concluído!", text_color=CORES["download_btn"])
        messagebox.showinfo("Sucesso", "Download finalizado!")
    else:
        progress_bar.set(0)
        lbl_status.configure(text="Erro", text_color="#FF5555")
        messagebox.showerror("Erro", msg)
    btn_download.configure(state="normal")
    entry_url.delete(0, 'end')

def thread_download():
    url = entry_url.get().strip()
    qualidade = combo_qualidade.get()
    
    if not url: return
    
    app.after(0, lambda: lbl_status.configure(text="Iniciando...", text_color="white"))
    
    try:
        class FakeHook:
            def __init__(self, callback): self.cb = callback
            def __call__(self, d): 
                if d['status'] == 'downloading': self.cb(d)
        
        logger_hook = FakeHook(atualizar_progresso_ui)

        # --- AQUI ESTÁ A CORREÇÃO PRINCIPAL ---
        # Enviamos apenas 4 argumentos, pois removemos o GIF das engines
        args = (url, DOWNLOAD_DIR, logger_hook, qualidade)

        if PLATAFORMA_ATUAL == "YouTube": engine_youtube.baixar(*args)
        elif PLATAFORMA_ATUAL == "TikTok": engine_tiktok.baixar(*args)
        elif PLATAFORMA_ATUAL == "Facebook": engine_facebook.baixar(*args)
        elif PLATAFORMA_ATUAL == "Instagram": engine_instagram.baixar(*args)
        elif PLATAFORMA_ATUAL == "Twitter": engine_twitter.baixar(*args)
        elif PLATAFORMA_ATUAL == "Twitch": engine_twitch.baixar(*args)
        
        app.after(0, lambda: finalizar_download(True, ""))
        
    except Exception as e:
        erro_msg = str(e)
        app.after(0, lambda: finalizar_download(False, erro_msg))

def iniciar_download():
    if not entry_url.get().strip(): return
    btn_download.configure(state="disabled")
    threading.Thread(target=thread_download).start()

def abrir_pasta():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    subprocess.Popen(f'explorer "{DOWNLOAD_DIR}"')

def resetar_botoes():
    btns = [btn_yt, btn_fb, btn_ig, btn_tw, btn_tch, btn_tt]
    for b in btns: b.configure(fg_color=CORES["inativo"], text_color=CORES["texto_inativo"], border_width=0)

def thread_atualizar_libs():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "gallery-dl", "requests"])
        messagebox.showinfo("Atualização", "Bibliotecas atualizadas com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao atualizar: {e}")

def iniciar_atualizacao():
    if messagebox.askyesno("Atualizar", "Deseja atualizar as dependências (yt-dlp)? Isso pode corrigir erros de download."):
        threading.Thread(target=thread_atualizar_libs).start()

# === UI ===
app = ctk.CTk()
app.title("Downloader do Herickão")
app.geometry("700x520") 
app.resizable(False, False)

# Header
frame_header = ctk.CTkFrame(app, fg_color="transparent")
frame_header.pack(pady=(15, 5), padx=20, fill="x")
ctk.CTkLabel(frame_header, text="Downloader do Herickão", font=("Roboto Black", 24)).pack(side="left")
ctk.CTkButton(frame_header, text="🛠 Fix / Atualizar", width=110, fg_color=CORES["fix_btn"], command=iniciar_atualizacao).pack(side="right")

# Plataformas
frame_plat = ctk.CTkFrame(app, fg_color="transparent")
frame_plat.pack(pady=10, padx=10, fill="x")
BTN_H, BTN_FONT = 50, ("Arial", 14, "bold")
btn_yt = ctk.CTkButton(frame_plat, text="YOUTUBE", height=BTN_H, font=BTN_FONT, command=lambda: selecionar_plataforma("YouTube", CORES["youtube"], btn_yt)); btn_yt.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
btn_fb = ctk.CTkButton(frame_plat, text="FACEBOOK", height=BTN_H, font=BTN_FONT, command=lambda: selecionar_plataforma("Facebook", CORES["facebook"], btn_fb)); btn_fb.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
btn_ig = ctk.CTkButton(frame_plat, text="INSTAGRAM", height=BTN_H, font=BTN_FONT, command=lambda: selecionar_plataforma("Instagram", CORES["instagram"], btn_ig)); btn_ig.grid(row=0, column=2, sticky="ew", padx=2, pady=2)
btn_tw = ctk.CTkButton(frame_plat, text="TWITTER / X", height=BTN_H, font=BTN_FONT, command=lambda: selecionar_plataforma("Twitter", CORES["twitter"], btn_tw)); btn_tw.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
btn_tch = ctk.CTkButton(frame_plat, text="TWITCH", height=BTN_H, font=BTN_FONT, command=lambda: selecionar_plataforma("Twitch", CORES["twitch"], btn_tch)); btn_tch.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
btn_tt = ctk.CTkButton(frame_plat, text="TIKTOK", height=BTN_H, font=BTN_FONT, command=lambda: selecionar_plataforma("TikTok", CORES["tiktok"], btn_tt, CORES["hover_tiktok"])); btn_tt.grid(row=1, column=2, sticky="ew", padx=2, pady=2)
frame_plat.grid_columnconfigure((0,1,2), weight=1)

# Input
entry_url = ctk.CTkEntry(app, height=50, placeholder_text="Selecione a plataforma e cole o link...", font=("Arial", 14))
entry_url.pack(pady=(10, 5), padx=20, fill="x")
entry_url.bind("<Button-1>", lambda event: entry_url.focus())

# --- OPÇÕES ---
frame_opcoes = ctk.CTkFrame(app, fg_color="transparent")
frame_opcoes.pack(pady=5)

ctk.CTkLabel(frame_opcoes, text="Qualidade:", font=("Arial", 12)).pack(side="left", padx=5)
combo_qualidade = ctk.CTkComboBox(frame_opcoes, values=["Melhor", "1080p", "720p", "MP3"], width=130, height=30)
combo_qualidade.pack(side="left", padx=(0, 20))

# Progresso e Botões de Ação
lbl_status = ctk.CTkLabel(app, text="Aguardando...", text_color="gray")
lbl_status.pack(pady=(10, 0))
progress_bar = ctk.CTkProgressBar(app, height=15, progress_color=CORES["download_btn"]); progress_bar.set(0); progress_bar.pack(pady=5, padx=20, fill="x")
frame_actions = ctk.CTkFrame(app, fg_color="transparent"); frame_actions.pack(pady=20, padx=20, fill="x"); frame_actions.grid_columnconfigure((0,1), weight=1)
btn_download = ctk.CTkButton(frame_actions, text="BAIXAR AGORA", height=60, font=("Arial", 16, "bold"), fg_color=CORES["download_btn"], corner_radius=10, command=iniciar_download); btn_download.grid(row=0, column=0, padx=5, sticky="ew")
btn_folder = ctk.CTkButton(frame_actions, text="ABRIR PASTA", height=60, font=("Arial", 16, "bold"), fg_color=CORES["folder_btn"], corner_radius=10, command=abrir_pasta); btn_folder.grid(row=0, column=1, padx=5, sticky="ew")

resetar_botoes()
selecionar_plataforma("YouTube", CORES["youtube"], btn_yt)
app.mainloop()