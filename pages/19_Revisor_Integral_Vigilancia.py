from __future__ import annotations

import hashlib
import io
import re
from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

from legal_analyzer.document_loader import load_document
from legal_analyzer.models import PageTrace
from legal_analyzer.ocr_engine import OCRConfig


st.set_page_config(
    page_title="Revisor Integral de Vigilancia",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ Revisor Integral de Vigilancia Judicial")
st.caption(
    "Carga documentos, formula una pregunta y recibe una respuesta sustentada; "
    "además revisa errores, términos y posibles conductas relevantes."
)

st.error(
    "Los resultados son preliminares. El sistema identifica indicios, no declara "
    "responsabilidad del despacho ni reemplaza recursos, incidentes o asesoría jurídica."
)


MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

NUMBER_WORDS = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3,
    "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
    "ocho": 8, "nueve": 9, "diez": 10, "quince": 15,
    "veinte": 20, "treinta": 30, "cuarenta y ocho": 48,
}

CONDUCTS = [
    {
        "name": "Mora o inactividad aparente",
        "terms": (
            "pendiente de decision", "sin resolver", "no se ha resuelto",
            "pase a despacho", "se encuentra a despacho", "mora",
            "sin pronunciamiento", "vencido el termino",
        ),
        "norm": "Ley 270 de 1996, artículos 4 y 7; Acuerdo PSAA11-8716 de 2011",
        "purpose": "Revisar oportunidad, celeridad y eficacia de la gestión.",
    },
    {
        "name": "Falta de trámite de memorial o solicitud",
        "terms": (
            "memorial de impulso", "solicitud de decision",
            "solicitud sin respuesta", "peticion sin respuesta",
            "no se dio tramite",
        ),
        "norm": "Constitución, artículos 29 y 229; Ley 270 de 1996",
        "purpose": "Verificar si una actuación presentada quedó sin gestión.",
    },
    {
        "name": "Notificación posiblemente incompleta",
        "terms": (
            "notificar", "correo electronico", "mensaje de datos",
            "sin constancia de notificacion", "no fue notificado",
        ),
        "norm": "Norma procesal aplicable; Ley 2213 de 2022, artículo 8, según el caso",
        "purpose": "Comprobar envío, entrega, acceso y fecha de inicio del término.",
    },
    {
        "name": "Seguimiento insuficiente del cumplimiento de tutela",
        "terms": (
            "incidente de desacato", "incumplimiento del fallo",
            "dar cumplimiento", "continua el incumplimiento",
            "no se cumplio la tutela",
        ),
        "norm": "Decreto 2591 de 1991, artículos 27 y 52",
        "purpose": "Verificar medidas para lograr el cumplimiento efectivo.",
    },
]

ERROR_RULES = [
    {
        "name": "Radicados diferentes dentro del expediente",
        "category": "Error fáctico o de identificación",
        "norm": "Constitución Política, artículo 29",
    },
    {
        "name": "Fechas incompatibles o futuras",
        "category": "Error fáctico",
        "norm": "Constitución Política, artículo 29",
    },
    {
        "name": "Confusión del objeto ordenado o entregado",
        "category": "Error fáctico y de congruencia",
        "norm": "Constitución Política, artículo 29",
    },
    {
        "name": "Afirmación de falta de prueba pese a referencias a anexos",
        "category": "Posible omisión probatoria",
        "norm": "Constitución Política, artículo 29",
    },
]


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.translate(
            str.maketrans(
                "áéíóúüñÁÉÍÓÚÜÑ",
                "aeiouunAEIOUUN",
            )
        ).lower(),
    ).strip()


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@st.cache_data(show_spinner=False, max_entries=200)
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


