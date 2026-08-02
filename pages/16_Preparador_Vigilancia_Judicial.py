from __future__ import annotations

import hashlib
import io
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import PurePosixPath

import pandas as pd
import streamlit as st
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

from legal_analyzer.case_extractor import (
    build_timeline,
    classify_document,
    extract_case_metadata,
)
from legal_analyzer.document_loader import load_document
from legal_analyzer.models import PageTrace
from legal_analyzer.ocr_engine import OCRConfig

from legal_ui.case_context import apply_prefill
from legal_ui.tool_bridge import render_active_case_banner


st.set_page_config(
    page_title="Preparador de Vigilancia Judicial",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ Preparador de Vigilancia Judicial Administrativa")
st.caption(
    "Analiza varias carpetas o expedientes, identifica posibles demoras "
    "y prepara los PDF para radicar en la plataforma de la Rama Judicial."
)

st.warning(
    "La vigilancia judicial administrativa controla oportunidad y eficacia "
    "en la gestión del despacho. No reemplaza recursos, tutelas, incidentes "
    "ni trámites disciplinarios. Cada conclusión debe revisarse antes de radicar."
)

render_active_case_banner()
apply_prefill(
    {
        "prep_applicant_name": "solicitante",
        "prep_applicant_id": "cliente_documento",
        "prep_applicant_email": "cliente_email",
        "prep_applicant_phone": "cliente_telefono",
        "prep_process_type": "tipo_proceso",
    }
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".eml",
}

ACTION_WORDS = {
    "Fallo": ("fallo", "sentencia", "resuelve"),
    "Auto": ("auto", "dispone", "ordena", "requiere"),
    "Notificación": ("notificacion", "notificado", "correo electronico"),
    "Solicitud": ("solicito", "peticion", "memorial", "incidente"),
    "Respuesta": ("respuesta", "contesta", "informa", "pronunciamiento"),
    "Impulso": ("impulso procesal", "solicitud de decision", "pase al despacho"),
}

DELAY_SIGNALS = (
    "sin respuesta",
    "no se ha resuelto",
    "pendiente de decision",
    "mora",
    "demora",
    "vencido el termino",
    "sin pronunciamiento",
    "no se ha decidido",
)


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


def read_zip(uploaded) -> dict[str, dict[str, bytes]]:
    """
    Devuelve:
    {
        "nombre_carpeta": {
            "archivo.pdf": b"..."
        }
    }
    """
    groups: dict[str, dict[str, bytes]] = defaultdict(dict)

    with zipfile.ZipFile(io.BytesIO(uploaded.getvalue())) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue

            path = PurePosixPath(info.filename)
            suffix = path.suffix.lower()

            if suffix not in ALLOWED_EXTENSIONS:
                continue

            parts = path.parts
            folder = parts[0] if len(parts) > 1 else path.stem
            groups[folder][path.name] = archive.read(info)

    return dict(groups)


def classify_action(text: str) -> str:
    clean = normalize(text)
    scores = {
        label: sum(term in clean for term in terms)
        for label, terms in ACTION_WORDS.items()
    }

    label, score = max(
        scores.items(),
        key=lambda item: item[1],
    )

    return label if score else "Documento"


def extract_dates(text: str) -> list[datetime]:
    values = []

    for day, month, year in re.findall(
        r"\b([0-3]?\d)[/-]([01]?\d)[/-]((?:19|20)\d{2})\b",
        text,
    ):
        try:
            values.append(
                datetime(int(year), int(month), int(day))
            )
        except ValueError:
            pass

    months = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    clean = normalize(text)
    pattern = (
        r"\b([0-3]?\d)\s+de\s+("
        + "|".join(months.keys())
        + r")\s+de\s+((?:19|20)\d{2})\b"
    )

    for day, month_name, year in re.findall(pattern, clean):
        try:
            values.append(
                datetime(
                    int(year),
                    months[month_name],
                    int(day),
                )
            )
        except ValueError:
            pass

    return list(dict.fromkeys(values))


def analyze_case(
    folder_name: str,
    files: dict[str, bytes],
    config: dict,
) -> dict:
    documents: dict[str, list[PageTrace]] = {}
    errors = []

    for name, content in files.items():
        try:
            raw = cached_load(
                name,
                digest(content),
                content,
                config["enabled"],
                config["min_chars"],
                config["max_pages"],
                config["dpi"],
            )
            documents[name] = [restore(item) for item in raw]
        except Exception as error:
            errors.append(f"{name}: {error}")
            documents[name] = []

    metadata = extract_case_metadata(documents)
    timeline = build_timeline(documents)

    action_rows = []
    all_text = []

    for name, pages in documents.items():
        text = "\n".join(page.text for page in pages)
        all_text.append(text)

        dates = extract_dates(text)
        action_rows.append(
            {
                "Carpeta": folder_name,
                "Documento": name,
                "Tipo detectado": classify_action(text),
                "Fecha principal": dates[0] if dates else None,
                "Páginas": len(pages),
                "Vista previa": text[:500],
            }
        )

    full_text = normalize("\n".join(all_text))
    delay_hits = [
        signal
        for signal in DELAY_SIGNALS
        if signal in full_text
    ]

    dated = [
        row
        for row in action_rows
        if row["Fecha principal"] is not None
    ]

    last_action = max(
        dated,
        key=lambda row: row["Fecha principal"],
        default=None,
    )

    days_without_action = None

    if last_action:
        days_without_action = (
            datetime.now().date()
            - last_action["Fecha principal"].date()
        ).days

    score = 0
    reasons = []

    if delay_hits:
        score += min(40, len(delay_hits) * 10)
        reasons.append(
            "El expediente contiene expresiones relacionadas con demora o falta de decisión."
        )

    if days_without_action is not None:
        if days_without_action >= 90:
            score += 40
            reasons.append(
                f"La última fecha documental detectada tiene {days_without_action} días."
            )
        elif days_without_action >= 30:
            score += 20
            reasons.append(
                f"La última fecha documental detectada tiene {days_without_action} días."
            )

    has_request = any(
        row["Tipo detectado"] in {"Solicitud", "Impulso"}
        for row in action_rows
    )
    has_later_answer = any(
        row["Tipo detectado"] in {"Respuesta", "Auto", "Fallo"}
        and last_action
        and row["Fecha principal"]
        and row["Fecha principal"] >= last_action["Fecha principal"]
        for row in action_rows
    )

    if has_request and not has_later_answer:
        score += 25
        reasons.append(
            "Se detectó una solicitud o impulso sin respuesta posterior claramente identificada."
        )

    score = min(100, score)

    if score >= 70:
        level = "Rojo"
        conclusion = "Posible mora o gestión pendiente relevante"
    elif score >= 35:
        level = "Amarillo"
        conclusion = "Requiere revisión antes de radicar"
    else:
        level = "Verde"
        conclusion = "No se observa mora clara con las reglas automáticas"

    return {
        "folder": folder_name,
        "documents": documents,
        "metadata": metadata,
        "timeline": timeline,
        "actions": action_rows,
        "errors": errors,
        "delay_hits": delay_hits,
        "last_action": last_action,
        "days_without_action": days_without_action,
        "score": score,
        "level": level,
        "conclusion": conclusion,
        "reasons": reasons,
    }


def viability_assessment(case: dict) -> dict:
    """
    Evalúa preliminarmente si los documentos permiten sustentar una
    Vigilancia Judicial Administrativa.

    VERDE: hay proceso/despacho identificable, actuación pendiente y señales
    documentales de demora o falta de respuesta.

    AMARILLO: existen indicios, pero faltan documentos o datos esenciales.

    ROJO: no aparece una demora administrativa clara o la pretensión parece
    dirigirse únicamente a controvertir una decisión judicial.
    """
    metadata = case.get("metadata", {})
    actions = case.get("actions", [])
    documents = case.get("documents", {})

    full_text = normalize(
        "\n".join(
            page.text
            for pages in documents.values()
            for page in pages
            if page.text
        )
    )

    positive = 0
    negative = 0
    strengths = []
    weaknesses = []
    missing = []
    cautions = []

    radicado = str(metadata.get("Radicado") or "").strip()
    court = str(metadata.get("Juzgado") or "").strip()

    if radicado:
        positive += 15
        strengths.append("Se identificó el número de radicación.")
    else:
        missing.append("Número completo de radicación del proceso.")

    if court:
        positive += 15
        strengths.append("Se identificó el despacho judicial.")
    else:
        missing.append("Nombre exacto del juzgado o despacho vigilado.")

    request_actions = [
        row
        for row in actions
        if row.get("Tipo detectado") in {"Solicitud", "Impulso"}
    ]

    judicial_actions = [
        row
        for row in actions
        if row.get("Tipo detectado") in {"Auto", "Fallo", "Notificación"}
    ]

    answer_actions = [
        row
        for row in actions
        if row.get("Tipo detectado") == "Respuesta"
    ]

    if request_actions:
        positive += 15
        strengths.append(
            "Se detectaron solicitudes, memoriales o actuaciones de impulso."
        )
    else:
        missing.append(
            "Memorial, solicitud o actuación cuya falta de trámite se cuestiona."
        )

    if judicial_actions:
        positive += 10
        strengths.append(
            "Hay providencias o actuaciones judiciales que permiten reconstruir el trámite."
        )
    else:
        missing.append(
            "Providencias, constancias o consultas del expediente que muestren su estado."
        )

    delay_hits = case.get("delay_hits", [])

    if delay_hits:
        positive += min(20, len(delay_hits) * 5)
        strengths.append(
            "Los documentos contienen expresiones relacionadas con demora, "
            "falta de decisión o término vencido."
        )

    days_without_action = case.get("days_without_action")

    if days_without_action is not None:
        if days_without_action >= 90:
            positive += 25
            strengths.append(
                f"Han transcurrido aproximadamente {days_without_action} días "
                "desde la última fecha documental detectada."
            )
        elif days_without_action >= 30:
            positive += 15
            strengths.append(
                f"Han transcurrido aproximadamente {days_without_action} días "
                "desde la última fecha documental detectada."
            )
        elif days_without_action >= 10:
            positive += 5
            cautions.append(
                f"Solo se detectan aproximadamente {days_without_action} días "
                "desde la última actuación; debe verificarse el término aplicable."
            )
        else:
            negative += 15
            weaknesses.append(
                "La última actuación parece reciente; no se observa todavía una demora clara."
            )
    else:
        missing.append(
            "Fecha comprobable de la última actuación o de la solicitud pendiente."
        )

    if request_actions and not answer_actions:
        positive += 15
        strengths.append(
            "No se detectó una respuesta posterior claramente identificada."
        )

    challenge_signals = (
        "revocar la sentencia",
        "revocar el fallo",
        "cambiar la decision",
        "modificar la sentencia",
        "desacuerdo con la decision",
        "el juez decidio mal",
        "valoracion probatoria equivocada",
        "revisar el fondo de la decision",
    )

    found_challenges = [
        signal
        for signal in challenge_signals
        if signal in full_text
    ]

    if found_challenges:
        negative += 35
        weaknesses.append(
            "La pretensión parece dirigirse a controvertir el contenido de una "
            "decisión judicial. La vigilancia no sustituye recursos ni permite "
            "ordenar cómo debe decidir el juez."
        )

    non_judicial_signals = (
        "fiscalia general de la nacion",
        "procuraduria general",
        "contraloria",
        "inspeccion de policia",
        "entidad administrativa",
    )

    if any(signal in full_text for signal in non_judicial_signals) and not court:
        negative += 25
        weaknesses.append(
            "No está claro que la autoridad cuestionada sea un despacho judicial "
            "sometido a la competencia del Consejo Seccional."
        )

    useful_docs = sum(
        1
        for pages in documents.values()
        if pages and any((page.text or "").strip() for page in pages)
    )

    if useful_docs >= 3:
        positive += 10
        strengths.append(
            f"Se pudieron leer {useful_docs} documentos con contenido útil."
        )
    elif useful_docs == 0:
        negative += 30
        weaknesses.append(
            "No se pudo leer contenido útil de los documentos."
        )
    else:
        missing.append(
            "Más soportes documentales para reconstruir el trámite completo."
        )

    score = max(0, min(100, positive - negative))

    essential_missing = (
        not radicado
        or not court
        or not request_actions
        or days_without_action is None
    )

    if score >= 60 and not essential_missing and not found_challenges:
        color = "Verde"
        label = "VIABLE PRELIMINARMENTE"
        recommendation = (
            "La documentación permite preparar una solicitud de Vigilancia Judicial "
            "Administrativa por posible demora o falta de gestión. Antes de radicar, "
            "confirma la última actuación, la fecha de la solicitud pendiente y que "
            "la petición no pretenda modificar el contenido de una decisión judicial."
        )
    elif score >= 25:
        color = "Amarillo"
        label = "VIABILIDAD CONDICIONADA"
        recommendation = (
            "Existen indicios, pero la solicitud no debería radicarse todavía sin "
            "completar los datos o soportes faltantes. Reúne las constancias indicadas "
            "y vuelve a ejecutar el análisis."
        )
    else:
        color = "Rojo"
        label = "NO VIABLE CON LOS DOCUMENTOS ACTUALES"
        recommendation = (
            "Con la documentación disponible no aparece suficientemente acreditada "
            "una demora atribuible al despacho, o la inconformidad corresponde a un "
            "asunto que debe tramitarse mediante recursos u otra actuación judicial."
        )

    next_steps = []

    if color == "Verde":
        next_steps = [
            "Verificar el estado actual del proceso en la consulta oficial.",
            "Adjuntar la solicitud o memorial pendiente y su constancia de recepción.",
            "Adjuntar la última providencia o actuación del despacho.",
            "Explicar qué actuación concreta sigue pendiente y desde cuándo.",
            "Radicar la solicitud en el Consejo Seccional competente.",
        ]
    elif color == "Amarillo":
        next_steps = [
            f"Conseguir: {item}"
            for item in missing
        ] or [
            "Revisar manualmente la cronología y completar la prueba de la demora."
        ]
    else:
        next_steps = [
            "Identificar si corresponde interponer un recurso, solicitar cumplimiento, "
            "promover un incidente o presentar otra actuación procesal.",
            "No usar la vigilancia únicamente para cuestionar el sentido de una decisión.",
        ]

    return {
        "Semáforo de viabilidad": color,
        "Resultado": label,
        "Puntaje de viabilidad": score,
        "Fortalezas": strengths,
        "Debilidades": weaknesses,
        "Documentos o datos faltantes": missing,
        "Precauciones": cautions,
        "Recomendación": recommendation,
        "Actuaciones siguientes": next_steps,
    }

def portal_description(case: dict) -> str:
    metadata = case["metadata"]
    last_action = case["last_action"]

    last_text = (
        f"La última actuación documental identificada corresponde a "
        f"{last_action['Documento']} de fecha "
        f"{last_action['Fecha principal']:%d/%m/%Y}."
        if last_action
        else "No fue posible establecer automáticamente la última actuación."
    )

    reasons = " ".join(case["reasons"]) or (
        "La revisión automática no identificó una razón concluyente; "
        "se requiere revisión humana."
    )

    return (
        f"Solicito vigilancia judicial administrativa respecto del proceso "
        f"{metadata.get('Radicado') or 'RADICADO POR COMPLETAR'}, a cargo de "
        f"{metadata.get('Juzgado') or 'DESPACHO POR COMPLETAR'}. "
        f"{last_text} {reasons} "
        "Solicito verificar la oportunidad y eficacia de la gestión del despacho, "
        "establecer el estado actual de la actuación pendiente y adoptar las medidas "
        "administrativas que correspondan para superar una eventual demora injustificada."
    )


def build_request_pdf(
    case: dict,
    applicant: dict,
    reviewed_description: str,
) -> bytes:
    output = io.BytesIO()
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCenter",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
    )

    normal = styles["BodyText"]
    normal.fontName = "Helvetica"
    normal.fontSize = 10
    normal.leading = 14

    doc = SimpleDocTemplate(
        output,
        pagesize=LETTER,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    metadata = case["metadata"]

    story = [
        Paragraph(
            "SOLICITUD DE VIGILANCIA JUDICIAL ADMINISTRATIVA",
            title_style,
        ),
        Spacer(1, 18),
        Paragraph(
            f"<b>Solicitante:</b> {applicant.get('name', '')}",
            normal,
        ),
        Paragraph(
            f"<b>Identificación:</b> {applicant.get('id', '')}",
            normal,
        ),
        Paragraph(
            f"<b>Correo:</b> {applicant.get('email', '')}",
            normal,
        ),
        Paragraph(
            f"<b>Teléfono:</b> {applicant.get('phone', '')}",
            normal,
        ),
        Spacer(1, 12),
        Paragraph(
            f"<b>Radicado del proceso:</b> {metadata.get('Radicado') or 'Por completar'}",
            normal,
        ),
        Paragraph(
            f"<b>Despacho:</b> {metadata.get('Juzgado') or 'Por completar'}",
            normal,
        ),
        Paragraph(
            f"<b>Accionante/Demandante:</b> {metadata.get('Accionante') or 'Por completar'}",
            normal,
        ),
        Paragraph(
            f"<b>Accionado/Demandado:</b> {metadata.get('Accionado') or 'Por completar'}",
            normal,
        ),
        Spacer(1, 14),
        Paragraph("<b>HECHOS Y DESCRIPCIÓN DE LA SOLICITUD</b>", normal),
        Spacer(1, 8),
        Paragraph(
            reviewed_description.replace("\n", "<br/>"),
            normal,
        ),
        Spacer(1, 14),
        Paragraph(
            "<b>SOLICITUD</b>",
            normal,
        ),
        Paragraph(
            "Solicito verificar la oportunidad y eficacia de la gestión judicial, "
            "establecer el estado actual del proceso y adoptar las medidas administrativas "
            "procedentes dentro de la competencia del Consejo Seccional de la Judicatura.",
            normal,
        ),
        Spacer(1, 20),
        Paragraph(
            "Firma: ______________________________",
            normal,
        ),
    ]

    doc.build(story)
    return output.getvalue()


def build_annex_index_pdf(case: dict) -> bytes:
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    normal.fontSize = 9

    doc = SimpleDocTemplate(
        output,
        pagesize=LETTER,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    story = [
        Paragraph(
            "ÍNDICE DE ANEXOS — VIGILANCIA JUDICIAL ADMINISTRATIVA",
            styles["Title"],
        ),
        Spacer(1, 12),
    ]

    rows = [["N.º", "Documento", "Tipo", "Fecha", "Páginas"]]

    for index, action in enumerate(case["actions"], start=1):
        date_value = (
            action["Fecha principal"].strftime("%d/%m/%Y")
            if action["Fecha principal"]
            else ""
        )

        rows.append(
            [
                str(index),
                action["Documento"],
                action["Tipo detectado"],
                date_value,
                str(action["Páginas"]),
            ]
        )

    table = Table(
        rows,
        colWidths=[1 * cm, 8.5 * cm, 3.5 * cm, 2.5 * cm, 1.5 * cm],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(table)
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Observación: este índice no sustituye los documentos originales. "
            "Adjunte únicamente piezas pertinentes y legibles.",
            normal,
        )
    )

    doc.build(story)
    return output.getvalue()


with st.sidebar:
    st.header("OCR")
    enabled = st.checkbox("Aplicar OCR", value=True)
    min_chars = st.slider("Mínimo de caracteres útiles", 20, 300, 80, 10)
    max_pages = st.slider("Máximo de páginas OCR por archivo", 5, 100, 40, 5)
    dpi = st.select_slider(
        "Resolución OCR",
        [150, 200, 220, 250, 300],
        value=220,
    )


st.subheader("1. Escoger una carpeta completa o archivos individuales")

upload_mode = st.radio(
    "¿Qué deseas seleccionar?",
    options=[
        "Carpeta completa",
        "Archivo individual o varios archivos",
    ],
    horizontal=True,
)

groups: dict[str, dict[str, bytes]] = defaultdict(dict)


if upload_mode == "Carpeta completa":
    st.info(
        "Pulsa «Examinar archivos», abre la carpeta, presiona Ctrl + A y luego pulsa Abrir. "
        "La aplicación cargará automáticamente los archivos compatibles "
        "que estén dentro de esa carpeta y sus subcarpetas."
    )

    st.warning(
        "Modo compatible activado: el navegador no está completando correctamente "
        "la carga directa de carpetas. Pulsa «Examinar archivos», entra en la carpeta, "
        "presiona Ctrl + A para seleccionar todos los documentos y luego pulsa Abrir."
    )

    folder_files = st.file_uploader(
        "Seleccionar todos los archivos de la carpeta",
        type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
        accept_multiple_files=True,
        key="vigilancia_folder_uploader_compatible",
        help=(
            "En Windows: abre la carpeta, presiona Ctrl + A y luego Abrir. "
            "Esto carga todos los documentos sin usar el modo directorio."
        ),
    )

    if not folder_files:
        st.stop()

    total_bytes = sum(
        uploaded.size
        for uploaded in folder_files
    )
    total_mb = total_bytes / (1024 * 1024)

    st.success(
        f"Se seleccionaron {len(folder_files)} archivo(s), "
        f"con un tamaño total aproximado de {total_mb:.1f} MB."
    )

    if total_mb > 900:
        st.error(
            "La carpeta supera aproximadamente 900 MB. "
            "Divídela en dos cargas para evitar que el navegador interrumpa el envío."
        )
        st.stop()

    invalid_files = [
        uploaded.name
        for uploaded in folder_files
        if uploaded.size == 0
    ]

    if invalid_files:
        st.warning(
            "Algunos archivos llegaron vacíos o no pudieron cargarse: "
            + ", ".join(invalid_files[:10])
        )

    folder_files = [
        uploaded
        for uploaded in folder_files
        if uploaded.size > 0
    ]

    if not folder_files:
        st.error(
            "Ningún archivo pudo cargarse correctamente."
        )
        st.stop()

    folder_rows = []

    for index, uploaded in enumerate(folder_files, start=1):
        normalized_path = uploaded.name.replace("\\", "/")
        path = PurePosixPath(normalized_path)
        parts = path.parts

        expediente = "Carpeta seleccionada"
        relative_name = path.name

        folder_rows.append(
            {
                "Usar": True,
                "Ruta dentro de la carpeta": normalized_path,
                "Documento": path.name,
                "Expediente o carpeta": expediente,
                "Orden": index,
            }
        )

    st.markdown("### Archivos encontrados en la carpeta")

    folder_df = st.data_editor(
        pd.DataFrame(folder_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Usar": st.column_config.CheckboxColumn("Usar"),
            "Ruta dentro de la carpeta": st.column_config.TextColumn(
                "Ruta dentro de la carpeta",
                disabled=True,
                width="large",
            ),
            "Documento": st.column_config.TextColumn(
                "Documento",
                disabled=True,
                width="large",
            ),
            "Expediente o carpeta": st.column_config.TextColumn(
                "Expediente o carpeta",
                width="large",
                required=True,
            ),
            "Orden": st.column_config.NumberColumn(
                "Orden",
                min_value=1,
                step=1,
            ),
        },
        key="folder_organization",
    )

    uploaded_by_path = {
        uploaded.name.replace("\\", "/"): uploaded
        for uploaded in folder_files
    }

    for _, row in folder_df.iterrows():
        if not bool(row["Usar"]):
            continue

        upload_path = str(row["Ruta dentro de la carpeta"])
        expediente = str(row["Expediente o carpeta"]).strip()

        if not expediente:
            expediente = "Carpeta seleccionada"

        uploaded = uploaded_by_path.get(upload_path)

        if uploaded is None:
            continue

        document_key = upload_path

        # Evita reemplazar archivos con el mismo nombre.
        if document_key in groups[expediente]:
            document_key = (
                f"{row['Orden']}_{PurePosixPath(upload_path).name}"
            )

        groups[expediente][document_key] = uploaded.getvalue()


else:
    st.info(
        "Selecciona un archivo, o mantén presionada la tecla Ctrl "
        "para escoger varios archivos."
    )

    uploaded_files = st.file_uploader(
        "Seleccionar archivo individual o varios archivos",
        type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
        accept_multiple_files=True,
        key="vigilancia_individual_uploader",
    )

    if not uploaded_files:
        st.stop()

    file_rows = []

    for index, uploaded in enumerate(uploaded_files, start=1):
        file_rows.append(
            {
                "Usar": True,
                "Documento": uploaded.name,
                "Expediente o carpeta": "Expediente 1",
                "Orden": index,
            }
        )

    st.markdown("### Organizar archivos por expediente")

    st.caption(
        "Escribe el mismo nombre en «Expediente o carpeta» para todos "
        "los archivos que pertenezcan al mismo proceso."
    )

    organization_df = st.data_editor(
        pd.DataFrame(file_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Usar": st.column_config.CheckboxColumn("Usar"),
            "Documento": st.column_config.TextColumn(
                "Documento",
                disabled=True,
                width="large",
            ),
            "Expediente o carpeta": st.column_config.TextColumn(
                "Expediente o carpeta",
                width="large",
                required=True,
            ),
            "Orden": st.column_config.NumberColumn(
                "Orden",
                min_value=1,
                step=1,
            ),
        },
        key="individual_organization",
    )

    uploaded_by_name = {
        uploaded.name: uploaded
        for uploaded in uploaded_files
    }

    for _, row in organization_df.iterrows():
        if not bool(row["Usar"]):
            continue

        document_name = str(row["Documento"])
        expediente = str(row["Expediente o carpeta"]).strip()

        if not expediente:
            expediente = "Sin clasificar"

        uploaded = uploaded_by_name.get(document_name)

        if uploaded is None:
            continue

        document_key = document_name

        if document_key in groups[expediente]:
            document_key = f"{row['Orden']}_{document_name}"

        groups[expediente][document_key] = uploaded.getvalue()


if not groups:
    st.error(
        "No hay documentos seleccionados para analizar."
    )
    st.stop()


total_documents = sum(
    len(files)
    for files in groups.values()
)

st.success(
    f"Se seleccionaron {total_documents} documento(s) "
    f"en {len(groups)} expediente(s) o carpeta(s)."
)


config = {
    "enabled": enabled,
    "min_chars": min_chars,
    "max_pages": max_pages,
    "dpi": dpi,
}

analyses = []
progress = st.progress(0)
message = st.empty()

for index, (folder, files) in enumerate(groups.items()):
    message.info(f"Analizando carpeta: {folder}")
    analyses.append(
        analyze_case(
            folder,
            files,
            config,
        )
    )
    progress.progress((index + 1) / len(groups))

message.empty()


st.info(
    "Puedes volver arriba y cambiar el nombre de «Expediente o carpeta». "
    "La aplicación volverá a agrupar y analizar los documentos automáticamente."
)

st.subheader("2. Resultado comparativo")

summary_rows = []

for case in analyses:
    metadata = case["metadata"]
    last_action = case["last_action"]
    viability = viability_assessment(case)
    case["viability"] = viability

    summary_rows.append(
        {
            "Carpeta": case["folder"],
            "Radicado": metadata.get("Radicado", ""),
            "Despacho": metadata.get("Juzgado", ""),
            "Documentos": len(case["actions"]),
            "Última actuación": (
                last_action["Documento"]
                if last_action
                else ""
            ),
            "Fecha última actuación": (
                last_action["Fecha principal"]
                if last_action
                else None
            ),
            "Días desde última fecha": case["days_without_action"],
            "Semáforo": case["level"],
            "Puntaje": case["score"],
            "Semáforo de viabilidad": viability["Semáforo de viabilidad"],
            "Viabilidad": viability["Resultado"],
            "Puntaje de viabilidad": viability["Puntaje de viabilidad"],
            "Conclusión técnica": case["conclusion"],
            "Recomendación": viability["Recomendación"],
            "Razones": " | ".join(case["reasons"]),
        }
    )

summary_df = pd.DataFrame(summary_rows)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
)


