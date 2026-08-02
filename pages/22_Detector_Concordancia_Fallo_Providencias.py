from __future__ import annotations

import hashlib
import io
import re
from collections import defaultdict
from datetime import date

import pandas as pd
import streamlit as st

from legal_analyzer.document_loader import load_document
from legal_analyzer.models import PageTrace
from legal_analyzer.ocr_engine import OCRConfig


st.set_page_config(
    page_title="Detector de Concordancia Judicial",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ Detector de Concordancia entre Fallos y Providencias")
st.caption(
    "Compara el fallo fuente con autos posteriores y detecta cambios de fecha, "
    "derechos tutelados, radicado, partes, objeto de la orden y contenido resolutivo."
)

st.error(
    "El sistema identifica inconsistencias documentales preliminares. "
    "El usuario debe verificar el texto completo, la versión firmada y el contexto procesal."
)


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

RIGHT_PATTERNS = {
    "salud": ("derecho a la salud", "derecho fundamental a la salud"),
    "vida en condiciones dignas": (
        "vida en condiciones dignas",
        "vida digna",
    ),
    "educación": (
        "derecho a la educacion",
        "derecho fundamental de educacion",
    ),
    "libre circulación": (
        "libre circulacion",
        "derecho a la libre circulacion",
    ),
    "dignidad humana": (
        "dignidad humana",
        "derecho a la dignidad",
    ),
    "igualdad": (
        "derecho a la igualdad",
        "igualdad material",
    ),
}

OBJECT_PATTERNS = {
    "molde de silicona blanda intracanal": (
        "molde de silicona blanda intracanal",
        "molde de silicona",
    ),
    "audífono Naída P90": (
        "naida p90",
        "audifono naida p90",
    ),
    "pilas tipo 675": (
        "pilas tipo 675",
        "pila tipo 675",
    ),
    "tratamiento integral": (
        "tratamiento integral",
    ),
}


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


@st.cache_data(show_spinner=False, max_entries=200)
def cached_load(name, content_hash, content, enabled, min_chars, max_pages, dpi):
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


def extract_text(pages: list[PageTrace]) -> str:
    return "\n".join(page.text or "" for page in pages)


def extract_radications(text: str) -> list[str]:
    values = []

    for pattern in (
        r"\b\d{2}-\d{3}-\d{2}-\d{2}-\d{3}-\d{4}-\d{5}-\d{2}\b",
        r"\b\d{23}\b",
        r"\b20\d{2}-\d{5}\b",
    ):
        values.extend(re.findall(pattern, text or ""))

    return list(dict.fromkeys(values))


def extract_decision_numbers(text: str) -> list[str]:
    clean = normalize(text)
    values = []

    patterns = (
        r"(?:fallo|sentencia)\s+de\s+tutela\s*(?:n[o°º.]*)?\s*(\d{1,5})",
        r"fallo\s+de\s+tutela\s*(?:n[o°º.]*)?\s*(\d{1,5})",
        r"sentencia\s*(?:n[o°º.]*)?\s*(\d{1,5})",
    )

    for pattern in patterns:
        values.extend(re.findall(pattern, clean))

    return list(dict.fromkeys(values))


def extract_dates(text: str) -> list[date]:
    clean = normalize(text)
    values = []

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

    for day, month_name, year in re.findall(pattern, clean):
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

    judicial = (
        r"\(([0-3]?\d)\)\s+de\s+("
        + "|".join(MONTHS.keys())
        + r")\s+de\s+[^()\n]{0,100}\(((?:19|20)\d{2})\)"
    )

    for day, month_name, year in re.findall(judicial, clean):
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


def extract_rights(text: str) -> list[str]:
    clean = normalize(text)
    found = []

    for right, patterns in RIGHT_PATTERNS.items():
        if any(pattern in clean for pattern in patterns):
            found.append(right)

    return found


def extract_objects(text: str) -> list[str]:
    clean = normalize(text)
    found = []

    for item, patterns in OBJECT_PATTERNS.items():
        if any(pattern in clean for pattern in patterns):
            found.append(item)

    return found


def find_fragment(text: str, terms: tuple[str, ...]) -> str:
    fragments = [
        item.strip()
        for item in re.split(r"(?<=[.;:])\s+|\n+", text or "")
        if len(item.strip()) >= 25
    ]

    for fragment in fragments:
        clean = normalize(fragment)

        if any(term in clean for term in terms):
            return fragment

    return ""


def build_profile(name: str, pages: list[PageTrace]) -> dict:
    text = extract_text(pages)
    clean = normalize(text)

    return {
        "Documento": name,
        "Texto": text,
        "Radicados": extract_radications(text),
        "Números de fallo": extract_decision_numbers(text),
        "Fechas": extract_dates(text),
        "Derechos": extract_rights(text),
        "Objetos": extract_objects(text),
        "Es fallo fuente": any(
            phrase in clean
            for phrase in (
                "fallo de tutela",
                "sentencia primera instancia",
                "r e s u e l v e",
            )
        ),
    }


def add_issue(
    rows: list[dict],
    category: str,
    severity: str,
    source_value,
    compared_value,
    source_document: str,
    compared_document: str,
    explanation: str,
    source_fragment: str,
    compared_fragment: str,
    norm: str,
):
    rows.append(
        {
            "Categoría": category,
            "Severidad": severity,
            "Documento fuente": source_document,
            "Documento comparado": compared_document,
            "Dato correcto según fuente": source_value,
            "Dato encontrado después": compared_value,
            "Explicación": explanation,
            "Fragmento fuente": source_fragment,
            "Fragmento comparado": compared_fragment,
            "Norma o principio posiblemente comprometido": norm,
            "Qué debe corregirse": (
                "Verificar el original firmado y solicitar corrección, aclaración "
                "o dejar constancia del error material, según la etapa procesal."
            ),
            "Confirmado por revisor": False,
            "Observación final": "",
        }
    )


def compare_profiles(source: dict, target: dict) -> list[dict]:
    rows = []

    source_text = source["Texto"]
    target_text = target["Texto"]

    source_numbers = set(source["Números de fallo"])
    target_numbers = set(target["Números de fallo"])

    if source_numbers and target_numbers and not source_numbers.intersection(target_numbers):
        add_issue(
            rows,
            "Número de fallo",
            "Alta",
            " / ".join(sorted(source_numbers)),
            " / ".join(sorted(target_numbers)),
            source["Documento"],
            target["Documento"],
            "La providencia posterior identifica un número de fallo diferente.",
            find_fragment(source_text, ("fallo de tutela", "sentencia")),
            find_fragment(target_text, ("fallo de tutela", "sentencia")),
            "Constitución Política, artículo 29; exactitud, congruencia y debido proceso",
        )

    source_radications = set(source["Radicados"])
    target_radications = set(target["Radicados"])

    if source_radications and target_radications:
        full_source = {
            item
            for item in source_radications
            if len(re.sub(r"\D", "", item)) >= 20
        }
        full_target = {
            item
            for item in target_radications
            if len(re.sub(r"\D", "", item)) >= 20
        }

        if full_source and full_target and not full_source.intersection(full_target):
            add_issue(
                rows,
                "Radicado",
                "Alta",
                " / ".join(sorted(full_source)),
                " / ".join(sorted(full_target)),
                source["Documento"],
                target["Documento"],
                "Los documentos parecen corresponder a radicados distintos.",
                find_fragment(source_text, ("expediente", "radicado")),
                find_fragment(target_text, ("expediente", "radicado")),
                "Constitución Política, artículo 29; identificación cierta del proceso",
            )

    source_dates = source["Fechas"]
    target_dates = target["Fechas"]

    source_fallo_dates = [
        value
        for value in source_dates
        if value.year >= 2020
    ]

    target_sentence_fragment = find_fragment(
        target_text,
        (
            "sentencia de tutela",
            "fallo de tutela",
        ),
    )

    target_sentence_dates = extract_dates(target_sentence_fragment)

    if source_fallo_dates and target_sentence_dates:
        expected = source_fallo_dates[0]

        wrong_dates = [
            value
            for value in target_sentence_dates
            if value != expected
        ]

        if wrong_dates:
            add_issue(
                rows,
                "Fecha del fallo",
                "Alta",
                expected.strftime("%d/%m/%Y"),
                " / ".join(
                    value.strftime("%d/%m/%Y")
                    for value in wrong_dates
                ),
                source["Documento"],
                target["Documento"],
                "La providencia posterior cambia la fecha del fallo fuente.",
                find_fragment(
                    source_text,
                    (
                        "popayan",
                        "diecinueve",
                    ),
                ),
                target_sentence_fragment,
                "Constitución Política, artículo 29; exactitud fáctica y congruencia",
            )

    source_rights = set(source["Derechos"])
    target_rights = set(target["Derechos"])

    if source_rights and target_rights:
        wrong_rights = target_rights - source_rights
        omitted_rights = source_rights - target_rights

        if wrong_rights or omitted_rights:
            add_issue(
                rows,
                "Derechos fundamentales",
                "Alta",
                " / ".join(sorted(source_rights)),
                " / ".join(sorted(target_rights)),
                source["Documento"],
                target["Documento"],
                (
                    "La providencia posterior describe derechos diferentes de los "
                    "identificados y tutelados en el fallo fuente."
                ),
                find_fragment(
                    source_text,
                    (
                        "derechos fundamentales",
                        "tutelar los derechos",
                        "derecho fundamental a la salud",
                    ),
                ),
                find_fragment(
                    target_text,
                    (
                        "derecho fundamental",
                        "concediendo el derecho",
                    ),
                ),
                "Constitución Política, artículo 29; congruencia, motivación y fidelidad al fallo",
            )

    source_objects = set(source["Objetos"])
    target_objects = set(target["Objetos"])

    if source_objects and target_objects:
        missing_objects = source_objects - target_objects

        if missing_objects:
            add_issue(
                rows,
                "Objeto de la orden",
                "Media",
                " / ".join(sorted(source_objects)),
                " / ".join(sorted(target_objects)),
                source["Documento"],
                target["Documento"],
                (
                    "La providencia posterior no reproduce completamente el objeto "
                    "material de la orden o utiliza una descripción distinta."
                ),
                find_fragment(
                    source_text,
                    (
                        "molde de silicona",
                        "tratamiento integral",
                    ),
                ),
                find_fragment(
                    target_text,
                    (
                        "audifonos",
                        "cumplimiento del fallo",
                    ),
                ),
                "Constitución Política, artículo 29; congruencia y cumplimiento exacto",
            )

    return rows


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


st.subheader("1. Cargar fallo fuente")

source_file = st.file_uploader(
    "Carga el fallo o sentencia original",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png"],
    accept_multiple_files=False,
    key="source_judgment",
)

st.subheader("2. Cargar providencias posteriores")

target_files = st.file_uploader(
    "Carga uno o varios autos, decisiones o actuaciones posteriores",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="later_orders",
)

if source_file is None or not target_files:
    st.stop()


with st.spinner("Comparando fallo fuente con providencias posteriores..."):
    source_raw = cached_load(
        source_file.name,
        digest(source_file.getvalue()),
        source_file.getvalue(),
        enabled,
        min_chars,
        max_pages,
        dpi,
    )

    source_pages = [
        restore(item)
        for item in source_raw
    ]

    source_profile = build_profile(
        source_file.name,
        source_pages,
    )

    target_profiles = []

    for uploaded in target_files:
        raw = cached_load(
            uploaded.name,
            digest(uploaded.getvalue()),
            uploaded.getvalue(),
            enabled,
            min_chars,
            max_pages,
            dpi,
        )

        pages = [
            restore(item)
            for item in raw
        ]

        target_profiles.append(
            build_profile(
                uploaded.name,
                pages,
            )
        )


st.subheader("3. Datos extraídos del fallo fuente")

source_summary = pd.DataFrame(
    [
        {
            "Documento": source_profile["Documento"],
            "Radicados": " | ".join(source_profile["Radicados"]),
            "Número de fallo": " | ".join(source_profile["Números de fallo"]),
            "Fechas detectadas": " | ".join(
                value.strftime("%d/%m/%Y")
                for value in source_profile["Fechas"]
            ),
            "Derechos": " | ".join(source_profile["Derechos"]),
            "Objeto de la orden": " | ".join(source_profile["Objetos"]),
        }
    ]
)

st.dataframe(
    source_summary,
    use_container_width=True,
    hide_index=True,
)


st.subheader("4. Inconsistencias detectadas")

issues = []

for target_profile in target_profiles:
    issues.extend(
        compare_profiles(
            source_profile,
            target_profile,
        )
    )

issues_df = pd.DataFrame(issues)

if issues_df.empty:
    st.success(
        "No se detectaron diferencias claras con las reglas actuales. "
        "Esto no sustituye la comparación jurídica manual."
    )
    st.stop()


edited = st.data_editor(
    issues_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fragmento fuente": st.column_config.TextColumn(
            "Fragmento fuente",
            width="large",
        ),
        "Fragmento comparado": st.column_config.TextColumn(
            "Fragmento comparado",
            width="large",
        ),
        "Explicación": st.column_config.TextColumn(
            "Explicación",
            width="large",
        ),
        "Confirmado por revisor": st.column_config.CheckboxColumn(
            "Confirmado por revisor",
        ),
        "Observación final": st.column_config.TextColumn(
            "Observación final",
            width="large",
        ),
    },
    key="concordance_issues",
)


