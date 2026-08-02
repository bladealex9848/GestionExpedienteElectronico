"""Comprobación de dependencias del sistema (Tesseract, Poppler)."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from legal_ui.app_logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    available: bool
    detail: str


def check_tesseract() -> DependencyStatus:
    try:
        import pytesseract

        version = pytesseract.get_tesseract_version()
        return DependencyStatus("Tesseract OCR", True, str(version))
    except Exception as exc:
        logger.warning("Tesseract no disponible: %s", exc)
        return DependencyStatus(
            "Tesseract OCR",
            False,
            f"{exc}. Instale Tesseract y asegure que esté en PATH "
            "(Windows: https://github.com/UB-Mannheim/tesseract/wiki).",
        )


def check_poppler() -> DependencyStatus:
    poppler_path = os.getenv("POPPLER_PATH", "").strip()
    if poppler_path:
        bin_dir = Path(poppler_path)
        if bin_dir.is_dir() and any(bin_dir.glob("pdftoppm*")):
            return DependencyStatus("Poppler", True, f"POPPLER_PATH={poppler_path}")

    for command in ("pdftoppm", "pdfinfo"):
        resolved = shutil.which(command)
        if resolved:
            return DependencyStatus("Poppler", True, resolved)

    return DependencyStatus(
        "Poppler",
        False,
        "No se encontró pdftoppm/pdfinfo. Linux: sudo apt install poppler-utils. "
        "Streamlit Cloud: use packages.txt. Windows: descargue Poppler y defina POPPLER_PATH.",
    )


def check_ocr_dependencies() -> list[DependencyStatus]:
    return [check_tesseract(), check_poppler()]


def ocr_dependencies_ready() -> bool:
    return all(item.available for item in check_ocr_dependencies())


def render_ocr_dependencies_status(*, stop_if_missing: bool = False) -> bool:
    """Muestra estado en Streamlit. Devuelve True si todo está listo."""
    import streamlit as st

    statuses = check_ocr_dependencies()
    ready = all(item.available for item in statuses)
    if ready:
        details = " · ".join(f"{item.name}: {item.detail}" for item in statuses)
        st.caption(f"Dependencias OCR: {details}")
        return True

    st.warning(
        "Esta herramienta requiere **Tesseract OCR** y **Poppler** instalados en el sistema. "
        "Sin ellos, el OCR de PDF escaneados fallará."
    )
    for item in statuses:
        if item.available:
            st.success(f"{item.name}: {item.detail}")
        else:
            st.error(f"{item.name}: {item.detail}")

    if stop_if_missing:
        st.info(
            "Consulte `packages.txt` (Linux/Cloud) o configure POPPLER_PATH y Tesseract en Windows."
        )
        st.stop()
    return False
