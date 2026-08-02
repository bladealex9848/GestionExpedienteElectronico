from __future__ import annotations

import hashlib
import io

import pandas as pd
import streamlit as st

from legal_analyzer.advanced_legal_engine import analyze, answer_question
from legal_analyzer.document_loader import load_document
from legal_analyzer.models import PageTrace
from legal_analyzer.ocr_engine import OCRConfig


st.set_page_config(
    page_title="Motor Jurídico Avanzado",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Motor Jurídico Avanzado")
st.caption(
    "Análisis cruzado de documentos, preguntas con evidencia, términos, "
    "errores, contradicciones y posibles conductas para Vigilancia Judicial."
)

st.error(
    "Este motor produce hallazgos preliminares. No declara responsabilidad, "
    "no sustituye recursos y no puede afirmar una violación sin verificación humana."
)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@st.cache_data(show_spinner=False, max_entries=250)
def cached_load(name, content_hash, content, enabled, min_chars, max_pages, dpi):
    del content_hash
    config = OCRConfig(
        enabled=enabled,
        min_useful_characters=min_chars,
        max_ocr_pages=max_pages,
        dpi=dpi,
    )
    return [item.to_dict() for item in load_document(name, content, config)]


def restore(data: dict) -> PageTrace:
    return PageTrace(**data)


with st.sidebar:
    st.header("OCR")
    enabled = st.checkbox("Aplicar OCR", value=True)
    min_chars = st.slider("Mínimo de caracteres útiles", 20, 300, 80, 10)
    max_pages = st.slider("Máximo de páginas OCR", 5, 200, 75, 5)
    dpi = st.select_slider(
        "Resolución OCR",
        [150, 200, 220, 250, 300],
        value=220,
    )


uploaded_files = st.file_uploader(
    "Carga uno o varios documentos del expediente",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.stop()


pages = []
errors_loading = []

with st.spinner("Leyendo documentos y construyendo el análisis cruzado..."):
    for uploaded in uploaded_files:
        try:
            raw = cached_load(
                uploaded.name,
                digest(uploaded.getvalue()),
                uploaded.getvalue(),
                enabled,
                min_chars,
                max_pages,
                dpi,
            )
            pages.extend(restore(item) for item in raw)
        except Exception as error:
            errors_loading.append(f"{uploaded.name}: {error}")


if errors_loading:
    st.warning(
        "Algunos archivos no pudieron leerse completamente:\n\n"
        + "\n".join(errors_loading)
    )

if not pages:
    st.error("No se pudo obtener texto útil de los documentos.")
    st.stop()


result = analyze(pages)


st.subheader("1. Preguntar al expediente")

default_questions = [
    "¿Cuál es la última actuación y qué sigue pendiente?",
    "¿Existen términos vencidos?",
    "¿Hay contradicciones entre los documentos?",
    "¿Qué errores fácticos aparecen?",
    "¿Se omitió valorar alguna prueba relevante?",
    "¿La notificación está suficientemente acreditada?",
    "¿El despacho dejó una solicitud sin resolver?",
    "¿Hay señales de mora o inactividad?",
    "¿Se adoptaron medidas suficientes para cumplir la tutela?",
    "¿Hay elementos para preparar Vigilancia Judicial Administrativa?",
]

selected = st.selectbox(
    "Selecciona una pregunta importante",
    ["Escribir otra pregunta"] + default_questions,
)

question = (
    st.text_area("Escribe la pregunta", height=90)
    if selected == "Escribir otra pregunta"
    else selected
)

if st.button(
    "Responder con evidencia documental",
    type="primary",
    use_container_width=True,
):
    response = answer_question(question, pages)

    st.info(
        f"**Confianza preliminar: {response['Confianza']}%**\n\n"
        f"{response['Respuesta']}"
    )

    if response["Evidencia"]:
        st.dataframe(
            pd.DataFrame(response["Evidencia"]),
            use_container_width=True,
            hide_index=True,
        )


st.subheader("2. Semáforo integral avanzado")

color = result["color"]
score = result["score"]
icon = {"Rojo": "🔴", "Amarillo": "🟡", "Verde": "🟢"}[color]

if color == "Rojo":
    st.error(f"{icon} REVISIÓN PRIORITARIA — {score}/100")
elif color == "Amarillo":
    st.warning(f"{icon} REQUIERE COMPLETAR Y VERIFICAR — {score}/100")
else:
    st.success(f"{icon} SIN INDICIOS SUFICIENTES — {score}/100")

components = pd.DataFrame(
    [
        {"Componente": key, "Puntaje": value}
        for key, value in result["score_components"].items()
    ]
)

st.dataframe(
    components,
    use_container_width=True,
    hide_index=True,
)


st.subheader("3. Términos detectados")

terms_df = pd.DataFrame(result["terms"])

if terms_df.empty:
    st.warning("No se detectaron términos expresos.")
else:
    st.dataframe(terms_df, use_container_width=True, hide_index=True)


st.subheader("4. Contradicciones entre documentos")

contradictions_df = pd.DataFrame(result["contradictions"])

if contradictions_df.empty:
    st.success("No se detectaron contradicciones claras con las reglas actuales.")
else:
    st.dataframe(
        contradictions_df,
        use_container_width=True,
        hide_index=True,
    )

    for index, row in contradictions_df.iterrows():
        with st.expander(
            f"Contradicción {index + 1}: {row['Tema']}",
            expanded=index == 0,
        ):
            st.markdown(
                f"**Documento 1:** {row['Documento versión 1']}, "
                f"página {row['Página versión 1']}"
            )
            st.markdown(f"**Versión 1:** {row['Versión 1']}")
            st.markdown(
                f"**Documento 2:** {row['Documento versión 2']}, "
                f"página {row['Página versión 2']}"
            )
            st.markdown(f"**Versión 2:** {row['Versión 2']}")
            st.warning(row["Qué debe revisarse"])


st.subheader("5. Posibles errores")

errors_df = pd.DataFrame(result["errors"])

if errors_df.empty:
    st.success("No se detectaron errores claros con las reglas actuales.")
else:
    st.dataframe(errors_df, use_container_width=True, hide_index=True)


st.subheader("6. Conductas relevantes para Vigilancia Judicial")

conducts_df = pd.DataFrame(result["conducts"])

if conducts_df.empty:
    st.warning("No se detectaron conductas claras con las reglas actuales.")
else:
    st.dataframe(conducts_df, use_container_width=True, hide_index=True)


st.subheader("7. Conclusión y actuación sugerida")

if color == "Rojo":
    conclusion = (
        "El expediente requiere revisión prioritaria. Antes de radicar, confirma "
        "la fecha real de notificación, el vencimiento de los términos, la actuación "
        "concreta pendiente, las contradicciones y el estado actual del proceso."
    )
elif color == "Amarillo":
    conclusion = (
        "Hay indicios útiles, pero faltan verificaciones o soportes. Completa la "
        "cronología y las constancias antes de presentar la solicitud."
    )
else:
    conclusion = (
        "Con los documentos actuales no aparecen elementos suficientes para recomendar "
        "una Vigilancia Judicial."
    )

st.info(conclusion)


st.subheader("8. Resolver actuaciones recomendadas paso a paso")

st.caption(
    "La aplicación solicitará un documento por vez. "
    "Cada documento se analiza antes de continuar con la siguiente actuación."
)

DOCUMENT_STEPS = [
    {
        "title": "1. Confirmar fecha real de notificación o ejecutoria",
        "document": "Constancia de notificación, correo completo, acuse de recibo o constancia de ejecutoria",
        "question": (
            "¿Cuál es la fecha real de notificación o ejecutoria, "
            "a quién se notificó y desde cuándo comienza el término?"
        ),
        "purpose": (
            "Establecer la fecha jurídicamente relevante para contar el término."
        ),
    },
    {
        "title": "2. Verificar el vencimiento del término",
        "document": "Providencia que fijó el término y constancia de notificación",
        "question": (
            "¿Qué término fue concedido, desde qué fecha se cuenta "
            "y cuál sería su fecha de vencimiento?"
        ),
        "purpose": (
            "Comprobar si el término realmente venció y evitar cálculos basados "
            "solo en la fecha del escrito."
        ),
    },
    {
        "title": "3. Obtener constancia secretarial",
        "document": "Constancia secretarial, estado, anotación del sistema o respuesta del juzgado",
        "question": (
            "¿La secretaría certifica el vencimiento del término, "
            "la presentación de respuestas o el paso del expediente al despacho?"
        ),
        "purpose": (
            "Acreditar oficialmente lo ocurrido después del vencimiento."
        ),
    },
    {
        "title": "4. Verificar si el expediente pasó al despacho",
        "document": "Consulta actualizada del proceso, captura, reporte o constancia del expediente",
        "question": (
            "¿Cuál es la última actuación registrada y aparece que el expediente "
            "pasó al despacho para decisión?"
        ),
        "purpose": (
            "Identificar el estado actual y la actuación que permanece pendiente."
        ),
    },
    {
        "title": "5. Identificar la actuación concreta pendiente",
        "document": "Última providencia, auto, fallo o actuación del despacho",
        "question": (
            "¿Qué ordenó el despacho y qué actuación concreta debía realizar después?"
        ),
        "purpose": (
            "Precisar la conducta que se solicita impulsar mediante la vigilancia."
        ),
    },
    {
        "title": "6. Comprobar el memorial o solicitud sin resolver",
        "document": "Memorial, incidente, solicitud de impulso o petición presentada",
        "question": (
            "¿Qué pidió el interesado, en qué fecha lo presentó "
            "y cuál era la actuación solicitada?"
        ),
        "purpose": (
            "Demostrar que existe una solicitud concreta pendiente de trámite."
        ),
    },
    {
        "title": "7. Comprobar la recepción del memorial",
        "document": "Correo enviado, sello de recibido, radicación o acuse",
        "question": (
            "¿Existe prueba de recepción del memorial, cuál es la fecha "
            "y qué destinatario lo recibió?"
        ),
        "purpose": (
            "Evitar afirmar falta de trámite sin acreditar primero la recepción."
        ),
    },
    {
        "title": "8. Construir la cronología del expediente",
        "document": "Documento adicional relevante para completar la secuencia",
        "question": (
            "¿Qué fecha, actuación, obligación o respuesta aporta este documento "
            "a la cronología del proceso?"
        ),
        "purpose": (
            "Completar la secuencia de hechos, términos y actuaciones pendientes."
        ),
    },
    {
        "title": "9. Verificar posibles errores",
        "document": "Documento fuente para comparar el error detectado",
        "question": (
            "¿El documento confirma o descarta el posible error fáctico, "
            "probatorio, de identificación o de congruencia?"
        ),
        "purpose": (
            "Separar errores reales de diferencias explicables o citas válidas."
        ),
    },
    {
        "title": "10. Preparar la solicitud de Vigilancia Judicial",
        "document": "Borrador de la solicitud o escrito que se pretende radicar",
        "question": (
            "¿El escrito identifica despacho, radicado, actuación pendiente, "
            "cronología, soportes y petición administrativa sin pedir que se cambie "
            "el contenido de una providencia?"
        ),
        "purpose": (
            "Revisar que la solicitud final sea clara, documentada y adecuada al mecanismo."
        ),
    },
]


if "step_document_results" not in st.session_state:
    st.session_state["step_document_results"] = {}


completed_steps = 0
step_summary_rows = []

for step_index, step in enumerate(DOCUMENT_STEPS, start=1):
    stored = st.session_state["step_document_results"].get(step_index)

    with st.expander(
        step["title"],
        expanded=(step_index == 1 or stored is not None),
    ):
        st.markdown(f"**Documento solicitado:** {step['document']}")
        st.markdown(f"**Objetivo:** {step['purpose']}")
        st.markdown(f"**Pregunta que resolverá el sistema:** {step['question']}")

        step_file = st.file_uploader(
            "Cargar este documento",
            type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
            accept_multiple_files=False,
            key=f"step_document_{step_index}",
        )

        step_notes = st.text_area(
            "Observaciones del usuario",
            key=f"step_notes_{step_index}",
            placeholder="Escribe cualquier dato que ayude a interpretar este documento.",
            height=70,
        )

        if step_file is not None:
            if st.button(
                "Analizar este documento",
                key=f"analyze_step_{step_index}",
                use_container_width=True,
            ):
                try:
                    raw_step = cached_load(
                        step_file.name,
                        digest(step_file.getvalue()),
                        step_file.getvalue(),
                        enabled,
                        min_chars,
                        max_pages,
                        dpi,
                    )

                    step_pages = [
                        restore(item)
                        for item in raw_step
                    ]

                    step_response = answer_question(
                        step["question"],
                        step_pages,
                    )

                    st.session_state["step_document_results"][step_index] = {
                        "Paso": step_index,
                        "Actuación": step["title"],
                        "Documento solicitado": step["document"],
                        "Archivo cargado": step_file.name,
                        "Pregunta": step["question"],
                        "Respuesta": step_response["Respuesta"],
                        "Confianza": step_response["Confianza"],
                        "Evidencia": step_response["Evidencia"],
                        "Observaciones": step_notes,
                        "Estado": (
                            "Resuelto preliminarmente"
                            if step_response["Evidencia"]
                            else "Requiere otro soporte"
                        ),
                    }

                    st.rerun()

                except Exception as error:
                    st.error(
                        f"No fue posible analizar el documento: {error}"
                    )

        stored = st.session_state["step_document_results"].get(step_index)

        if stored:
            if stored["Estado"] == "Resuelto preliminarmente":
                st.success(
                    f"✅ Paso resuelto preliminarmente — "
                    f"confianza {stored['Confianza']}%"
                )
                completed_steps += 1
            else:
                st.warning(
                    "⚠️ El documento no contiene evidencia suficiente. "
                    "Carga otro soporte para este mismo paso."
                )

            st.info(stored["Respuesta"])

            if stored["Evidencia"]:
                evidence_step_df = pd.DataFrame(
                    stored["Evidencia"]
                )
                st.dataframe(
                    evidence_step_df,
                    use_container_width=True,
                    hide_index=True,
                )

            if st.button(
                "Eliminar resultado y cargar otro documento",
                key=f"clear_step_{step_index}",
            ):
                del st.session_state["step_document_results"][step_index]
                st.rerun()

            step_summary_rows.append(
                {
                    key: value
                    for key, value in stored.items()
                    if key != "Evidencia"
                }
            )
        else:
            step_summary_rows.append(
                {
                    "Paso": step_index,
                    "Actuación": step["title"],
                    "Documento solicitado": step["document"],
                    "Archivo cargado": "",
                    "Pregunta": step["question"],
                    "Respuesta": "",
                    "Confianza": 0,
                    "Observaciones": step_notes,
                    "Estado": "Pendiente",
                }
            )


st.markdown("### Progreso general")

progress_percentage = round(
    completed_steps / len(DOCUMENT_STEPS) * 100
)

st.progress(
    completed_steps / len(DOCUMENT_STEPS)
)

st.write(
    f"**Pasos resueltos:** {completed_steps} de {len(DOCUMENT_STEPS)} "
    f"— {progress_percentage}%"
)

if completed_steps == len(DOCUMENT_STEPS):
    st.success(
        "✅ Se completaron los documentos esenciales. "
        "Ya puedes revisar el expediente completo y preparar la solicitud final."
    )
elif completed_steps >= 7:
    st.warning(
        "🟡 El expediente está avanzado, pero todavía faltan algunos documentos."
    )
else:
    st.error(
        "🔴 Todavía faltan documentos esenciales para resolver todas las actuaciones."
    )


step_summary_df = pd.DataFrame(
    step_summary_rows
)

st.dataframe(
    step_summary_df,
    use_container_width=True,
    hide_index=True,
)

st.session_state["step_document_summary"] = step_summary_df


st.subheader("9. Exportar análisis")

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    components.to_excel(writer, sheet_name="Puntaje", index=False)
    terms_df.to_excel(writer, sheet_name="Términos", index=False)
    contradictions_df.to_excel(writer, sheet_name="Contradicciones", index=False)
    errors_df.to_excel(writer, sheet_name="Errores", index=False)
    conducts_df.to_excel(writer, sheet_name="Conductas", index=False)

    st.session_state.get(
        "step_document_summary",
        pd.DataFrame(),
    ).to_excel(
        writer,
        sheet_name="Documentos paso a paso",
        index=False,
    )

    st.session_state.get(
        "step_document_summary",
        pd.DataFrame(),
    ).to_excel(
        writer,
        sheet_name="Documentos paso a paso",
        index=False,
    )

st.download_button(
    "Descargar análisis avanzado en Excel",
    data=output.getvalue(),
    file_name="motor_juridico_avanzado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)