st.subheader("5. Semáforo de concordancia")

weights = {
    "Alta": 30,
    "Media": 15,
    "Baja": 5,
}

score = min(
    100,
    sum(
        weights.get(value, 5)
        for value in edited["Severidad"]
    ),
)

if score >= 60:
    st.error(
        f"🔴 INCONSISTENCIAS RELEVANTES — {score}/100. "
        "La providencia posterior altera o contradice datos esenciales del fallo fuente."
    )
elif score >= 25:
    st.warning(
        f"🟡 REQUIERE VERIFICACIÓN — {score}/100."
    )
else:
    st.success(
        f"🟢 SIN DIFERENCIAS GRAVES DETECTADAS — {score}/100."
    )


st.subheader("6. Explicación detallada")

for index, row in edited.iterrows():
    with st.expander(
        f"{index + 1}. {row['Categoría']} — {row['Documento comparado']}",
        expanded=True,
    ):
        st.markdown(
            f"**Dato correcto según el fallo:** "
            f"{row['Dato correcto según fuente']}"
        )
        st.markdown(
            f"**Dato utilizado en la providencia posterior:** "
            f"{row['Dato encontrado después']}"
        )
        st.markdown(f"**Explicación:** {row['Explicación']}")
        st.markdown(f"**Fragmento del fallo:** {row['Fragmento fuente']}")
        st.markdown(
            f"**Fragmento de la providencia posterior:** "
            f"{row['Fragmento comparado']}"
        )
        st.markdown(
            f"**Norma o principio posiblemente comprometido:** "
            f"{row['Norma o principio posiblemente comprometido']}"
        )
        st.markdown(f"**Actuación:** {row['Qué debe corregirse']}")


