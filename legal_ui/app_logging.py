"""Configuración centralizada de logging para depuración."""

from __future__ import annotations

import logging
import os
from pathlib import Path

_CONFIGURED = False
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.getenv("GARCIABERMEO_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "app.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
