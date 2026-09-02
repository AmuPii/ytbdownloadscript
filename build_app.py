from __future__ import annotations

import os
import sys
from pathlib import Path

if os.name != "nt":
    raise SystemExit("\nERRO: o executável deve ser compilado no Windows.\n")
if sys.version_info < (3, 10):
    raise SystemExit("\nERRO: use Python 3.10 ou mais recente.\n")

try:
    import _tkinter
    import tkinter
except (ImportError, ModuleNotFoundError) as exc:
    raise SystemExit(
        "\nERRO: esta instalação do Python não possui um Tcl/Tk funcional. "
        "Reinstale o Python oficial marcando a opção 'tcl/tk and IDLE'. "
        f"Detalhes: {exc}\n"
    ) from exc

try:
    import customtkinter  # noqa: F401
    import PyInstaller.__main__
    import yt_dlp  # noqa: F401
    from PIL import Image  # noqa: F401
    from PyInstaller.utils.hooks.tcl_tk import tcltk_info
except (ImportError, ModuleNotFoundError) as exc:
    raise SystemExit(
        "\nERRO: faltam dependências de build. Execute "
        '".\\.venv\\Scripts\\python.exe -m pip install -e \".[build]\"". '
        f"Detalhes: {exc}\n"
    ) from exc

PROJECT_ROOT = Path(__file__).resolve().parent
SPEC_FILE = PROJECT_ROOT / "DownloaderHerickao.spec"
FFMPEG_DIR = PROJECT_ROOT / "ffmpeg" / "bin"


def fail(message: str) -> None:
    raise SystemExit(f"\nERRO: {message}\n")


def validate_environment() -> None:
    try:
        interpreter = tkinter.Tcl()
        interpreter.eval("info patchlevel")
    except tkinter.TclError as exc:
        fail(f"o Tcl/Tk desta instalação do Python não pôde ser iniciado: {exc}")

    if not tcltk_info.available:
        fail("o PyInstaller não conseguiu localizar a instalação do Tcl/Tk.")

    required_tk_files = (
        _tkinter.__file__,
        tcltk_info.tcl_shared_library,
        tcltk_info.tk_shared_library,
        tcltk_info.tcl_data_dir,
        tcltk_info.tk_data_dir,
    )
    missing_tk_files = [
        str(path) if path else "<caminho não encontrado>"
        for path in required_tk_files
        if not path or not Path(path).exists()
    ]
    if missing_tk_files:
        fail(
            "a instalação do Tcl/Tk está incompleta: "
            + ", ".join(missing_tk_files)
        )

    missing_ffmpeg_files = [
        FFMPEG_DIR / filename
        for filename in ("ffmpeg.exe", "ffprobe.exe")
        if not (FFMPEG_DIR / filename).is_file()
    ]
    if missing_ffmpeg_files:
        fail(
            "a pasta ffmpeg/bin está incompleta: "
            + ", ".join(str(path) for path in missing_ffmpeg_files)
        )

    dll_directory = Path(_tkinter.__file__).resolve().parent
    os.environ["PATH"] = os.pathsep.join(
        (str(dll_directory), str(Path(sys.base_prefix)), os.environ.get("PATH", ""))
    )


def main() -> None:
    validate_environment()

    os.chdir(PROJECT_ROOT)
    print(f">>> Python: {sys.executable}")
    print(">>> Iniciando a compilação do DownloaderHerickao.exe...")

    PyInstaller.__main__.run(
        [
            "--clean",
            "--noconfirm",
            f"--distpath={PROJECT_ROOT / 'dist'}",
            f"--workpath={PROJECT_ROOT / 'build'}",
            str(SPEC_FILE),
        ]
    )

    executable = PROJECT_ROOT / "dist" / "DownloaderHerickao.exe"
    if not executable.is_file():
        fail("o PyInstaller terminou sem criar dist/DownloaderHerickao.exe.")

    print(f"\n>>> SUCESSO: {executable}")
    print(">>> O FFmpeg e as bibliotecas Tcl/Tk foram incluídos no executável.")


if __name__ == "__main__":
    main()
