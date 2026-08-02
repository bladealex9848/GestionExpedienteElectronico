from __future__ import annotations

import streamlit as st

from legal_ui.case_context import activate_case
from legal_ui.despacho_store import client_name
from legal_ui.expediente_store import (
    delete_document,
    delete_result,
    read_document_bytes,
    read_result_bytes,
    save_document,
)
from legal_ui.page_registry import TOOL_SECTIONS

CASE_TOOLS = [
    ("📚 Consulta iLey CO", "pages/26_Consulta_Normativa_iLey_CO.py"),
    ("📚 Organizador Vigilancia", "pages/24_Organizador_Automatico_Vigilancia.py"),
    ("🧠 Panel Integral", "pages/13_Panel_Integral_Expediente.py"),
    ("📋 Preparador Vigilancia", "pages/16_Preparador_Vigilancia_Judicial.py"),
    ("📅 Control de Términos", "pages/14_Control_Terminos.py"),
    ("⚖️ Auditor Jurídico V2", "pages/6_Auditor_Juridico_V2.py"),
]


def render_expediente_tab(case: dict, store: dict, persist) -> None:
    st.markdown("#### Expediente del caso")
    st.caption("Documentos, resultados de herramientas y acceso directo con contexto del caso.")

    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        despacho = st.text_input("Despacho judicial", value=case.get("despacho", ""), key=f"exp_despacho_{case['id']}")
        tipo_proceso = st.text_input(
            "Tipo de proceso",
            value=case.get("tipo_proceso", "") or "Vigilancia Judicial Administrativa",
            key=f"exp_tipo_{case['id']}",
        )
    with meta_col2:
        partes = st.text_area("Partes / solicitante", value=case.get("partes", ""), height=88, key=f"exp_partes_{case['id']}")
        if st.button("Guardar metadatos del expediente", key=f"save_exp_meta_{case['id']}"):
            case["despacho"] = despacho.strip()
            case["tipo_proceso"] = tipo_proceso.strip()
            case["partes"] = partes.strip()
            if not case["partes"]:
                case["partes"] = client_name(store, case.get("cliente_id", ""))
            persist()
            st.success("Metadatos del expediente actualizados.")

    st.markdown("##### Documentos del expediente")
    uploaded = st.file_uploader(
        "Subir documentos al caso",
        type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml", "xlsx"],
        accept_multiple_files=True,
        key=f"exp_upload_{case['id']}",
    )
    cat_col, up_col = st.columns([2, 1])
    with cat_col:
        categoria = st.text_input(
            "Categoría (opcional)",
            placeholder="Ej: Fallo, Memorial, Constancia",
            key=f"exp_cat_{case['id']}",
        )
    with up_col:
        st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
        if uploaded and st.button("Agregar al expediente", key=f"exp_add_{case['id']}", use_container_width=True):
            for file in uploaded:
                save_document(case, file.name, file.getvalue(), categoria=categoria)
            persist()
            st.success(f"Se agregaron {len(uploaded)} documento(s).")
            st.rerun()

    documentos = case.get("documentos", [])
    if documentos:
        for doc in documentos:
            dcol1, dcol2, dcol3, dcol4 = st.columns([3, 1.2, 1.2, 0.7])
            dcol1.write(f"**{doc.get('nombre', '')}**")
            dcol2.write(doc.get("categoria") or doc.get("tipo", ""))
            dcol3.write(f"{doc.get('tamano', 0) / 1024:.1f} KB")
            try:
                data = read_document_bytes(case["id"], doc)
                dcol4.download_button("⬇", data=data, file_name=doc.get("nombre", "doc"), key=f"dl_doc_{doc['id']}")
            except OSError:
                dcol4.caption("—")
            if st.button("🗑", key=f"rm_doc_{case['id']}_{doc['id']}"):
                delete_document(case, doc["id"])
                persist()
                st.rerun()
    else:
        st.info("Aún no hay documentos en este expediente.")

    st.markdown("##### Resultados guardados")
    resultados = case.get("resultados", [])
    if resultados:
        for row in reversed(resultados):
            rcol1, rcol2, rcol3, rcol4 = st.columns([2.5, 1.5, 1.2, 0.7])
            rcol1.write(f"**{row.get('titulo', '')}**")
            rcol2.write(row.get("herramienta", ""))
            rcol3.write(str(row.get("fecha", ""))[:10])
            try:
                data = read_result_bytes(case["id"], row)
                rcol4.download_button("⬇", data=data, file_name=row.get("archivo", "resultado"), key=f"dl_res_{row['id']}")
            except OSError:
                rcol4.caption("—")
            if row.get("notas"):
                st.caption(row["notas"])
    else:
        st.info("Los informes y paquetes generados en herramientas pueden guardarse aquí.")

    st.markdown("##### Abrir herramientas con este caso")
    st.caption("Se prellenarán radicado, despacho, cliente y documentos del expediente.")
    tool_cols = st.columns(2)
    for index, (label, path) in enumerate(CASE_TOOLS):
        with tool_cols[index % 2]:
            if st.button(label, key=f"open_tool_{case['id']}_{path}", use_container_width=True):
                activate_case(store, case["id"])
                st.session_state.lexivox_vista = "casos"
                st.session_state.caso_seleccionado_id = case["id"]
                st.switch_page(path)

    with st.expander("Todas las herramientas", expanded=False):
        for section_name, pages in TOOL_SECTIONS:
            st.markdown(f"**{section_name}**")
            for label, path in pages:
                if st.button(label, key=f"open_all_{case['id']}_{path}", use_container_width=True):
                    activate_case(store, case["id"])
                    st.switch_page(path)