st.subheader("3. Semáforo de viabilidad por expediente")

selected_viability_folder = st.selectbox(
    "Selecciona un expediente para ver por qué es viable o no",
    options=[case["folder"] for case in analyses],
    key="viability_folder",
)

viability_case = next(
    case
    for case in analyses
    if case["folder"] == selected_viability_folder
)

assessment = viability_case["viability"]

icon = {
    "Verde": "🟢",
    "Amarillo": "🟡",
    "Rojo": "🔴",
}.get(
    assessment["Semáforo de viabilidad"],
    "⚪",
)

if assessment["Semáforo de viabilidad"] == "Verde":
    st.success(
        f"{icon} {assessment['Resultado']} — "
        f"{assessment['Puntaje de viabilidad']}/100"
    )
elif assessment["Semáforo de viabilidad"] == "Amarillo":
    st.warning(
        f"{icon} {assessment['Resultado']} — "
        f"{assessment['Puntaje de viabilidad']}/100"
    )
else:
    st.error(
        f"{icon} {assessment['Resultado']} — "
        f"{assessment['Puntaje de viabilidad']}/100"
    )

st.markdown(f"**Recomendación:** {assessment['Recomendación']}")

v1, v2 = st.columns(2)

with v1:
    st.markdown("#### Fortalezas documentales")

    if assessment["Fortalezas"]:
        for item in assessment["Fortalezas"]:
            st.markdown(f"✅ {item}")
    else:
        st.caption("No se identificaron fortalezas suficientes.")

    st.markdown("#### Precauciones")

    if assessment["Precauciones"]:
        for item in assessment["Precauciones"]:
            st.markdown(f"⚠️ {item}")
    else:
        st.caption("No se identificaron precauciones adicionales.")

