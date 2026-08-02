from __future__ import annotations

import hashlib
import io
import re
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from legal_analyzer.document_loader import load_document
from legal_analyzer.models import PageTrace
from legal_analyzer.ocr_engine import OCRConfig


st.set_page_config(
    page_title="Centro Integral de Auditoría Judicial",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ Centro Integral de Auditoría Judicial")
st.caption(
    "Todo en uno: carga del expediente, comparación con el fallo, errores, términos, "
    "preguntas, conductas para vigilancia, documentos pendientes y exportación."
)

st.error(
    "Los hallazgos son preliminares. No declaran responsabilidad ni sustituyen "
    "recursos, incidentes o revisión jurídica humana."
)


MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

RIGHTS = {
    "salud": ("derecho a la salud", "derecho fundamental a la salud"),
    "vida en condiciones dignas": ("vida en condiciones dignas", "vida digna"),
    "educación": ("derecho a la educacion", "derecho fundamental de educacion"),
    "libre circulación": ("libre circulacion", "derecho a la libre circulacion"),
    "dignidad humana": ("dignidad humana",),
    "igualdad": ("derecho a la igualdad", "igualdad material"),
}

OBJECTS = {
    "molde de silicona blanda intracanal": (
        "molde de silicona blanda intracanal",
        "molde de silicona",
    ),
    "audífono Naída P90": ("naida p90", "audifono naida p90"),
    "pilas tipo 675": ("pilas tipo 675", "pila tipo 675"),
    "tratamiento integral": ("tratamiento integral",),
}

QUESTIONS = [
    "¿Cuál es la última actuación judicial y qué actuación continúa pendiente?",
    "¿Existe un término vencido y desde qué fecha debe contarse?",
    "¿El despacho dejó vencer un término sin decidir?",
    "¿Hay diferencias entre el fallo original y los autos posteriores?",
    "¿Se modificó la fecha, los derechos tutelados o el objeto de la orden?",
    "¿Existe una solicitud o memorial sin resolver?",
    "¿La notificación está suficientemente acreditada?",
    "¿Se omitió valorar una prueba relevante?",
    "¿Se adoptaron medidas suficientes para lograr el cumplimiento de la tutela?",
    "¿Hay elementos para presentar Vigilancia Judicial Administrativa?",
]

DOC_STEPS = [
    ("Fallo o sentencia original", "Documento fuente para comparar las providencias posteriores."),
    ("Constancia de notificación o ejecutoria", "Permite fijar el inicio real de los términos."),
    ("Providencia que fijó el término", "Permite identificar cantidad, unidad y obligación."),
    ("Constancia secretarial", "Permite comprobar vencimiento, respuestas y paso al despacho."),
    ("Consulta actualizada del expediente", "Permite establecer la última actuación oficial."),
    ("Memorial o solicitud pendiente", "Permite identificar qué actuación se pidió."),
    ("Constancia de recepción", "Permite demostrar que el despacho recibió la actuación."),
    ("Documento fuente del error", "Permite confirmar o descartar la inconsistencia."),
    ("Borrador de vigilancia", "Permite revisar la solicitud antes de radicar."),
]


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        (text or "").translate(
            str.maketrans(
                "áéíóúüñÁÉÍÓÚÜÑ",
                "aeiouunAEIOUUN",
            )
        ).lower(),
    ).strip()


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@st.cache_data(show_spinner=False, max_entries=400)
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


def split_fragments(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[.;:!?])\s+|\n+", text or "")
        if len(item.strip()) >= 25
    ]


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
        + "|".join(MONTHS)
        + r")\s+de\s+((?:19|20)\d{2})\b"
    )

    for day, month_name, year in re.findall(pattern, clean):
        try:
            values.append(date(int(year), MONTHS[month_name], int(day)))
        except ValueError:
            pass

    return list(dict.fromkeys(values))


def extract_radications(text: str) -> list[str]:
    values = []
    for pattern in (
        r"\b\d{2}-\d{3}-\d{2}-\d{2}-\d{3}-\d{4}-\d{5}-\d{2}\b",
        r"\b\d{23}\b",
        r"\b20\d{2}-\d{5}\b",
    ):
        values.extend(re.findall(pattern, text or ""))
    return list(dict.fromkeys(values))


