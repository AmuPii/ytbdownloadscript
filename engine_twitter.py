"""Compatibilidade: use ``core.DownloaderEngine`` em novos códigos."""
from core.legacy import download_legacy


def baixar(url, output_dir, hook_progresso, qualidade):
    return download_legacy(url, output_dir, hook_progresso, qualidade)
