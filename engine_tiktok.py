import requests
import os
import time
import re
import utils 
import subprocess

def limpar_nome_arquivo(nome):
    return re.sub(r'[<>:"/\\|?*]', '', nome).strip()

def baixar(url, output_dir, hook_progresso, escolha_formato, gerar_gif_extra=False):
    
    # Prevenção de erros de variável não definida
    link_download = None
    caminho_completo = None
    
    pasta_saida = os.path.join(output_dir, "TikTok")
    os.makedirs(pasta_saida, exist_ok=True)

    # === 1. BUSCAR O VÍDEO (API) ===
    try:
        hook_progresso({'status': 'downloading', '_percent_str': '0%', '_speed_str': 'Conectando à API...'})
        
        api_url = "https://www.tikwm.com/api/"
        payload = {"url": url, "count": 12, "cursor": 0, "web": 1, "hd": 1}
        
        resp = requests.post(api_url, data=payload)
        resp_json = resp.json()

        if resp_json.get("code") != 0:
            raise Exception("Vídeo não encontrado ou link inválido.")

        dados = resp_json.get("data", {})
        
        # Tenta pegar HD, senão pega normal
        link_temp = dados.get("hdplay") or dados.get("play")
        
        if not link_temp:
            raise Exception("A API não retornou nenhum link de vídeo.")

        # --- CORREÇÃO DO ERRO "INVALID URL" ---
        # Se o link vier relativo (começa com /), adicionamos o domínio na frente
        if link_temp.startswith("/"):
            link_download = "https://www.tikwm.com" + link_temp
        else:
            link_download = link_temp

        # Define nomes
        titulo = dados.get("title", "tiktok_video")
        video_id = dados.get("id", str(int(time.time())))
        nome_arquivo = f"{limpar_nome_arquivo(titulo)[:50]} [{video_id}].mp4"
        caminho_completo = os.path.join(pasta_saida, nome_arquivo)

    except Exception as e:
        raise Exception(f"Erro ao processar link: {e}")

    # === 2. BAIXAR O VÍDEO ===
    try:
        if not link_download:
             raise Exception("Link de download vazio.")

        print(f"Baixando de: {link_download}")
        
        with requests.get(link_download, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            baixado = 0
            
            with open(caminho_completo, 'wb') as f:
                start = time.time()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        baixado += len(chunk)
                        if total > 0:
                            percent = (baixado / total) * 100
                            hook_progresso({
                                'status': 'downloading',
                                'downloaded_bytes': baixado,
                                'total_bytes': total,
                                '_percent_str': f"{percent:.1f}%",
                                '_speed_str': "Baixando..."
                            })

    except Exception as e:
        # Se der erro no download, limpamos o arquivo corrompido
        if caminho_completo and os.path.exists(caminho_completo):
            os.remove(caminho_completo)
        raise Exception(f"Erro de conexão/download: {e}")

    # === 3. CONVERSÃO (GIF/MP3) ===
    # Só executa se o arquivo existir
    if caminho_completo and os.path.exists(caminho_completo):
        
        if escolha_formato == "MP3":
            try:
                hook_progresso({'status': 'downloading', '_percent_str': '100%', '_speed_str': 'Gerando MP3...'})
                mp3 = caminho_completo.replace(".mp4", ".mp3")
                ffmpeg = utils.get_ffmpeg_path()
                subprocess.run([ffmpeg, "-y", "-i", caminho_completo, "-q:a", "0", "-map", "a", mp3],
                               creationflags=0x08000000 if os.name=='nt' else 0, check=True)
                if os.path.exists(mp3): os.remove(caminho_completo)
            except: pass

        elif gerar_gif_extra and escolha_formato != "MP3":
            try:
                hook_progresso({'status': 'downloading', '_percent_str': '100%', '_speed_str': 'Gerando GIF...'})
                webm = caminho_completo.replace(".mp4", ".webm")
                utils.converter_para_webm_discord(caminho_completo, webm, manter_original=True)
            except: pass

    return True