with v2:
    st.markdown("#### Debilidades")

    if assessment["Debilidades"]:
        for item in assessment["Debilidades"]:
            st.markdown(f"❌ {item}")
    else:
        st.caption("No se identificaron debilidades importantes.")

    st.markdown("#### Documentos o datos faltantes")

    if assessment["Documentos o datos faltantes"]:
        for item in assessment["Documentos o datos faltantes"]:
            st.markdown(f"📎 {item}")
    else:
        st.caption("No se detectaron faltantes esenciales.")

st.markdown("#### Actuación recomendada")

for number, item in enumerate(
    assessment["Actuaciones siguientes"],
    start=1,
):
    st.markdown(f"{number}. {item}")

st.info(
    "El semáforo evalúa la suficiencia documental y la posible existencia "
    "de demora. No predice la decisión del Consejo Seccional ni declara "
    "responsabilidad disciplinaria."
)


st.subheader("4. Preparar solicitud para el portal")

selected_folder = st.selectbox(
    "Selecciona el expediente que deseas radicar",
    options=[case["folder"] for case in analyses],
)

selected_case = next(
    case
    for case in analyses
    if case["folder"] == selected_folder
)

c1, c2 = st.columns(2)

with c1:
    applicant_name = st.text_input("Nombres y apellidos", key="prep_applicant_name")
    applicant_id = st.text_input("Número de identificación", key="prep_applicant_id")
    applicant_email = st.text_input("Correo electrónico", key="prep_applicant_email")

