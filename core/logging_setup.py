from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .utils import get_app_base


def configure_logging() -> None:
    root = logging.getLogger()
    log_path = get_app_base() / "app.log"
    if any(getattr(handler, "baseFilename", None) == str(log_path) for handler in root.handlers):
        return
    try:
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root.setLevel(logging.INFO)
        root.addHandler(handler)
    except OSError:
        # Um diretório de instalação protegido não deve impedir a abertura da UI.
        logging.basicConfig(level=logging.INFO)
