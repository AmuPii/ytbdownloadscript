"""Compatibilidade: use ``core.DownloaderEngine`` em novos códigos.

O parâmetro ``gerar_gif_extra`` foi descontinuado: o conversor de GIF da
interface substitui a antiga chamada a uma função inexistente.
"""
from core.legacy import download_legacy


def baixar(url, output_dir, hook_progresso, escolha_formato, gerar_gif_extra=False):
    return download_legacy(url, output_dir, hook_progresso, escolha_formato)