def extract_rights(text: str) -> list[str]:
    clean = normalize(text)
    return [
        right
        for right, patterns in RIGHTS.items()
        if any(pattern in clean for pattern in patterns)
    ]


def extract_objects(text: str) -> list[str]:
    clean = normalize(text)
    return [
        item
        for item, patterns in OBJECTS.items()
        if any(pattern in clean for pattern in patterns)
    ]


def source_type(text: str) -> str:
    clean = normalize(text)
    if any(x in clean for x in ("fallo de tutela", "sentencia primera instancia", "r e s u e l v e")):
        return "Fallo o sentencia"
    if any(x in clean for x in ("auto de sustanciacion", "juzgado", "resuelve", "dispone")):
        return "Providencia del despacho"
    if any(x in clean for x in ("solicito", "pretensiones", "apoderado", "memorial", "recurso")):
        return "Escrito de abogado o parte"
    return "Documento por clasificar"


def profile(name: str, pages: list[PageTrace]) -> dict:
    text = "\n".join(page.text or "" for page in pages)
    return {
        "Documento": name,
        "Texto": text,
        "Tipo": source_type(text),
        "Radicados": extract_radications(text),
        "Fechas": extract_dates(text),
        "Derechos": extract_rights(text),
        "Objetos": extract_objects(text),
    }


def find_fragment(text: str, terms: tuple[str, ...]) -> str:
    for fragment in split_fragments(text):
        clean = normalize(fragment)
        if any(term in clean for term in terms):
            return fragment
    return ""


def compare_source(source: dict, target: dict) -> list[dict]:
    rows = []

    target_sentence_fragment = find_fragment(
        target["Texto"],
        ("sentencia de tutela", "fallo de tutela"),
    )
    target_sentence_dates = extract_dates(target_sentence_fragment)

    if source["Fechas"] and target_sentence_dates:
        expected = source["Fechas"][0]
        different = [value for value in target_sentence_dates if value != expected]
        if different:
            rows.append({
                "Documento": target["Documento"],
                "Categoría": "Fecha del fallo",
                "Severidad": "Alta",
                "Dato fuente": expected.strftime("%d/%m/%Y"),
                "Dato posterior": " | ".join(value.strftime("%d/%m/%Y") for value in different),
                "Fragmento fuente": find_fragment(source["Texto"], ("fallo de tutela", "popayan")),
                "Fragmento posterior": target_sentence_fragment,
                "Explicación": "La providencia posterior cambia la fecha del fallo fuente.",
                "Norma o principio": "Constitución Política, artículo 29; exactitud y congruencia.",
            })

    source_rights = set(source["Derechos"])
    target_rights = set(target["Derechos"])

    if source_rights and target_rights and source_rights != target_rights:
        rows.append({
            "Documento": target["Documento"],
            "Categoría": "Derechos tutelados",
            "Severidad": "Alta",
            "Dato fuente": " | ".join(sorted(source_rights)),
            "Dato posterior": " | ".join(sorted(target_rights)),
            "Fragmento fuente": find_fragment(
                source["Texto"],
                ("tutelar los derechos", "derechos fundamentales"),
            ),
            "Fragmento posterior": find_fragment(
                target["Texto"],
                ("concediendo el derecho", "derecho fundamental"),
            ),
            "Explicación": "La providencia posterior modifica o sustituye los derechos protegidos.",
            "Norma o principio": "Constitución Política, artículo 29; fidelidad y motivación.",
        })

    source_objects = set(source["Objetos"])
    target_objects = set(target["Objetos"])

    if source_objects and target_objects and not source_objects.issubset(target_objects):
        rows.append({
            "Documento": target["Documento"],
            "Categoría": "Objeto de la orden",
            "Severidad": "Media",
            "Dato fuente": " | ".join(sorted(source_objects)),
            "Dato posterior": " | ".join(sorted(target_objects)),
            "Fragmento fuente": find_fragment(source["Texto"], ("molde de silicona", "tratamiento integral")),
            "Fragmento posterior": find_fragment(target["Texto"], ("audifonos", "cumplimiento")),
            "Explicación": "La providencia posterior no reproduce completamente el objeto de la orden.",
            "Norma o principio": "Constitución Política, artículo 29; congruencia y cumplimiento exacto.",
        })

    return rows


