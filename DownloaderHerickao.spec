# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks.tcl_tk import tcltk_info

project_root = Path(SPECPATH)
yt_dlp_data, yt_dlp_binaries, yt_dlp_imports = collect_all("yt_dlp")
ctk_data, ctk_binaries, ctk_imports = collect_all("customtkinter")

datas = [(str(project_root / "ffmpeg"), "ffmpeg"), *yt_dlp_data, *ctk_data]
binaries = [*yt_dlp_binaries, *ctk_binaries]
hiddenimports = ["_tkinter", *yt_dlp_imports, *ctk_imports]

for shared_library in (
    tcltk_info.tcl_shared_library,
    tcltk_info.tk_shared_library,
):
    if shared_library:
        binaries.append((shared_library, "."))


a = Analysis(
    [str(project_root / "youtube_downloader_window.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DownloaderHerickao',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
