from __future__ import annotations

import hashlib
import io
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import PurePosixPath

import pandas as pd
import streamlit as st

from legal_analyzer.document_loader import load_document
from legal_analyzer.models import PageTrace
from legal_analyzer.ocr_engine import OCRConfig


st.set_page_config(
    page_title="Auditor de errores de despachos",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Auditor jurídico de errores de despachos")
st.caption(
    "Revisa cada documento, detecta posibles errores fácticos, procesales, "
    "probatorios y de motivación, y los relaciona con la norma posiblemente comprometida."
)

st.error(
    "El sistema no declara que un juez o despacho haya violado la ley. "
    "Genera hallazgos preliminares que deben comprobarse con el expediente completo, "
    "las constancias de notificación y la norma especial del proceso."
)


NORM_CATALOG = {
    "Identificación incorrecta del proceso": {
        "norma": "Constitución Política, artículo 29",
        "principio": "Debido proceso e identificación cierta de la actuación",
        "uso": "Verificar radicado, partes, despacho y tipo de proceso.",
    },
    "Incongruencia entre motivación y decisión": {
        "norma": "Constitución Política, artículo 29; Ley 270 de 1996, artículo 9",
        "principio": "Debido proceso, respeto de derechos y motivación suficiente",
        "uso": "Comparar consideraciones, problema jurídico y parte resolutiva.",
    },
    "Falta de decisión sobre una solicitud": {
        "norma": "Constitución Política, artículos 29 y 229; Ley 270 de 1996, artículos 4 y 7",
        "principio": "Acceso a la justicia, celeridad y eficiencia",
        "uso": "Comprobar recepción, competencia y término aplicable.",
    },
    "Mora o inactividad aparente": {
        "norma": "Ley 270 de 1996, artículos 4 y 7; Acuerdo PSAA11-8716 de 2011",
        "principio": "Celeridad, eficiencia y oportunidad de la gestión judicial",
        "uso": "Determinar última actuación, término legal y justificación de la demora.",
    },
    "Cómputo dudoso del término": {
        "norma": "Ley 1564 de 2012, artículo 118, o norma especial aplicable",
        "principio": "Cómputo correcto de términos procesales",
        "uso": "Confirmar notificación, ejecutoria, días hábiles y suspensiones.",
    },
    "Notificación posiblemente defectuosa": {
        "norma": "Decreto 2591 de 1991, artículo 16; Ley 2213 de 2022, artículo 8, según el caso",
        "principio": "Publicidad, contradicción y conocimiento efectivo de la providencia",
        "uso": "Verificar canal, destinatario, envío, entrega y constancia.",
    },
    "Omisión de prueba relevante": {
        "norma": "Constitución Política, artículo 29",
        "principio": "Derecho de defensa, contradicción y valoración integral",
        "uso": "Comprobar que la prueba fue aportada, pertinente y decisiva.",
    },
    "Afirmación sin soporte visible": {
        "norma": "Constitución Política, artículo 29; deber de motivación",
        "principio": "Motivación basada en elementos verificables",
        "uso": "Buscar el documento, constancia o prueba que respalde la afirmación.",
    },
    "Confusión de personas, entidades o dispositivos": {
        "norma": "Constitución Política, artículo 29",
        "principio": "Exactitud fáctica y congruencia",
        "uso": "Comparar nombres, cargos, entidades, bienes, medicamentos o dispositivos.",
    },
    "Incumplimiento o seguimiento insuficiente de tutela": {
        "norma": "Decreto 2591 de 1991, artículos 27 y 52",
        "principio": "Cumplimiento efectivo del fallo de tutela",
        "uso": "Verificar orden, obligado, plazo, cumplimiento material y medidas adoptadas.",
    },
    "Decisión por fuera de lo pedido": {
        "norma": "Constitución Política, artículo 29; principio de congruencia",
        "principio": "Correspondencia entre pretensiones, debate y decisión",
        "uso": "Comparar solicitudes, oposición, problema jurídico y resolutivo.",
    },
}


MONTHS = {
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


@st.cache_data(show_spinner=False, max_entries=300)
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


def split_fragments(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(
            r"(?<=[\.\;\:])\s+|\n+",
            text,
        )
        if len(item.strip()) >= 30
    ]


def extract_radications(text: str) -> list[str]:
    patterns = [
        r"\b\d{2}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{3}[-\s]?\d{4}[-\s]?\d{5}[-\s]?\d{2}\b",
        r"\b\d{2}[-]\d{3}[-]\d{2}[-]\d{2}[-]\d{3}[-]\d{4}[-]\d{5}[-]\d{2}\b",
        r"\b\d{23}\b",
    ]

    values = []

    for pattern in patterns:
        values.extend(
            re.findall(
                pattern,
                text,
            )
        )

    return list(dict.fromkeys(values))


def extract_dates(text: str) -> list[date]:
    values = []
    clean = normalize(text)

    for day, month, year in re.findall(
        r"\b([0-3]?\d)[/-]([01]?\d)[/-]((?:19|20)\d{2})\b",
        clean,
    ):
        try:
            values.append(
                date(
                    int(year),
                    int(month),
                    int(day),
                )
            )
        except ValueError:
            pass

    pattern = (
        r"\b([0-3]?\d)\s+de\s+("
        + "|".join(MONTHS.keys())
        + r")\s+de\s+((?:19|20)\d{2})\b"
    )

    for day, month_name, year in re.findall(
        pattern,
        clean,
    ):
        try:
            values.append(
                date(
                    int(year),
                    MONTHS[month_name],
                    int(day),
                )
            )
        except ValueError:
            pass

    return list(dict.fromkeys(values))


def quoted_entities(text: str) -> list[str]:
    """
    Extrae referencias técnicas que suelen revelar confusión fáctica:
    modelos, números de sentencias y nombres entre comillas o paréntesis.
    """
    candidates = []

    candidates.extend(
        re.findall(
            r"\b(?:Phonak|Naida|Sky|Lumity|L\d{2}|UP|EPS|IPS)"
            r"(?:[\wÁÉÍÓÚáéíóúÑñ\-]+|\s+){0,5}",
            text,
            flags=re.IGNORECASE,
        )
    )

    candidates.extend(
        re.findall(
            r"\b(?:Sentencia|Fallo|Auto)\s+(?:No\.?|N\.?º?)?\s*[\w\-\.]+",
            text,
            flags=re.IGNORECASE,
        )
    )

    return [
        re.sub(r"\s+", " ", item).strip(" ,.;:")
        for item in candidates
        if len(item.strip()) >= 4
    ]


def add_finding(
    findings: list[dict],
    document: str,
    page: int | str,
    category: str,
    subtype: str,
    fragment: str,
    explanation: str,
    severity: str,
    confidence: int,
    comparison: str = "",
    evidence_needed: str = "",
):
    norm_info = NORM_CATALOG[subtype]

    findings.append(
        {
            "Documento": document,
            "Página": page,
            "Categoría": category,
            "Posible error": subtype,
            "Severidad": severity,
            "Confianza preliminar": confidence,
            "Fragmento": fragment,
            "Qué podría estar equivocado": explanation,
            "Comparación o contradicción": comparison,
            "Norma posiblemente comprometida": norm_info["norma"],
            "Principio o deber": norm_info["principio"],
            "Cómo verificarlo": norm_info["uso"],
            "Prueba necesaria": evidence_needed,
            "Conclusión revisada": "",
            "Confirmado por revisor": False,
        }
    )


def detect_per_file(
    document: str,
    pages: list[PageTrace],
) -> list[dict]:
    findings: list[dict] = []
    full_text = "\n".join(
        page.text or ""
        for page in pages
    )
    clean = normalize(full_text)

    radications = extract_radications(full_text)

    if len(radications) > 1:
        add_finding(
            findings,
            document,
            "Varias",
            "Fáctico",
            "Identificación incorrecta del proceso",
            " | ".join(radications),
            "El archivo contiene más de un número de radicación. Puede tratarse de una cita válida o de una mezcla de expedientes.",
            "Alta",
            80,
            comparison="Radicados detectados: " + " / ".join(radications),
            evidence_needed="Carátula, consulta oficial del proceso y providencia completa.",
        )

    dates = extract_dates(full_text)

    future_dates = [
        value
        for value in dates
        if value > date.today()
    ]

    if future_dates:
        add_finding(
            findings,
            document,
            "Fáctico",
            "Afirmación sin soporte visible",
            ", ".join(
                value.strftime("%d/%m/%Y")
                for value in future_dates
            ),
            "El documento contiene una fecha posterior al día actual. Puede ser una fecha programada o un error material.",
            "Media",
            70,
            evidence_needed="Original firmado y contexto completo de la fecha.",
        )

    fragments = split_fragments(full_text)

    for index, fragment in enumerate(fragments):
        fragment_clean = normalize(fragment)
        page_number = next(
            (
                page.page
                for page in pages
                if fragment[:80] in (page.text or "")
            ),
            "",
        )

        if any(
            expression in fragment_clean
            for expression in (
                "no obra prueba",
                "no se aporto",
                "no existe prueba",
                "no se acredito",
            )
        ):
            nearby = " ".join(
                fragments[max(0, index - 3): index + 4]
            )
            nearby_clean = normalize(nearby)

            if any(
                evidence_word in nearby_clean
                for evidence_word in (
                    "anexo",
                    "historia clinica",
                    "constancia",
                    "certificacion",
                    "correo",
                    "dictamen",
                    "recibo",
                )
            ):
                add_finding(
                    findings,
                    document,
                    page_number,
                    "Probatorio",
                    "Omisión de prueba relevante",
                    fragment,
                    "La providencia afirma que no existe acreditación, pero en el contexto cercano aparecen referencias a anexos o pruebas. Debe verificarse si fueron realmente aportadas y valoradas.",
                    "Alta",
                    75,
                    evidence_needed="Índice del expediente, anexos y constancia de incorporación.",
                )

        if any(
            expression in fragment_clean
            for expression in (
                "se encuentra a despacho",
                "pendiente de decision",
                "pase a despacho",
                "para decidir",
            )
        ):
            dates_fragment = extract_dates(fragment)

            if dates_fragment:
                oldest = min(dates_fragment)
                elapsed = (date.today() - oldest).days

                if elapsed >= 30:
                    add_finding(
                        findings,
                        document,
                        page_number,
                        "Procesal",
                        "Mora o inactividad aparente",
                        fragment,
                        f"La actuación aparece pendiente de decisión y la fecha detectada tiene aproximadamente {elapsed} días. El dato no prueba por sí solo una mora injustificada.",
                        "Alta" if elapsed >= 90 else "Media",
                        min(95, 55 + elapsed // 10),
                        evidence_needed="Consulta actual del proceso, constancia secretarial y última actuación.",
                    )

        if any(
            expression in fragment_clean
            for expression in (
                "notificar",
                "notificacion",
                "correo electronico",
                "mensaje de datos",
            )
        ) and not any(
            proof in fragment_clean
            for proof in (
                "constancia",
                "acuse",
                "entregado",
                "recibido",
                "fecha de envio",
            )
        ):
            add_finding(
                findings,
                document,
                page_number,
                "Procesal",
                "Notificación posiblemente defectuosa",
                fragment,
                "Se menciona u ordena una notificación, pero el fragmento no muestra constancia de envío, entrega o acceso.",
                "Media",
                55,
                evidence_needed="Constancia de envío, acuse, registro de entrega y correo completo.",
            )

        term_match = re.search(
            r"(?:termino|plazo)[^\.]{0,80}"
            r"(\d{1,3})\s+(dias?|horas?)",
            fragment_clean,
        )

        if term_match and any(
            word in fragment_clean
            for word in (
                "vencido",
                "extemporaneo",
                "fuera de termino",
            )
        ):
            add_finding(
                findings,
                document,
                page_number,
                "Procesal",
                "Cómputo dudoso del término",
                fragment,
                "El archivo califica un término como vencido o extemporáneo. Debe comprobarse la fecha de notificación, la regla de inicio y los días excluidos.",
                "Alta",
                70,
                evidence_needed="Providencia, constancia de notificación, calendario judicial y radicación.",
            )

        if any(
            expression in fragment_clean
            for expression in (
                "se ordena",
                "ordenar",
                "dispone",
            )
        ) and any(
            expression in fragment_clean
            for expression in (
                "sin mas consideraciones",
                "no hay lugar",
                "no procede",
            )
        ):
            add_finding(
                findings,
                document,
                page_number,
                "Motivación",
                "Incongruencia entre motivación y decisión",
                fragment,
                "La transición entre la motivación y la decisión puede ser insuficiente o contradictoria. Debe compararse el razonamiento completo con la parte resolutiva.",
                "Media",
                55,
                evidence_needed="Providencia completa y solicitudes de las partes.",
            )

        if any(
            expression in fragment_clean
            for expression in (
                "cumplimiento del fallo",
                "incidente de desacato",
                "dar cumplimiento",
                "no ha cumplido",
            )
        ) and any(
            expression in clean
            for expression in (
                "continua el incumplimiento",
                "incumplimiento material",
                "no se entrego lo ordenado",
            )
        ):
            add_finding(
                findings,
                document,
                page_number,
                "Cumplimiento",
                "Incumplimiento o seguimiento insuficiente de tutela",
                fragment,
                "El documento muestra que continúa discutiéndose el cumplimiento material del fallo. Debe verificarse si el despacho adoptó medidas eficaces y si individualizó al responsable.",
                "Alta",
                75,
                evidence_needed="Fallo, órdenes posteriores, respuestas de obligados y prueba de cumplimiento material.",
            )

    entities = quoted_entities(full_text)
    entity_counts = Counter(
        normalize(item)
        for item in entities
    )

    technical_entities = [
        item
        for item in entity_counts
        if any(
            token in item
            for token in (
                "phonak",
                "naida",
                "sky",
                "lumity",
            )
        )
    ]

    if len(technical_entities) >= 2:
        add_finding(
            findings,
            document,
            "Varias",
            "Fáctico",
            "Confusión de personas, entidades o dispositivos",
            " / ".join(technical_entities),
            "Se identificaron referencias técnicas diferentes. Puede ser una comparación válida o una confusión sobre el objeto ordenado y el objeto entregado.",
            "Alta",
            85,
            comparison="Referencias detectadas: " + " frente a ".join(technical_entities),
            evidence_needed="Prescripción original, fallo, autorización, ficha técnica y acta de entrega.",
        )

    return findings


def cross_document_findings(
    documents: dict[str, list[PageTrace]],
) -> list[dict]:
    findings = []

    radicado_map: dict[str, list[str]] = defaultdict(list)
    entity_map: dict[str, list[str]] = defaultdict(list)

    for document, pages in documents.items():
        text = "\n".join(
            page.text or ""
            for page in pages
        )

        for radicado in extract_radications(text):
            radicado_map[radicado].append(document)

        for entity in quoted_entities(text):
            normalized = normalize(entity)

            if any(
                token in normalized
                for token in (
                    "phonak",
                    "naida",
                    "sky",
                    "lumity",
                )
            ):
                entity_map[normalized].append(document)

    if len(radicado_map) > 1:
        add_finding(
            findings,
            "Comparación del expediente",
            "Varias",
            "Fáctico",
            "Identificación incorrecta del proceso",
            " | ".join(radicado_map.keys()),
            "Los archivos seleccionados contienen radicados distintos. Puede existir mezcla de expedientes o documentos citados como antecedentes.",
            "Alta",
            85,
            comparison="; ".join(
                f"{radicado}: {', '.join(files)}"
                for radicado, files in radicado_map.items()
            ),
            evidence_needed="Separar los documentos por proceso y confirmar la carátula oficial.",
        )

    if len(entity_map) >= 2:
        add_finding(
            findings,
            "Comparación del expediente",
            "Varias",
            "Fáctico",
            "Confusión de personas, entidades o dispositivos",
            " | ".join(entity_map.keys()),
            "Los documentos usan referencias técnicas diferentes. El sistema no presume cuál es correcta: exige comparar prescripción, orden judicial y cumplimiento.",
            "Alta",
            90,
            comparison="; ".join(
                f"{entity}: {', '.join(files)}"
                for entity, files in entity_map.items()
            ),
            evidence_needed="Documento fuente que define el objeto exacto de la orden.",
        )

    return findings


def viability_color(findings: pd.DataFrame) -> tuple[str, str, int]:
    if findings.empty:
        return (
            "Verde",
            "No se detectaron errores claros con las reglas automáticas",
            15,
        )

    severity_weight = {
        "Alta": 25,
        "Media": 12,
        "Baja": 5,
    }

    score = min(
        100,
        sum(
            severity_weight.get(value, 5)
            for value in findings["Severidad"]
        ),
    )

    confirmed_high = (
        (findings["Severidad"] == "Alta")
        & (findings["Confianza preliminar"] >= 75)
    ).sum()

    if confirmed_high >= 2 or score >= 70:
        return (
            "Rojo",
            "Revisión jurídica prioritaria",
            score,
        )

    if score >= 25:
        return (
            "Amarillo",
            "Hay hallazgos que deben comprobarse",
            score,
        )

    return (
        "Verde",
        "Hallazgos leves o insuficientes",
        score,
    )


with st.sidebar:
    st.header("OCR")
    enabled = st.checkbox("Aplicar OCR", value=True)
    min_chars = st.slider("Mínimo de caracteres útiles", 20, 300, 80, 10)
    max_pages = st.slider("Máximo de páginas OCR por archivo", 5, 150, 50, 5)
    dpi = st.select_slider(
        "Resolución OCR",
        [150, 200, 220, 250, 300],
        value=220,
    )


st.subheader("1. Seleccionar documentos")

uploaded_files = st.file_uploader(
    "Escoge un archivo o varios documentos del expediente",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.stop()


documents: dict[str, list[PageTrace]] = {}
loading_errors = []
progress = st.progress(0)

for index, uploaded in enumerate(uploaded_files, start=1):
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

        documents[uploaded.name] = [
            restore(item)
            for item in raw
        ]
    except Exception as error:
        loading_errors.append(
            f"{uploaded.name}: {error}"
        )
        documents[uploaded.name] = []

    progress.progress(index / len(uploaded_files))


if loading_errors:
    st.warning(
        "Algunos documentos no pudieron leerse completamente:\n\n"
        + "\n".join(loading_errors)
    )


st.subheader("2. Errores detectados en cada archivo")

all_findings = []

for document, pages in documents.items():
    file_findings = detect_per_file(
        document,
        pages,
    )
    all_findings.extend(file_findings)

all_findings.extend(
    cross_document_findings(documents)
)

findings_df = pd.DataFrame(all_findings)

if findings_df.empty:
    st.success(
        "🟢 No se detectaron errores claros con las reglas automáticas. "
        "Esto no demuestra que el expediente esté libre de errores."
    )
    st.stop()


edited = st.data_editor(
    findings_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fragmento": st.column_config.TextColumn(
            "Fragmento",
            width="large",
        ),
        "Qué podría estar equivocado": st.column_config.TextColumn(
            "Qué podría estar equivocado",
            width="large",
        ),
        "Comparación o contradicción": st.column_config.TextColumn(
            "Comparación o contradicción",
            width="large",
        ),
        "Norma posiblemente comprometida": st.column_config.TextColumn(
            "Norma posiblemente comprometida",
            width="large",
        ),
        "Confianza preliminar": st.column_config.ProgressColumn(
            "Confianza preliminar",
            min_value=0,
            max_value=100,
            format="%d",
        ),
        "Severidad": st.column_config.SelectboxColumn(
            "Severidad",
            options=["Alta", "Media", "Baja"],
        ),
        "Confirmado por revisor": st.column_config.CheckboxColumn(
            "Confirmado por revisor",
        ),
        "Conclusión revisada": st.column_config.TextColumn(
            "Conclusión revisada",
            width="large",
        ),
    },
    key="office_error_editor",
)


st.subheader("3. Semáforo de errores")

color, label, score = viability_color(edited)
icon = {
    "Rojo": "🔴",
    "Amarillo": "🟡",
    "Verde": "🟢",
}[color]

if color == "Rojo":
    st.error(
        f"{icon} {label} — puntaje de riesgo documental: {score}/100"
    )
elif color == "Amarillo":
    st.warning(
        f"{icon} {label} — puntaje de riesgo documental: {score}/100"
    )
else:
    st.success(
        f"{icon} {label} — puntaje de riesgo documental: {score}/100"
    )


st.subheader("4. Explicación por hallazgo")

for index, row in edited.iterrows():
    with st.expander(
        f"{index + 1}. {row['Posible error']} — "
        f"{row['Documento']}, página {row['Página']}",
        expanded=index == 0,
    ):
        st.markdown(f"**Categoría:** {row['Categoría']}")
        st.markdown(f"**Fragmento:** {row['Fragmento']}")
        st.markdown(
            f"**Qué podría estar equivocado:** "
            f"{row['Qué podría estar equivocado']}"
        )

        if str(row["Comparación o contradicción"]).strip():
            st.markdown(
                f"**Comparación:** "
                f"{row['Comparación o contradicción']}"
            )

        st.markdown(
            f"**Norma posiblemente comprometida:** "
            f"{row['Norma posiblemente comprometida']}"
        )
        st.markdown(
            f"**Principio o deber:** {row['Principio o deber']}"
        )
        st.markdown(
            f"**Cómo verificarlo:** {row['Cómo verificarlo']}"
        )
        st.markdown(
            f"**Prueba necesaria:** {row['Prueba necesaria']}"
        )


st.subheader("5. Utilidad para Vigilancia Judicial")

high_findings = edited[
    (edited["Severidad"] == "Alta")
    & (
        edited["Posible error"].isin(
            [
                "Mora o inactividad aparente",
                "Falta de decisión sobre una solicitud",
                "Notificación posiblemente defectuosa",
                "Identificación incorrecta del proceso",
            ]
        )
    )
]

if not high_findings.empty:
    st.success(
        "Los hallazgos más útiles para una Vigilancia Judicial son los relacionados "
        "con mora, falta de trámite, identificación del proceso y gestión de notificaciones."
    )
else:
    st.warning(
        "Los errores fácticos, probatorios o de interpretación pueden servir como contexto, "
        "pero la Vigilancia Judicial no reemplaza recursos ni permite corregir el sentido "
        "de una providencia."
    )


st.subheader("6. Exportar matriz")

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    edited.to_excel(
        writer,
        sheet_name="Errores por archivo",
        index=False,
    )

    summary = (
        edited.groupby(
            [
                "Documento",
                "Categoría",
                "Posible error",
                "Severidad",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="Cantidad")
    )

    summary.to_excel(
        writer,
        sheet_name="Resumen",
        index=False,
    )


st.download_button(
    "Descargar auditoría jurídica en Excel",
    data=output.getvalue(),
    file_name="auditoria_errores_despachos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)