def extract_dates(text: str) -> list[date]:
    clean = normalize(text)
    values = []

    for day, month, year in re.findall(
        r"\b([0-3]?\d)[/-]([01]?\d)[/-]((?:19|20)\d{2})\b",
        clean,
    ):
        try:
            values.append(date(int(year), int(month), int(day)))
        except ValueError:
            pass

    pattern = (
        r"\b([0-3]?\d)\s+de\s+("
        + "|".join(MONTHS.keys())
        + r")\s+de\s+((?:19|20)\d{2})\b"
    )

    for day, month_name, year in re.findall(pattern, clean):
        try:
            values.append(date(int(year), MONTHS[month_name], int(day)))
        except ValueError:
            pass

    judicial = (
        r"\(([0-3]?\d)\)\s+de\s+("
        + "|".join(MONTHS.keys())
        + r")\s+de\s+[^()\n]{0,100}\(((?:19|20)\d{2})\)"
    )

    for day, month_name, year in re.findall(judicial, clean):
        try:
            values.append(date(int(year), MONTHS[month_name], int(day)))
        except ValueError:
            pass

    return list(dict.fromkeys(values))


def extract_radications(text: str) -> list[str]:
    patterns = [
        r"\b\d{2}-\d{3}-\d{2}-\d{2}-\d{3}-\d{4}-\d{5}-\d{2}\b",
        r"\b\d{23}\b",
    ]
    values = []
    for pattern in patterns:
        values.extend(re.findall(pattern, text))
    return list(dict.fromkeys(values))


def detect_terms(document: str, pages: list[PageTrace]) -> list[dict]:
    rows = []
    word_pattern = (
        "cuarenta y ocho|treinta|veinte|quince|diez|nueve|ocho|"
        "siete|seis|cinco|cuatro|tres|dos|un|uno|una"
    )
    pattern = (
        rf"(?:dentro de|termino(?: \w+){{0,4}} de|plazo(?: \w+){{0,4}} de)\s+"
        rf"(?P<number>{word_pattern}|\d{{1,3}})\s*"
        rf"(?P<unit>horas?|dias?)"
        rf"(?:\s*\((?P<paren>\d{{1,3}})\)\s*(?:horas?|dias?)?)?"
    )

    document_date = None
    full_text = "\n".join(page.text or "" for page in pages)
    dates = extract_dates(full_text)
    if dates:
        document_date = dates[0]

    for page in pages:
        fragments = [
            item.strip()
            for item in re.split(r"(?<=[.;:])\s+|\n+", page.text or "")
            if len(item.strip()) >= 20
        ]

        for fragment in fragments:
            clean = normalize(fragment)
            match = re.search(pattern, clean)
            if not match:
                continue

            raw_number = match.group("number")
            parenthetical = match.groupdict().get("paren")

            if parenthetical:
                quantity = int(parenthetical)
            elif raw_number.isdigit():
                quantity = int(raw_number)
            else:
                quantity = NUMBER_WORDS.get(raw_number)

            if quantity is None:
                continue

            unit = "Horas" if "hora" in match.group("unit") else "Días"
            day_rule = "Calendario" if "calendario" in clean else "Hábiles"
            start = None
            deadline = None

            if document_date:
                start = datetime.combine(
                    document_date + timedelta(days=1),
                    time(8, 0),
                )

                if unit == "Horas":
                    deadline = start + timedelta(hours=quantity)
                elif day_rule == "Calendario":
                    deadline = start + timedelta(days=max(quantity - 1, 0))
                else:
                    current = start
                    counted = 1
                    while counted < quantity:
                        current += timedelta(days=1)
                        if current.weekday() < 5:
                            counted += 1
                    deadline = current

            rows.append({
                "Documento": document,
                "Página": page.page,
                "Fragmento": fragment,
                "Cantidad": quantity,
                "Unidad": unit,
                "Tipo de días": day_rule,
                "Fecha del escrito usada": document_date,
                "Inicio estimado": start,
                "Vencimiento estimado": deadline,
                "Estado": (
                    "Vencido"
                    if deadline and deadline < datetime.now()
                    else "En plazo o por confirmar"
                ),
                "Advertencia": (
                    "El cálculo usa la fecha del escrito. Confirmar notificación, "
                    "ejecutoria, festivos y regla especial."
                ),
            })

    return rows