st.subheader("7. Conclusión automática")

categories = set(edited["Categoría"])

conclusions = []

if "Fecha del fallo" in categories:
    conclusions.append(
        "Se detectó alteración de la fecha del fallo fuente."
    )

if "Derechos fundamentales" in categories:
    conclusions.append(
        "Se detectó sustitución o modificación de los derechos tutelados."
    )

if "Radicado" in categories:
    conclusions.append(
        "Se detectó posible mezcla o identificación equivocada del proceso."
    )

if "Objeto de la orden" in categories:
    conclusions.append(
        "Debe verificarse si la providencia posterior reprodujo fielmente el objeto de la orden."
    )

for item in conclusions:
    st.markdown(f"❌ {item}")

st.info(
    "Estos errores pueden ser materiales, pero son relevantes cuando afectan "
    "la comprensión del fallo, el análisis de cumplimiento o la decisión posterior. "
    "Deben dejarse documentados y verificarse en la versión oficial firmada."
)


st.subheader("8. Exportar comparación")

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    source_summary.to_excel(
        writer,
        sheet_name="Fallo fuente",
        index=False,
    )

    edited.to_excel(
        writer,
        sheet_name="Inconsistencias",
        index=False,
    )

st.download_button(
    "Descargar comparación en Excel",
    data=output.getvalue(),
    file_name="comparacion_fallo_providencias.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)
