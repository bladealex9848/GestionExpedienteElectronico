from __future__ import annotations

import streamlit as st

from legal_ui.despacho_store import find_case, find_client
from legal_ui.expediente_store import read_document_bytes

ACTIVE_CASE_KEY = "lexivox_active_case_id"
TOOL_CONTEXT_KEY = "lexivox_tool_context"
LOADED_FILES_KEY = "lexivox_loaded_files"
PREFILL_CASE_KEY = "_lexivox_prefill_case_id"


class CaseUploadFile:
    """Wrapper compatible con file_uploader (.name, .getvalue())."""

    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data

    def read(self) -> bytes:
        return self._data


def build_tool_context(store: dict, case_id: str) -> dict | None:
    case = find_case(store, case_id)
    if not case:
        return None
    client = find_client(store, case.get("cliente_id", "")) or {}
    return {
        "caso_id": case_id,
        "caso_nombre": case.get("nombre", ""),
        "radicado": case.get("radicado", ""),
        "despacho": case.get("despacho", ""),
        "solicitante": client.get("nombre", ""),
        "tipo_proceso": case.get("tipo_proceso", "") or "Vigilancia Judicial Administrativa",
        "partes": case.get("partes", ""),
        "cliente_documento": client.get("documento", ""),
        "cliente_email": client.get("email", ""),
        "cliente_telefono": client.get("telefono", ""),
    }


def activate_case(store: dict, case_id: str) -> dict | None:
    ctx = build_tool_context(store, case_id)
    if not ctx:
        return None
    st.session_state[ACTIVE_CASE_KEY] = case_id
    st.session_state[TOOL_CONTEXT_KEY] = ctx
    st.session_state[PREFILL_CASE_KEY] = None
    return ctx


def get_tool_context() -> dict | None:
    return st.session_state.get(TOOL_CONTEXT_KEY)


def get_active_case_id() -> str:
    return st.session_state.get(ACTIVE_CASE_KEY, "")


def load_case_upload_files(store: dict, case_id: str | None = None) -> list[CaseUploadFile]:
    case_id = case_id or get_active_case_id()
    case = find_case(store, case_id) if case_id else None
    if not case:
        return []
    files: list[CaseUploadFile] = []
    for doc in case.get("documentos", []):
        try:
            data = read_document_bytes(case_id, doc)
            files.append(CaseUploadFile(doc.get("nombre", doc.get("archivo", "doc")), data))
        except OSError:
            continue
    return files


def apply_prefill(field_map: dict[str, str]) -> None:
    ctx = get_tool_context()
    if not ctx:
        return
    case_id = ctx["caso_id"]
    if st.session_state.get(PREFILL_CASE_KEY) == case_id:
        return
    for session_key, context_key in field_map.items():
        value = ctx.get(context_key, "")
        if value:
            st.session_state[session_key] = value
    st.session_state[PREFILL_CASE_KEY] = case_id


def prefill_value(context_key: str, default: str = "") -> str:
    ctx = get_tool_context()
    if ctx and ctx.get(context_key):
        return str(ctx[context_key])
    return default