with c2:
    applicant_phone = st.text_input("Teléfono", key="prep_applicant_phone")
    applicant_quality = st.selectbox(
        "Calidad",
        [
            "Demandante – Accionante",
            "Demandado – Accionado",
            "Apoderado",
            "Otro",
        ],
    )
    process_type = st.text_input("Tipo de proceso", key="prep_process_type")

description = st.text_area(
    "Descripción para copiar en el portal",
    value=portal_description(selected_case),
    height=260,
)

st.markdown("### Datos que debes completar en la plataforma")

portal_fields = pd.DataFrame(
    [
        {
            "Campo": "Consejo Seccional",
            "Valor sugerido": "Seleccionar según ubicación del despacho",
        },
        {
            "Campo": "Especialidad",
            "Valor sugerido": "Confirmar según el juzgado",
        },
        {
            "Campo": "Juzgado/Despacho",
            "Valor sugerido": selected_case["metadata"].get("Juzgado", ""),
        },
        {
            "Campo": "Número de proceso",
            "Valor sugerido": re.sub(
                r"\D",
                "",
                selected_case["metadata"].get("Radicado", ""),
            ),
        },
        {
            "Campo": "Tipo de proceso",
            "Valor sugerido": process_type,
        },
        {
            "Campo": "Partes",
            "Valor sugerido": (
                f"{selected_case['metadata'].get('Accionante', '')} / "
                f"{selected_case['metadata'].get('Accionado', '')}"
            ),
        },
        {
            "Campo": "Hecho generador",
            "Valor sugerido": "Mora o demora en actuación judicial — confirmar en lista",
        },
    ]
)