def detect_errors(document: str, pages: list[PageTrace]) -> list[dict]:
    findings = []
    full_text = "\n".join(page.text or "" for page in pages)
    clean = normalize(full_text)

    radications = extract_radications(full_text)
    if len(radications) > 1:
        findings.append({
            "Documento": document,
            "Página": "Varias",
            "Posible error": ERROR_RULES[0]["name"],
            "Categoría": ERROR_RULES[0]["category"],
            "Norma posible": ERROR_RULES[0]["norm"],
            "Evidencia": " / ".join(radications),
            "Explicación": (
                "Puede existir mezcla de expedientes o una cita válida. "
                "Debe verificarse la carátula y el contexto."
            ),
            "Severidad": "Alta",
        })

    future_dates = [d for d in extract_dates(full_text) if d > date.today()]
    if future_dates:
        findings.append({
            "Documento": document,
            "Página": "Varias",
            "Posible error": ERROR_RULES[1]["name"],
            "Categoría": ERROR_RULES[1]["category"],
            "Norma posible": ERROR_RULES[1]["norm"],
            "Evidencia": ", ".join(d.strftime("%d/%m/%Y") for d in future_dates),
            "Explicación": "La fecha puede ser programada o un error material.",
            "Severidad": "Media",
        })

    technical = []
    for token in ("phonak sky", "phonak naida", "lumity", "l90-up", "up l90"):
        if token in clean:
            technical.append(token)

    if len(set(technical)) >= 2:
        findings.append({
            "Documento": document,
            "Página": "Varias",
            "Posible error": ERROR_RULES[2]["name"],
            "Categoría": ERROR_RULES[2]["category"],
            "Norma posible": ERROR_RULES[2]["norm"],
            "Evidencia": " / ".join(sorted(set(technical))),
            "Explicación": (
                "Los documentos mencionan referencias diferentes. "
                "Debe compararse prescripción, fallo, autorización y entrega."
            ),
            "Severidad": "Alta",
        })

    if any(x in clean for x in ("no obra prueba", "no se acredito", "no se aporto")):
        if any(x in clean for x in ("anexo", "historia clinica", "constancia", "dictamen")):
            findings.append({
                "Documento": document,
                "Página": "Varias",
                "Posible error": ERROR_RULES[3]["name"],
                "Categoría": ERROR_RULES[3]["category"],
                "Norma posible": ERROR_RULES[3]["norm"],
                "Evidencia": "El texto niega prueba y también menciona anexos o soportes.",
                "Explicación": "Debe comprobarse si la prueba fue aportada y valorada.",
                "Severidad": "Alta",
            })

    return findings


def detect_conducts(document: str, pages: list[PageTrace]) -> list[dict]:
    rows = []
    full_text = "\n".join(page.text or "" for page in pages)
    clean = normalize(full_text)

    for rule in CONDUCTS:
        hits = [term for term in rule["terms"] if term in clean]
        if not hits:
            continue

        fragments = [
            item.strip()
            for item in re.split(r"(?<=[.;:])\s+|\n+", full_text)
            if any(term in normalize(item) for term in hits)
        ]

        rows.append({
            "Documento": document,
            "Posible conducta relevante": rule["name"],
            "Coincidencias": " | ".join(hits),
            "Fragmento principal": fragments[0] if fragments else "",
            "Norma o marco posible": rule["norm"],
            "Utilidad para vigilancia": rule["purpose"],
            "Conclusión": (
                "Indicio que debe verificarse con cronología, constancias "
                "y estado actual del proceso."
            ),
        })

    return rows