def detect_errors(item: dict) -> list[dict]:
    rows = []
    clean = normalize(item["Texto"])

    if len(item["Radicados"]) > 1:
        rows.append({
            "Documento": item["Documento"],
            "Categoría": "Identificación",
            "Severidad": "Alta",
            "Hallazgo": "Más de un radicado dentro del archivo",
            "Evidencia": " | ".join(item["Radicados"]),
            "Explicación": "Puede existir mezcla de procesos o una cita que debe justificarse.",
            "Norma o principio": "Constitución Política, artículo 29.",
        })

    if any(x in clean for x in ("no obra prueba", "no se acredito", "no se aporto")):
        if any(x in clean for x in ("anexo", "constancia", "dictamen", "historia clinica", "correo")):
            rows.append({
                "Documento": item["Documento"],
                "Categoría": "Probatorio",
                "Severidad": "Alta",
                "Hallazgo": "Posible omisión de prueba relevante",
                "Evidencia": "El texto niega acreditación y también menciona anexos o soportes.",
                "Explicación": "Debe verificarse si la prueba fue aportada y valorada.",
                "Norma o principio": "Constitución Política, artículo 29.",
            })

    if any(x in clean for x in ("incidente de desacato", "continua el incumplimiento", "cumplimiento del fallo")):
        rows.append({
            "Documento": item["Documento"],
            "Categoría": "Cumplimiento",
            "Severidad": "Alta",
            "Hallazgo": "Cumplimiento de tutela posiblemente insuficiente",
            "Evidencia": find_fragment(item["Texto"], ("incidente de desacato", "incumplimiento", "cumplimiento")),
            "Explicación": "Debe compararse la orden exacta con el cumplimiento material.",
            "Norma o principio": "Decreto 2591 de 1991, artículos 27 y 52.",
        })

    return rows


def detect_terms(item: dict) -> list[dict]:
    rows = []
    pattern = re.compile(
        r"(?:dentro de|por el termino de|termino(?: \w+){0,5} de|plazo(?: \w+){0,5} de)\s+"
        r"(?P<number>\d{1,3})\s*(?P<unit>horas?|dias?)",
        re.IGNORECASE,
    )

    base_date = item["Fechas"][0] if item["Fechas"] else None

    for fragment in split_fragments(item["Texto"]):
        match = pattern.search(normalize(fragment))
        if not match:
            continue

        quantity = int(match.group("number"))
        unit = "Horas" if "hora" in match.group("unit") else "Días"
        deadline = None

        if base_date:
            start = datetime.combine(base_date + timedelta(days=1), datetime.min.time())
            deadline = (
                start + timedelta(hours=quantity)
                if unit == "Horas"
                else start + timedelta(days=quantity)
            )

        rows.append({
            "Documento": item["Documento"],
            "Fragmento": fragment,
            "Cantidad": quantity,
            "Unidad": unit,
            "Fecha base": base_date,
            "Vencimiento estimado": deadline,
            "Estado": "Vencido" if deadline and deadline < datetime.now() else "Por confirmar",
            "Advertencia": "Confirmar notificación, ejecutoria, festivos y norma especial.",
        })

    return rows


def detect_conducts(item: dict) -> list[dict]:
    clean = normalize(item["Texto"])
    rules = [
        ("Mora o inactividad aparente", ("pendiente de decision", "sin resolver", "pase a despacho"), "Ley 270 de 1996, artículos 4 y 7."),
        ("Falta de trámite de memorial", ("memorial de impulso", "solicitud sin respuesta", "no se dio tramite"), "Constitución, artículos 29 y 229."),
        ("Notificación posiblemente incompleta", ("no fue notificado", "sin constancia de notificacion"), "Norma procesal aplicable."),
        ("Seguimiento insuficiente del cumplimiento", ("continua el incumplimiento", "incumplimiento del fallo", "incidente de desacato"), "Decreto 2591 de 1991, artículos 27 y 52."),
    ]

    rows = []
    for name, phrases, norm in rules:
        hits = [phrase for phrase in phrases if phrase in clean]
        if hits:
            rows.append({
                "Documento": item["Documento"],
                "Conducta posible": name,
                "Coincidencias": " | ".join(hits),
                "Norma o marco": norm,
                "Cómo verificar": "Revisar cronología, constancias y estado actual.",
            })
    return rows


