from __future__ import annotations

import hashlib
import io

import pandas as pd
import streamlit as st

from legal_analyzer.case_extractor import (
    build_timeline,
    classify_document,
    extract_case_metadata,
)
from legal_analyzer.command_center import detect_contradictions
from legal_analyzer.document_loader import load_document
from legal_analyzer.evidence_radar import (
    evidence_inventory,
    extract_entities,
    extract_relations,
    missing_evidence_actions,
    theory_of_case,
)
from legal_analyzer.models import PageTrace
from legal_analyzer.ocr_engine import OCRConfig, quality_label
from legal_analyzer.petition_comparator import (
    compare_requests_with_answers,
    extract_requests,
)
from legal_analyzer.question_engine import (
    answer_question,
    build_fragment_index,
    suggested_questions,
)
from legal_analyzer.semaphore_engine import (
    build_semaphores,
    overall_semaphore,
)

from legal_ui.case_context import LOADED_FILES_KEY
from legal_ui.tool_bridge import render_active_case_banner


st.set_page_config(
    page_title="Panel Integral del Expediente",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Panel Integral del Expediente")
st.caption(
    "Carga el expediente una sola vez y revisa todo desde un mismo lugar."
)


def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@st.cache_data(show_spinner=False, max_entries=80)
def cached_load(
    name: str,
    content_hash: str,
    content: bytes,
    enabled: bool,
    min_chars: int,
    max_pages: int,
    dpi: int,
) -> list[dict]:
    del content_hash

    config = OCRConfig(
        enabled=enabled,
        min_useful_characters=min_chars,
        max_ocr_pages=max_pages,
        dpi=dpi,
    )

    return [
        item.to_dict()
        for item in load_document(name, content, config)
    ]


def restore(data: dict) -> PageTrace:
    return PageTrace(**data)


def semaforo_icon(color: str) -> str:
    return {
        "Verde": "🟢",
        "Amarillo": "🟡",
        "Rojo": "🔴",
    }.get(color, "⚪")


with st.sidebar:
    st.header("Configuración")

    ocr_enabled = st.checkbox(
        "Aplicar OCR",
        value=True,
    )

    min_chars = st.slider(
        "Mínimo de caracteres útiles",
        20,
        300,
        80,
        10,
    )

    max_pages = st.slider(
        "Máximo de páginas OCR",
        5,
        100,
        40,
        5,
    )

    dpi = st.select_slider(
        "Resolución OCR",
        [150, 200, 220, 250, 300],
        value=220,
    )


render_active_case_banner()

files = st.file_uploader(
    "Sube todas las piezas del expediente",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
    accept_multiple_files=True,
)

if not files:
    files = st.session_state.get(LOADED_FILES_KEY)

if not files:
    st.info(
        "Carga el expediente una sola vez. Después podrás revisar datos, "
        "cronología, semáforos, contradicciones, pruebas y preguntas."
    )
    st.stop()


documents: dict[str, list[PageTrace]] = {}
progress = st.progress(0)
status = st.empty()

for index, uploaded in enumerate(files):
    status.info(f"Procesando {uploaded.name}")
    content = uploaded.getvalue()

    try:
        raw = cached_load(
            uploaded.name,
            file_hash(content),
            content,
            ocr_enabled,
            min_chars,
            max_pages,
            dpi,
        )
        documents[uploaded.name] = [
            restore(item)
            for item in raw
        ]
    except Exception as error:
        st.error(
            f"No se pudo procesar {uploaded.name}: {error}"
        )
        documents[uploaded.name] = []

    progress.progress((index + 1) / len(files))

status.empty()


quality_rows = []

for name, pages in documents.items():
    kind, _ = classify_document(pages)

    for page in pages:
        quality_rows.append(
            {
                "Documento": name,
                "Tipo": kind,
                "Página": page.page,
                "Método": page.extraction_method,
                "Confianza OCR": page.ocr_confidence,
                "Caracteres útiles": page.useful_characters,
                "Calidad": quality_label(page),
                "Advertencias": " | ".join(page.warnings),
                "Vista previa": page.text[:400],
            }
        )


metadata = extract_case_metadata(documents)
timeline = pd.DataFrame(build_timeline(documents))
quality_df = pd.DataFrame(quality_rows)

if not timeline.empty:
    timeline["_orden"] = pd.to_datetime(
        timeline["Fecha principal"],
        errors="coerce",
    )
    timeline = timeline.sort_values(
        ["_orden", "Documento"],
        na_position="last",
    ).drop(columns="_orden")


semaphore_items = build_semaphores(
    documents,
    quality_rows,
)
overall = overall_semaphore(
    semaphore_items
)

contradictions = pd.DataFrame(
    detect_contradictions(documents)
)

evidence = evidence_inventory(documents)
entities = extract_entities(documents)
relations = extract_relations(documents, entities)
missing_actions = missing_evidence_actions(evidence)
case_theory = theory_of_case(metadata, evidence, relations)

fragment_index = build_fragment_index(documents)


st.subheader("Resumen general")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Estado",
    f"{semaforo_icon(overall['color'])} {overall['label']}",
)
c2.metric(
    "Atención",
    f"{overall['score']}/100",
)
c3.metric(
    "Documentos",
    len(documents),
)
c4.metric(
    "Contradicciones",
    len(contradictions),
)
c5.metric(
    "Pruebas faltantes",
    sum(
        row["Estado"] == "No localizada"
        for row in evidence
    ),
)