def answer_question(question: str, pages: list[PageTrace]) -> tuple[str, list[dict]]:
    clean_question = normalize(question)
    keywords = {
        word
        for word in re.findall(r"\b[a-z0-9]{4,}\b", clean_question)
        if word not in {
            "para", "como", "cual", "cuando", "donde", "esta",
            "este", "esto", "debe", "puede", "tiene", "hacer",
        }
    }

    candidates = []

    for page in pages:
        fragments = [
            item.strip()
            for item in re.split(r"(?<=[.;:])\s+|\n+", page.text or "")
            if len(item.strip()) >= 25
        ]

        for fragment in fragments:
            clean_fragment = normalize(fragment)
            score = sum(word in clean_fragment for word in keywords)
            if score:
                candidates.append({
                    "Documento": page.document,
                    "Página": page.page,
                    "Fragmento": fragment,
                    "Coincidencias": score,
                })

    candidates.sort(key=lambda item: item["Coincidencias"], reverse=True)
    top = candidates[:5]

    if not top:
        return (
            "No encontré en los documentos un fragmento suficiente para responder "
            "esa pregunta. Revisa el texto de la pregunta o carga más piezas del expediente.",
            [],
        )

    evidence_text = " ".join(item["Fragmento"] for item in top[:3])
    answer = (
        "Con base en los fragmentos más relacionados, el expediente indica lo siguiente: "
        + evidence_text
        + " Esta respuesta debe revisarse junto con el documento completo y no debe "
          "interpretarse como una conclusión jurídica definitiva."
    )

    return answer, top


with st.sidebar:
    st.header("OCR")
    enabled = st.checkbox("Aplicar OCR", value=True)
    min_chars = st.slider("Mínimo de caracteres útiles", 20, 300, 80, 10)
    max_pages = st.slider("Máximo de páginas OCR", 5, 150, 50, 5)
    dpi = st.select_slider("Resolución OCR", [150, 200, 220, 250, 300], value=220)


IMPORTANT_QUESTIONS = [
    "¿Cuál es la última actuación judicial registrada y qué actuación continúa pendiente?",
    "¿Existe un término legal o judicial vencido y desde qué fecha debe contarse?",
    "¿El despacho dejó vencer un término sin emitir la decisión o actuación correspondiente?",
    "¿Se presentó un memorial, incidente o solicitud que todavía no ha sido resuelto?",
    "¿Existe constancia válida de notificación a todas las partes y sujetos vinculados?",
    "¿Hay contradicciones entre los hechos, las pruebas, la motivación y la parte resolutiva?",
    "¿El despacho confundió nombres, entidades, fechas, radicados, dispositivos u objetos de la orden?",
    "¿Se omitió valorar una prueba relevante que aparece aportada en el expediente?",
    "¿El despacho adoptó medidas suficientes para lograr el cumplimiento efectivo del fallo de tutela?",
    "¿Los documentos muestran conductas o demoras que podrían justificar una Vigilancia Judicial Administrativa?",
]

