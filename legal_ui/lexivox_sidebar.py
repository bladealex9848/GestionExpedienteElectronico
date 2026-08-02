from __future__ import annotations

import importlib

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from legal_ui.brand import BRAND_NAME
from legal_ui import page_registry

importlib.reload(page_registry)
from legal_ui.page_registry import APP_PAGES, TOOL_SECTIONS, page_exists
from legal_ui.auth_ui import render_user_badge

ILEY_PAGE = "pages/26_Consulta_Normativa_iLey_CO.py"


VISTAS = [
    ("dashboard", "📊 Dashboard"),
    ("casos", "📁 Casos"),
    ("clientes", "👥 Clientes"),
    ("tareas", "✅ Tareas"),
    ("calendario", "📅 Calendario"),
    ("facturacion", "💰 Facturación"),
    ("configuracion", "⚙️ Configuración"),
]


def _vista_labels() -> dict[str, str]:
    return dict(VISTAS)


def _multipage_ready() -> bool:
    ctx = get_script_run_ctx()
    if not ctx or not ctx.pages_manager:
        return False
    try:
        return len(ctx.pages_manager.get_pages()) > 1
    except Exception:
        return False


def _nav_to_page(page_path: str) -> None:
    if not page_exists(page_path):
        st.error(f"No se encontró la página: {page_path}")
        return
    st.switch_page(page_path)


def _render_nav_button(label: str, page_path: str, key: str) -> None:
    if st.button(label, key=key, use_container_width=True):
        _nav_to_page(page_path)


def render_lexivox_sidebar(vista_activa: str) -> str:
    labels = _vista_labels()
    keys = list(labels.keys())

    st.markdown(f'<div class="lx-brand">{BRAND_NAME}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lx-brand-sub">Gestión de expedientes judiciales</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Buscar",
        placeholder="Radicado, cliente, asunto...",
        label_visibility="collapsed",
        key="lexivox_buscar",
    )

    st.markdown('<div class="lx-nav-section">PRINCIPAL</div>', unsafe_allow_html=True)
    selected = st.radio(
        "Navegación principal",
        options=keys,
        index=keys.index(vista_activa) if vista_activa in keys else 0,
        format_func=lambda key: labels[key],
        key="lexivox_nav_radio",
        label_visibility="collapsed",
    )
    if selected != st.session_state.get("lexivox_vista"):
        st.session_state.lexivox_vista = selected
        st.rerun()

    st.markdown('<div class="lx-nav-section">ACCIONES RÁPIDAS</div>', unsafe_allow_html=True)
    quick_col1, quick_col2 = st.columns(2)
    with quick_col1:
        if st.button("➕ Caso", use_container_width=True, key="quick_new_case"):
            st.session_state.lexivox_vista = "casos"
            st.session_state.mostrar_formulario_caso = True
            st.rerun()
    with quick_col2:
        if st.button("➕ Cliente", use_container_width=True, key="quick_new_client"):
            st.session_state.lexivox_vista = "clientes"
            st.session_state.mostrar_formulario_cliente = True
            st.rerun()

    if st.button("📚 Consulta iLey CO", use_container_width=True, key="quick_iley"):
        _nav_to_page(ILEY_PAGE)

    if not _multipage_ready():
        st.caption("Use los botones para abrir herramientas del sistema.")

    st.markdown('<div class="lx-nav-section">APLICACIÓN</div>', unsafe_allow_html=True)
    for label, target in APP_PAGES:
        _render_nav_button(label, target, key=f"app_{target}")

    st.markdown('<div class="lx-nav-section">HERRAMIENTAS</div>', unsafe_allow_html=True)
    tool_options = {"— Seleccionar herramienta —": ""}
    for section_name, pages in TOOL_SECTIONS:
        for label, target in pages:
            tool_options[f"{label}"] = target

    picked = st.selectbox(
        "Ir a herramienta",
        options=list(tool_options.keys()),
        key="lexivox_tool_picker",
        label_visibility="collapsed",
    )
    picked_path = tool_options[picked]
    if picked_path and st.button("Abrir herramienta", key="open_tool_picker", use_container_width=True):
        _nav_to_page(picked_path)

    for section_name, pages in TOOL_SECTIONS:
        expanded = section_name == "Consulta normativa"
        with st.expander(section_name, expanded=expanded):
            for label, target in pages:
                _render_nav_button(label, target, key=f"tool_{target}")

    store = st.session_state.get("despacho_store", {})
    casos_recientes = store.get("casos", [])[:4]
    if casos_recientes:
        st.markdown('<div class="lx-nav-section">RECIENTES</div>', unsafe_allow_html=True)
        for case in casos_recientes:
            if st.button(
                case.get("nombre", "Caso")[:42],
                key=f"recent_{case['id']}",
                use_container_width=True,
            ):
                st.session_state.lexivox_vista = "casos"
                st.session_state.caso_seleccionado_id = case["id"]
                st.rerun()

    st.markdown(
        '<div class="lx-status-bar">Estado: Online · Core v3.0</div>',
        unsafe_allow_html=True,
    )
    render_user_badge()
    return query.strip().lower()
