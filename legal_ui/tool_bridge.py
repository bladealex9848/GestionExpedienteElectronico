from __future__ import annotations

import streamlit as st

from legal_ui.case_context import (
    LOADED_FILES_KEY,
    get_active_case_id,
    get_tool_context,
    load_case_upload_files,
)
from legal_ui.despacho_store import find_case, load_store, save_store
from legal_ui.expediente_store import save_result
from legal_ui.brand import BRAND_NAME
from legal_ui.terminos_sync import sync_terms_batch


LEXIVOX_PAGE = "pages/25_Gestion_Casos_Despacho.py"


def render_active_case_banner(*, show_load_button: bool = True) -> dict | None:
    ctx = get_tool_context()
    if not ctx:
        return None

    st.markdown(
        f"""
        <div style="padding:0.75rem 1rem;border-radius:10px;background:rgba(59,130,246,0.12);
        border:1px solid rgba(59,130,246,0.35);margin-bottom:1rem;">
        <b>📎 Caso activo ({BRAND_NAME}):</b> {ctx.get("caso_nombre", "")}<br>
        <span style="opacity:0.85">Radicado: {ctx.get("radicado") or "—"} · Despacho: {ctx.get("despacho") or "—"}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_back, col_load, col_info = st.columns([1.1, 1.2, 1.7])
    if col_back.button(f"← Volver a {BRAND_NAME}", use_container_width=True, key="bridge_back_lexivox"):
        st.switch_page(LEXIVOX_PAGE)
    if show_load_button and col_load.button(
        "Cargar documentos del caso",
        use_container_width=True,
        key="bridge_load_case_docs",
    ):
        store = _get_store()
        files = load_case_upload_files(store, ctx["caso_id"])
        st.session_state[LOADED_FILES_KEY] = files
        st.session_state["lexivox_docs_loaded_count"] = len(files)
        st.rerun()

    loaded = st.session_state.get("lexivox_docs_loaded_count", 0)
    if loaded:
        col_info.caption(f"{loaded} documento(s) del caso listos para usar.")
    return ctx


def merge_loaded_files(uploaded_files, tool_session_key: str):
    """Combina archivos subidos con los cargados desde el despacho."""
    loaded = st.session_state.get(LOADED_FILES_KEY) or []
    if not uploaded_files and loaded:
        st.session_state[tool_session_key] = loaded
        return loaded
    if uploaded_files:
        st.session_state[tool_session_key] = uploaded_files
        return uploaded_files
    return st.session_state.get(tool_session_key)


def save_output_to_case(
    herramienta: str,
    titulo: str,
    filename: str,
    content: bytes,
    notas: str = "",
) -> bool:
    ctx = get_tool_context()
    if not ctx:
        st.warning(f"No hay un caso activo en {BRAND_NAME}.")
        return False
    store = _get_store()
    case = find_case(store, ctx["caso_id"])
    if not case:
        st.error("No se encontró el caso activo.")
        return False
    save_result(case, herramienta, titulo, filename, content, notas=notas)
    save_store(store)
    if "despacho_store" in st.session_state:
        st.session_state.despacho_store = store
    st.success(f"Resultado guardado en el caso «{ctx.get('caso_nombre', '')}».")
    return True


def render_save_result_button(
    herramienta: str,
    titulo: str,
    filename: str,
    content: bytes,
    *,
    key: str,
    notas: str = "",
) -> None:
    ctx = get_tool_context()
    if not ctx:
        return
    if st.button(f"💾 Guardar en caso ({BRAND_NAME})", key=key, use_container_width=True):
        save_output_to_case(herramienta, titulo, filename, content, notas=notas)


def _get_store() -> dict:
    if "despacho_store" in st.session_state:
        return st.session_state.despacho_store
    store = load_store()
    st.session_state.despacho_store = store
    return store


def sync_store_from_session() -> None:
    """Persist session store if modified by tools."""
    if "despacho_store" in st.session_state:
        save_store(st.session_state.despacho_store)


def render_sync_terms_to_lexivox(
    rows: list[dict],
    *,
    source: str,
    key: str,
    label: str | None = None,
) -> None:
    if label is None:
        label = f"📅 Sincronizar términos con {BRAND_NAME}"
    ctx = get_tool_context()
    if not ctx:
        st.caption(
            f"Abre esta herramienta desde un caso en {BRAND_NAME} "
            "para crear tareas y eventos automáticamente."
        )
        return
    if not rows:
        st.caption("No hay términos para sincronizar.")
        return
    st.markdown(
        f"Se crearán **tareas** y **eventos** en el caso «{ctx.get('caso_nombre', '')}»."
    )
    if st.button(label, key=key, type="primary", use_container_width=True):
        store = _get_store()
        stats = sync_terms_batch(store, ctx["caso_id"], rows, source)
        save_store(store)
        st.session_state.despacho_store = store
        st.success(
            f"Sincronización completa: {stats['created']} nuevo(s), "
            f"{stats['duplicates']} duplicado(s) omitido(s), "
            f"{stats['skipped']} no aplicable(s)."
        )
        st.rerun()