st.data_editor(
    portal_fields,
    use_container_width=True,
    hide_index=True,
    key="portal_fields",
)


st.subheader("5. Descargar los dos PDF")

applicant = {
    "name": applicant_name,
    "id": applicant_id,
    "email": applicant_email,
    "phone": applicant_phone,
    "quality": applicant_quality,
}

request_pdf = build_request_pdf(
    selected_case,
    applicant,
    description,
)

annex_pdf = build_annex_index_pdf(
    selected_case
)

d1, d2 = st.columns(2)

with d1:
    st.download_button(
        "Descargar PDF de solicitud",
        data=request_pdf,
        file_name="solicitud_vigilancia_judicial.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )

with d2:
    st.download_button(
        "Descargar PDF índice de anexos",
        data=annex_pdf,
        file_name="indice_anexos_vigilancia.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


st.subheader("6. Exportar análisis de todas las carpetas")

excel = io.BytesIO()

with pd.ExcelWriter(excel, engine="openpyxl") as writer:
    summary_df.to_excel(
        writer,
        sheet_name="Resumen expedientes",
        index=False,
    )

    viability_export = pd.DataFrame(
        [
            {
                "Carpeta": case["folder"],
                "Semáforo": case["viability"]["Semáforo de viabilidad"],
                "Resultado": case["viability"]["Resultado"],
                "Puntaje": case["viability"]["Puntaje de viabilidad"],
                "Fortalezas": " | ".join(case["viability"]["Fortalezas"]),
                "Debilidades": " | ".join(case["viability"]["Debilidades"]),
                "Faltantes": " | ".join(
                    case["viability"]["Documentos o datos faltantes"]
                ),
                "Recomendación": case["viability"]["Recomendación"],
                "Actuación siguiente": " | ".join(
                    case["viability"]["Actuaciones siguientes"]
                ),
            }
            for case in analyses
        ]
    )

    viability_export.to_excel(
        writer,
        sheet_name="Viabilidad",
        index=False,
    )

    for index, case in enumerate(analyses, start=1):
        sheet = f"Expediente {index}"[:31]
        pd.DataFrame(case["actions"]).to_excel(
            writer,
            sheet_name=sheet,
            index=False,
        )

st.download_button(
    "Descargar auditoría completa en Excel",
    data=excel.getvalue(),
    file_name="auditoria_vigilancia_judicial.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

st.warning(
    "La plataforma oficial exige revisar y completar los datos del solicitante, "
    "despacho, proceso, partes, hecho generador y descripción. "
    "El envío debe realizarlo personalmente el usuario en el portal oficial."
)