st.progress(overall["score"] / 100)


tabs = st.tabs(
    [
        "📌 Datos",
        "🕒 Cronología",
        "🚦 Semáforos",
        "⚠️ Contradicciones",
        "🔎 Pruebas",
        "💬 Preguntar",
        "📨 Peticiones",
        "📤 Exportar",
    ]
)


with tabs[0]:
    st.subheader("Datos del proceso")

    metadata_df = pd.DataFrame(
        [
            {"Campo": key, "Valor": value}
            for key, value in metadata.items()
        ]
    )

    metadata_edit = st.data_editor(
        metadata_df,
        use_container_width=True,
        hide_index=True,
        key="integral_metadata",
    )


with tabs[1]:
    st.subheader("Línea de tiempo")

    timeline_edit = st.data_editor(
        timeline,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="integral_timeline",
    )

    st.markdown("### Calidad documental")

    st.dataframe(
        quality_df,
        use_container_width=True,
        hide_index=True,
    )


with tabs[2]:
    st.subheader("Semáforos por área")

    columns = st.columns(3)

    for index, item in enumerate(semaphore_items):
        with columns[index % 3]:
            text = (
                f"### {semaforo_icon(item.color)} {item.area}\n"
                f"**Atención:** {item.score}/100\n\n"
                f"**Motivo:** {item.reason}\n\n"
                f"**Acción:** {item.action}"
            )

            if item.color == "Rojo":
                st.error(text)
            elif item.color == "Amarillo":
                st.warning(text)
            else:
                st.success(text)


with tabs[3]:
    st.subheader("Contradicciones completas")

    if contradictions.empty:
        st.success(
            "No se detectaron contradicciones con las reglas actuales."
        )
    else:
        for index, row in contradictions.iterrows():
            with st.expander(
                f"Contradicción {index + 1}: {row.get('Tema', '')}",
                expanded=index == 0,
            ):
                left, right = st.columns(2)

                with left:
                    st.markdown("#### Versión 1")
                    st.write(
                        row.get(
                            "Versión 1 completa",
                            row.get("Versión 1", ""),
                        )
                    )
                    st.markdown(
                        f"**Documento de la versión 1:** "
                        f"{row.get('Documento de la versión 1', '')}"
                    )
                    st.markdown(
                        f"**Página:** {row.get('Página de la versión 1', '')}"
                    )

                with right:
                    st.markdown("#### Versión 2")
                    st.write(
                        row.get(
                            "Versión 2 completa",
                            row.get("Versión 2", ""),
                        )
                    )
                    st.markdown(
                        f"**Documento de la versión 2:** "
                        f"{row.get('Documento de la versión 2', '')}"
                    )
                    st.markdown(
                        f"**Página:** {row.get('Página de la versión 2', '')}"
                    )

                st.markdown("#### Explicación de la contradicción")
                st.write(row.get("Qué se contradice", ""))

                st.markdown("#### Por qué importa")
                st.write(row.get("Por qué importa", ""))

                st.markdown("#### Todo lo que debes revisar")
                st.warning(row.get("Todo lo que debe revisarse", ""))

                st.markdown("#### Prueba que puede faltar")
                st.write(row.get("Prueba que puede faltar", ""))

                st.markdown("#### Conclusión preliminar")
                st.info(row.get("Conclusión preliminar", ""))

        contradictions = st.data_editor(
            contradictions,
            use_container_width=True,
            hide_index=True,
            key="integral_contradictions",
        )


with tabs[4]:
    st.subheader("Inventario de pruebas")

    evidence_df = pd.DataFrame(evidence)

    evidence_edit = st.data_editor(
        evidence_df,
        use_container_width=True,
        hide_index=True,
        key="integral_evidence",
    )

    st.markdown("### Vacíos probatorios")

    if missing_actions:
        for number, action in enumerate(
            missing_actions,
            start=1,
        ):
            st.warning(
                f"{number}. {action}"
            )
    else:
        st.success(
            "No se detectaron vacíos en las categorías configuradas."
        )

    st.markdown("### Teoría preliminar")
    st.info(case_theory)


