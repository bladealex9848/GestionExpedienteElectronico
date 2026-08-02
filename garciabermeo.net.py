"""Entrypoint garciabermeo.net: interfaz del despacho con navegacion a todas las herramientas."""

from __future__ import annotations

import importlib

import streamlit as st

from legal_ui.auth import init_auth
from legal_ui.auth_ui import ensure_authenticated
from legal_ui.app_logging import setup_logging
from legal_ui.brand import BRAND_NAME
from legal_ui.lexivox_theme import LEXIVOX_CSS
from legal_ui import page_registry

importlib.reload(page_registry)
from legal_ui.page_registry import APP_PAGES, TOOL_SECTIONS


def _page_title(label: str) -> str:
    parts = label.split(" ", 1)
    return parts[1] if len(parts) > 1 else label


def _build_navigation() -> dict[str, list[st.Page]]:
    sections: dict[str, list[st.Page]] = {
        BRAND_NAME: [
            st.Page(
                "pages/25_Gestion_Casos_Despacho.py",
                title="Gestión del Despacho",
                icon="⚖️",
                default=True,
            )
        ],
    }

    app_pages = [
        st.Page(path, title=_page_title(label))
        for label, path in APP_PAGES
        if "25_Gestion_Casos_Despacho" not in path
    ]
    if app_pages:
        sections["Aplicación"] = app_pages

    for section_name, pages in TOOL_SECTIONS:
        sections[section_name] = [
            st.Page(path, title=_page_title(label)) for label, path in pages
        ]

    return sections


st.set_page_config(
    page_title=f"{BRAND_NAME} | Gestión de Expedientes Judiciales",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(LEXIVOX_CSS, unsafe_allow_html=True)

setup_logging()
init_auth()
if not ensure_authenticated():
    st.stop()

pg = st.navigation(_build_navigation(), position="hidden")
pg.run()