def answer_question(question: str, pages: list[PageTrace]) -> dict:
    query_tokens = {
        token
        for token in re.findall(r"\b[a-z0-9]{4,}\b", normalize(question))
        if token not in {"para", "como", "cual", "cuando", "donde", "esta", "este", "debe", "puede"}
    }

    candidates = []
    for page in pages:
        for fragment in split_fragments(page.text):
            clean = normalize(fragment)
            score = sum(token in clean for token in query_tokens)
            if score:
                candidates.append({
                    "Documento": page.document,
                    "Página": page.page,
                    "Fragmento": fragment,
                    "Coincidencias": score,
                })

    candidates.sort(key=lambda item: item["Coincidencias"], reverse=True)
    evidence = candidates[:8]

    if not evidence:
        return {"Respuesta": "No se encontró evidencia suficiente.", "Evidencia": [], "Confianza": 0}

    return {
        "Respuesta": (
            "La evidencia más relacionada indica: "
            + " ".join(item["Fragmento"] for item in evidence[:3])
            + " Debe verificarse con los documentos completos."
        ),
        "Evidencia": evidence,
        "Confianza": min(95, 45 + evidence[0]["Coincidencias"] * 8),
    }


with st.sidebar:
    st.header("OCR")
    enabled = st.checkbox("Aplicar OCR", value=True)
    min_chars = st.slider("Mínimo de caracteres útiles", 20, 300, 80, 10)
    max_pages = st.slider("Máximo de páginas OCR", 5, 250, 100, 5)
    dpi = st.select_slider("Resolución OCR", [150, 200, 220, 250, 300], value=220)


st.subheader("1. Cargar expediente completo")

uploaded_files = st.file_uploader(
    "Carga el fallo, autos, memoriales, constancias, respuestas y demás documentos",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.stop()


documents = {}
all_pages = []
loading_errors = []

with st.spinner("Leyendo y organizando el expediente..."):
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
            pages = [restore(item) for item in raw]
            documents[uploaded.name] = pages
            all_pages.extend(pages)
        except Exception as error:
            loading_errors.append(f"{uploaded.name}: {error}")


if loading_errors:
    st.warning("\n".join(loading_errors))


profiles = [profile(name, pages) for name, pages in documents.items()]


st.subheader("2. Clasificación automática")

classification_df = pd.DataFrame([
    {
        "Documento": item["Documento"],
        "Tipo": item["Tipo"],
        "Radicados": " | ".join(item["Radicados"]),
        "Fechas": " | ".join(value.strftime("%d/%m/%Y") for value in item["Fechas"]),
        "Derechos": " | ".join(item["Derechos"]),
        "Objetos": " | ".join(item["Objetos"]),
    }
    for item in profiles
])

st.dataframe(classification_df, use_container_width=True, hide_index=True)


st.subheader("3. Seleccionar fallo fuente")

fallo_candidates = [item["Documento"] for item in profiles if item["Tipo"] == "Fallo o sentencia"]

source_name = st.selectbox(
    "Escoge el fallo o sentencia que servirá como documento fuente",
    options=fallo_candidates or [item["Documento"] for item in profiles],
)

source_profile = next(item for item in profiles if item["Documento"] == source_name)


st.subheader("4. Comparación fallo–providencias")

comparison_rows = []

for item in profiles:
    if item["Documento"] != source_name:
        comparison_rows.extend(compare_source(source_profile, item))

comparison_df = pd.DataFrame(comparison_rows)

if comparison_df.empty:
    st.success("No se detectaron diferencias claras frente al fallo fuente.")
else:
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)


st.subheader("5. Errores y riesgos por documento")

error_rows = []
for item in profiles:
    error_rows.extend(detect_errors(item))

errors_df = pd.DataFrame(error_rows)

if errors_df.empty:
    st.success("No se detectaron errores claros con las reglas automáticas.")
else:
    st.dataframe(errors_df, use_container_width=True, hide_index=True)


st.subheader("6. Conteo de términos")

term_rows = []
for item in profiles:
    term_rows.extend(detect_terms(item))

terms_df = pd.DataFrame(term_rows)

if terms_df.empty:
    st.warning("No se detectaron términos expresos.")
else:
    st.dataframe(terms_df, use_container_width=True, hide_index=True)


st.subheader("7. Conductas relevantes para Vigilancia Judicial")