with tabs[5]:
    st.subheader("Preguntar al expediente")

    suggestions = suggested_questions(documents)

    suggestion = st.selectbox(
        "Pregunta sugerida",
        ["Escribir otra pregunta"] + suggestions,
        key="integral_question_suggestion",
    )

    default_question = (
        ""
        if suggestion == "Escribir otra pregunta"
        else suggestion
    )

    question = st.text_area(
        "Pregunta",
        value=default_question,
        height=100,
        key="integral_question",
    )

    if st.button(
        "Consultar expediente",
        type="primary",
        key="integral_ask",
    ):
        result = answer_question(
            question,
            fragment_index,
            top_k=5,
        )

        st.session_state["integral_answer"] = result

    result = st.session_state.get(
        "integral_answer"
    )

    if result:
        st.markdown("### Respuesta")
        st.write(result["answer"])
        st.caption(
            f"{result['status']} — confianza {result['confidence']}%"
        )

        st.markdown("### Fuentes")

        for source in result["sources"]:
            with st.expander(
                f"{source['document']} — página {source['page']}"
            ):
                st.write(source["fragment"])


with tabs[6]:
    st.subheader("Comparador de peticiones y respuestas")

    names = list(documents)

    petition_candidates = [
        name
        for name, pages in documents.items()
        if classify_document(pages)[0]
        in {"Derecho de petición", "Acción de tutela"}
    ]

    default_index = (
        names.index(petition_candidates[0])
        if petition_candidates
        else 0
    )

    petition_doc = st.selectbox(
        "Documento con solicitudes",
        names,
        index=default_index,
        key="integral_petition_doc",
    )

    response_names = [
        name
        for name in names
        if name != petition_doc
    ]

    selected_responses = st.multiselect(
        "Documentos de respuesta",
        response_names,
        default=response_names,
        key="integral_response_docs",
    )

    requests = extract_requests(
        documents.get(petition_doc, [])
    )

    answer_pages = [
        page
        for name in selected_responses
        for page in documents.get(name, [])
    ]

    comparison_df = pd.DataFrame(
        compare_requests_with_answers(
            requests,
            answer_pages,
        )
    )

    if comparison_df.empty:
        st.warning(
            "No se detectaron solicitudes con los patrones actuales."
        )
    else:
        comparison_df = st.data_editor(
            comparison_df,
            use_container_width=True,
            hide_index=True,
            key="integral_comparison",
        )


with tabs[7]:
    st.subheader("Exportar todo")

    export_metadata = pd.DataFrame(
        [
            {"Campo": key, "Valor": value}
            for key, value in metadata.items()
        ]
    )

    export_semaphores = pd.DataFrame(
        [
            {
                "Área": item.area,
                "Color": item.color,
                "Atención": item.score,
                "Motivo": item.reason,
                "Acción": item.action,
                "Fuente": item.source,
            }
            for item in semaphore_items
        ]
    )

    export_evidence = pd.DataFrame(evidence)
    export_entities = pd.DataFrame(entities)
    export_relations = pd.DataFrame(relations)

    excel = io.BytesIO()

    with pd.ExcelWriter(
        excel,
        engine="openpyxl",
    ) as writer:
        export_metadata.to_excel(
            writer,
            sheet_name="Datos",
            index=False,
        )
        timeline.to_excel(
            writer,
            sheet_name="Cronologia",
            index=False,
        )
        quality_df.to_excel(
            writer,
            sheet_name="Calidad",
            index=False,
        )
        export_semaphores.to_excel(
            writer,
            sheet_name="Semaforos",
            index=False,
        )
        contradictions.to_excel(
            writer,
            sheet_name="Contradicciones",
            index=False,
        )
        export_evidence.to_excel(
            writer,
            sheet_name="Pruebas",
            index=False,
        )
        export_entities.to_excel(
            writer,
            sheet_name="Entidades",
            index=False,
        )
        export_relations.to_excel(
            writer,
            sheet_name="Relaciones",
            index=False,
        )

    st.download_button(
        "Descargar análisis integral en Excel",
        data=excel.getvalue(),
        file_name="panel_integral_expediente.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    st.info(
        "Este archivo reúne datos, cronología, calidad, semáforos, "
        "contradicciones, pruebas, entidades y relaciones."
    )


st.warning(
    "El panel integral genera alertas preliminares. Verifica siempre "
    "el documento original, la página, el contexto y los términos aplicables."
)