uploaded_files = st.file_uploader(
    "Carga uno o varios documentos del expediente",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.stop()


all_pages = []
documents = {}

with st.spinner("Leyendo y organizando documentos..."):
    for uploaded in uploaded_files:
        raw = cached_load(
            uploaded.name,
            digest(uploaded.getvalue()),
            uploaded.getvalue(),
            enabled,
            min_chars,
            max_pages,
            dpi,
        )
        pages = [restore(item) for item in raw]
        documents[uploaded.name] = pages
        all_pages.extend(pages)


st.subheader("1. Formular una pregunta y obtener respuesta")

st.markdown("### Diez preguntas relevantes para revisar el expediente")

selected_question = st.selectbox(
    "Selecciona una pregunta importante",
    options=["Escribir otra pregunta"] + IMPORTANT_QUESTIONS,
    key="important_question_selector",
)

if selected_question == "Escribir otra pregunta":
    question = st.text_area(
        "Escribe tu pregunta",
        placeholder=(
            "Ejemplo: ¿El juzgado dejó vencer el término sin decidir?"
        ),
        height=100,
        key="custom_process_question",
    )
else:
    st.info(f"Pregunta seleccionada: {selected_question}")
    question = selected_question

answer_button = st.button(
    "Analizar y responder la pregunta",
    type="primary",
    use_container_width=True,
)

if answer_button and question.strip():
    answer, evidence = answer_question(
        question,
        all_pages,
    )

    st.markdown("### Respuesta basada en los documentos")
    st.info(answer)

    if evidence:
        evidence_df = pd.DataFrame(evidence)

        st.markdown("#### Fragmentos utilizados para responder")
        st.dataframe(
            evidence_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### Detalle de la respuesta")

        for number, item in enumerate(evidence, start=1):
            with st.expander(
                f"Evidencia {number}: {item['Documento']} — página {item['Página']}",
                expanded=number == 1,
            ):
                st.markdown(f"**Fragmento completo:** {item['Fragmento']}")
                st.markdown(
                    f"**Coincidencias con la pregunta:** {item['Coincidencias']}"
                )
    else:
        st.warning(
            "No se encontró evidencia documental suficiente para responder."
        )

st.markdown("#### Lista de las 10 preguntas de control")

for number, important_question in enumerate(
    IMPORTANT_QUESTIONS,
    start=1,
):
    st.markdown(f"{number}. {important_question}")


st.subheader("2. Conteo automático de términos")

term_rows = []
for document, pages in documents.items():
    term_rows.extend(detect_terms(document, pages))

terms_df = pd.DataFrame(term_rows)

if terms_df.empty:
    st.warning("No se detectaron términos expresos con las reglas actuales.")
else:
    st.dataframe(terms_df, use_container_width=True, hide_index=True)


st.subheader("3. Posibles errores encontrados")

error_rows = []
for document, pages in documents.items():
    error_rows.extend(detect_errors(document, pages))

errors_df = pd.DataFrame(error_rows)

if errors_df.empty:
    st.success(
        "No se detectaron errores claros con las reglas automáticas. "
        "Esto no demuestra que el expediente esté libre de errores."
    )
else:
    st.dataframe(errors_df, use_container_width=True, hide_index=True)


st.subheader("4. Conductas que podrían ameritar Vigilancia Judicial")

conduct_rows = []
for document, pages in documents.items():
    conduct_rows.extend(detect_conducts(document, pages))

conducts_df = pd.DataFrame(conduct_rows)

if conducts_df.empty:
    st.warning(
        "No se identificaron conductas claras relacionadas con mora o gestión. "
        "Puede faltar una actuación, constancia o consulta actual del proceso."
    )
else:
    st.dataframe(conducts_df, use_container_width=True, hide_index=True)


st.subheader("5. Semáforo integral — informe detallado")

expired_terms = (
    terms_df[terms_df["Estado"] == "Vencido"]
    if not terms_df.empty
    else pd.DataFrame()
)

high_errors = (
    errors_df[errors_df["Severidad"] == "Alta"]
    if not errors_df.empty
    else pd.DataFrame()
)

risk_terms = 30 if not expired_terms.empty else 0
risk_errors = min(35, len(errors_df) * 15)
risk_conducts = min(35, len(conducts_df) * 20)
risk = min(
    100,
    risk_terms + risk_errors + risk_conducts,
)

if risk >= 65:
    semaphore_color = "Rojo"
    semaphore_title = "REVISIÓN PRIORITARIA"
    st.error(
        f"🔴 {semaphore_title} — {risk}/100. "
        "Hay términos vencidos, errores relevantes o conductas que deben comprobarse."
    )
elif risk >= 30:
    semaphore_color = "Amarillo"
    semaphore_title = "REQUIERE COMPLETAR Y VERIFICAR"
    st.warning(
        f"🟡 {semaphore_title} — {risk}/100."
    )
else:
    semaphore_color = "Verde"
    semaphore_title = "SIN INDICIOS SUFICIENTES"
    st.success(
        f"🟢 {semaphore_title} — {risk}/100."
    )


st.markdown("### Composición del puntaje")

score_details = pd.DataFrame(
    [
        {
            "Componente": "Términos vencidos",
            "Hallazgos": len(expired_terms),
            "Puntaje aportado": risk_terms,
            "Máximo": 30,
        },
        {
            "Componente": "Errores detectados",
            "Hallazgos": len(errors_df),
            "Puntaje aportado": risk_errors,
            "Máximo": 35,
        },
        {
            "Componente": "Conductas relevantes",
            "Hallazgos": len(conducts_df),
            "Puntaje aportado": risk_conducts,
            "Máximo": 35,
        },
    ]
)

st.dataframe(
    score_details,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### Razones de importancia")

important_reasons = []

if not expired_terms.empty:
    important_reasons.append(
        f"Se detectaron {len(expired_terms)} término(s) clasificado(s) como vencido(s)."
    )

if not high_errors.empty:
    important_reasons.append(
        f"Se detectaron {len(high_errors)} posible(s) error(es) de severidad alta."
    )

if not conducts_df.empty:
    important_reasons.append(
        f"Se identificaron {len(conducts_df)} posible(s) conducta(s) relacionada(s) "
        "con demora, falta de trámite, notificación o cumplimiento."
    )

if important_reasons:
    for reason in important_reasons:
        st.markdown(f"⚠️ {reason}")
else:
    st.markdown(
        "✅ Las reglas automáticas no encontraron razones suficientes "
        "para una revisión prioritaria."
    )


st.markdown("### Detalle de términos vencidos")

if expired_terms.empty:
    st.success("No se clasificaron términos como vencidos.")
else:
    st.dataframe(
        expired_terms,
        use_container_width=True,
        hide_index=True,
    )

    for index, row in expired_terms.iterrows():
        with st.expander(
            f"Término vencido: {row['Documento']} — página {row['Página']}",
            expanded=True,
        ):
            st.markdown(f"**Texto:** {row['Fragmento']}")
            st.markdown(
                f"**Cantidad:** {row['Cantidad']} {str(row['Unidad']).lower()}"
            )
            st.markdown(
                f"**Fecha del escrito usada:** {row['Fecha del escrito usada']}"
            )
            st.markdown(
                f"**Inicio estimado:** {row['Inicio estimado']}"
            )
            st.markdown(
                f"**Vencimiento estimado:** {row['Vencimiento estimado']}"
            )
            st.warning(row["Advertencia"])


st.markdown("### Detalle de posibles errores")

if errors_df.empty:
    st.success("No se detectaron errores claros con las reglas automáticas.")
else:
    for index, row in errors_df.iterrows():
        severity_icon = "🔴" if row["Severidad"] == "Alta" else "🟡"

        with st.expander(
            f"{severity_icon} {row['Posible error']} — {row['Documento']}",
            expanded=row["Severidad"] == "Alta",
        ):
            st.markdown(f"**Categoría:** {row['Categoría']}")
            st.markdown(f"**Evidencia encontrada:** {row['Evidencia']}")
            st.markdown(f"**Explicación:** {row['Explicación']}")
            st.markdown(f"**Norma posible:** {row['Norma posible']}")
            st.markdown(f"**Severidad:** {row['Severidad']}")
            st.caption(
                "El hallazgo debe contrastarse con el documento completo y "
                "con las demás piezas del expediente."
            )


st.markdown("### Detalle de conductas relevantes para Vigilancia Judicial")

if conducts_df.empty:
    st.warning(
        "No se encontraron conductas claras con las reglas actuales."
    )
else:
    for index, row in conducts_df.iterrows():
        with st.expander(
            f"🏛️ {row['Posible conducta relevante']} — {row['Documento']}",
            expanded=True,
        ):
            st.markdown(f"**Coincidencias:** {row['Coincidencias']}")
            st.markdown(
                f"**Fragmento principal:** {row['Fragmento principal']}"
            )
            st.markdown(
                f"**Norma o marco posible:** {row['Norma o marco posible']}"
            )
            st.markdown(
                f"**Utilidad para la vigilancia:** "
                f"{row['Utilidad para vigilancia']}"
            )
            st.markdown(f"**Conclusión preliminar:** {row['Conclusión']}")


st.markdown("### Actuaciones recomendadas")

recommended_actions = []

if not expired_terms.empty:
    recommended_actions.extend(
        [
            "Confirmar la fecha real de notificación o ejecutoria de cada providencia.",
            "Solicitar constancia secretarial del vencimiento del término.",
            "Verificar si después del vencimiento el expediente pasó al despacho.",
        ]
    )

if not conducts_df.empty:
    recommended_actions.extend(
        [
            "Obtener una consulta actualizada del expediente.",
            "Identificar la actuación concreta que permanece pendiente.",
            "Adjuntar el memorial o solicitud sin resolver y su constancia de recepción.",
            "Preparar una cronología breve con fechas, documentos y actuaciones pendientes.",
        ]
    )

if not errors_df.empty:
    recommended_actions.extend(
        [
            "Comparar cada posible error con el documento fuente correspondiente.",
            "Separar los errores que deben discutirse mediante recursos de aquellos "
            "que muestran falta de gestión administrativa.",
        ]
    )

if risk >= 65:
    recommended_actions.append(
        "Preparar la solicitud de Vigilancia Judicial Administrativa, "
        "sin pedir que el Consejo cambie el contenido de una providencia."
    )

recommended_actions = list(
    dict.fromkeys(recommended_actions)
)

if recommended_actions:
    for number, action in enumerate(recommended_actions, start=1):
        st.markdown(f"{number}. {action}")
else:
    st.info(
        "Con los documentos actuales no se recomienda radicar todavía. "
        "Carga las constancias y actuaciones faltantes."
    )


st.markdown("### Conclusión integral")

if risk >= 65:
    integral_conclusion = (
        "El expediente requiere revisión prioritaria porque concurren uno o más "
        "indicadores de término vencido, posible error relevante o conducta relacionada "
        "con la gestión del despacho. El puntaje no prueba responsabilidad: indica que "
        "deben confirmarse la cronología, la notificación, la actuación pendiente y el "
        "estado actual antes de radicar la Vigilancia Judicial."
    )
elif risk >= 30:
    integral_conclusion = (
        "Existen indicios, pero la documentación todavía debe completarse o verificarse. "
        "No conviene radicar hasta confirmar fechas, términos, constancias y actuación pendiente."
    )
else:
    integral_conclusion = (
        "Las reglas automáticas no encontraron indicios suficientes para recomendar "
        "una Vigilancia Judicial con los documentos actuales."
    )

st.info(integral_conclusion)

st.session_state["integral_score_details"] = score_details
st.session_state["integral_summary"] = pd.DataFrame(
    [
        {
            "Semáforo": semaphore_color,
            "Resultado": semaphore_title,
            "Puntaje": risk,
            "Términos vencidos": len(expired_terms),
            "Errores detectados": len(errors_df),
            "Errores de severidad alta": len(high_errors),
            "Conductas relevantes": len(conducts_df),
            "Conclusión": integral_conclusion,
            "Actuaciones recomendadas": " | ".join(recommended_actions),
        }
    ]
)


st.subheader("6. Exportar análisis")

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    terms_df.to_excel(writer, sheet_name="Términos", index=False)
    errors_df.to_excel(writer, sheet_name="Errores", index=False)
    conducts_df.to_excel(writer, sheet_name="Conductas vigilancia", index=False)

    st.session_state.get(
        "integral_score_details",
        pd.DataFrame(),
    ).to_excel(
        writer,
        sheet_name="Detalle puntaje",
        index=False,
    )

    st.session_state.get(
        "integral_summary",
        pd.DataFrame(),
    ).to_excel(
        writer,
        sheet_name="Conclusión integral",
        index=False,
    )

st.download_button(
    "Descargar revisión integral en Excel",
    data=output.getvalue(),
    file_name="revision_integral_vigilancia.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)