conduct_rows = []
for item in profiles:
    conduct_rows.extend(detect_conducts(item))

conducts_df = pd.DataFrame(conduct_rows)

if conducts_df.empty:
    st.warning("No se detectaron conductas claras con las reglas actuales.")
else:
    st.dataframe(conducts_df, use_container_width=True, hide_index=True)


st.subheader("8. Preguntar al expediente")

selected_question = st.selectbox(
    "Selecciona una pregunta relevante",
    ["Escribir otra pregunta"] + QUESTIONS,
)

question = (
    st.text_area("Escribe la pregunta", height=90)
    if selected_question == "Escribir otra pregunta"
    else selected_question
)

if st.button("Responder con evidencia", type="primary", use_container_width=True):
    response = answer_question(question, all_pages)

    st.info(
        f"**Confianza preliminar: {response['Confianza']}%**\n\n"
        f"{response['Respuesta']}"
    )

    if response["Evidencia"]:
        st.dataframe(pd.DataFrame(response["Evidencia"]), use_container_width=True, hide_index=True)


st.subheader("9. Semáforo integral")

expired_count = int((terms_df["Estado"] == "Vencido").sum()) if not terms_df.empty else 0
comparison_score = min(35, len(comparison_df) * 20)
error_score = min(30, len(errors_df) * 15)
term_score = min(20, expired_count * 10)
conduct_score = min(15, len(conducts_df) * 8)
total_score = min(100, comparison_score + error_score + term_score + conduct_score)

score_df = pd.DataFrame([
    {"Componente": "Diferencias frente al fallo", "Puntaje": comparison_score, "Máximo": 35},
    {"Componente": "Errores y riesgos", "Puntaje": error_score, "Máximo": 30},
    {"Componente": "Términos vencidos", "Puntaje": term_score, "Máximo": 20},
    {"Componente": "Conductas de vigilancia", "Puntaje": conduct_score, "Máximo": 15},
])

st.dataframe(score_df, use_container_width=True, hide_index=True)

if total_score >= 65:
    st.error(f"🔴 REVISIÓN PRIORITARIA — {total_score}/100")
elif total_score >= 30:
    st.warning(f"🟡 REQUIERE COMPLETAR Y VERIFICAR — {total_score}/100")
else:
    st.success(f"🟢 SIN INDICIOS SUFICIENTES — {total_score}/100")


st.subheader("10. Actuaciones recomendadas y documentos pendientes")

for index, (document_name, purpose) in enumerate(DOC_STEPS, start=1):
    with st.expander(f"{index}. {document_name}", expanded=index == 1):
        st.markdown(f"**Para qué sirve:** {purpose}")
        step_file = st.file_uploader(
            "Cargar este documento",
            type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
            accept_multiple_files=False,
            key=f"integral_step_{index}",
        )
        if step_file is not None:
            st.success(f"Documento cargado: {step_file.name}")


st.subheader("11. Conclusión integral")

conclusions = []

if not comparison_df.empty:
    conclusions.append("Se detectaron diferencias entre el fallo fuente y providencias posteriores.")
if not errors_df.empty:
    conclusions.append("Existen posibles errores fácticos, probatorios o de litigación.")
if expired_count:
    conclusions.append(f"Se clasificaron {expired_count} término(s) como vencido(s), sujeto(s) a verificación.")
if not conducts_df.empty:
    conclusions.append("Se detectaron conductas relacionadas con mora, trámite, notificación o cumplimiento.")

if conclusions:
    for item in conclusions:
        st.markdown(f"⚠️ {item}")
else:
    st.info("No se encontraron indicios suficientes con los documentos actuales.")


st.subheader("12. Exportar auditoría completa")

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    classification_df.to_excel(writer, sheet_name="Clasificación", index=False)
    comparison_df.to_excel(writer, sheet_name="Comparación fallo", index=False)
    errors_df.to_excel(writer, sheet_name="Errores", index=False)
    terms_df.to_excel(writer, sheet_name="Términos", index=False)
    conducts_df.to_excel(writer, sheet_name="Conductas", index=False)
    score_df.to_excel(writer, sheet_name="Puntaje", index=False)

st.download_button(
    "Descargar auditoría integral en Excel",
    data=output.getvalue(),
    file_name="auditoria_integral_judicial.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)
