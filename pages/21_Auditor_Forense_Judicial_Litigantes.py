from __future__ import annotations

import hashlib
import io
import re
from collections import defaultdict
from datetime import date, datetime

import pandas as pd
import streamlit as st

from legal_analyzer.document_loader import load_document
from legal_analyzer.models import PageTrace
from legal_analyzer.ocr_engine import OCRConfig


st.set_page_config(
    page_title="Auditor Forense Judicial",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Auditor Forense Judicial y de Litigación")
st.caption(
    "Revisa documentos de despachos judiciales y escritos de abogados, "
    "detecta inconsistencias, errores, omisiones y riesgos procesales."
)

st.error(
    "Los resultados son indicios preliminares. No declaran faltas disciplinarias, "
    "delitos ni errores judiciales definitivos. Cada hallazgo debe comprobarse "
    "con el expediente completo y la norma especial aplicable."
)


MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

CATALOG = {
    "Mora o inactividad aparente": (
        "Despacho judicial",
        "Ley 270 de 1996, artículos 4 y 7; Acuerdo PSAA11-8716 de 2011",
        "Constancia de radicación, última actuación, término aplicable y consulta actual.",
        "Vigilancia Judicial Administrativa, si la demora es atribuible a la gestión.",
    ),
    "Término posiblemente vencido": (
        "Despacho judicial o parte",
        "Ley 1564 de 2012, artículo 118, o norma especial",
        "Providencia, notificación, ejecutoria, días inhábiles y suspensiones.",
        "Impulso, recurso, solicitud de decisión o vigilancia, según el caso.",
    ),
    "Notificación posiblemente incompleta": (
        "Despacho judicial",
        "Norma procesal aplicable; Ley 2213 de 2022, artículo 8, cuando corresponda",
        "Mensaje, destinatario, envío, entrega, acceso y constancia.",
        "Solicitar corrección o actuación procesal; vigilancia solo por gestión.",
    ),
    "Incongruencia entre motivación y decisión": (
        "Despacho judicial",
        "Constitución Política, artículo 29; deber de motivación y congruencia",
        "Comparar hechos, problema jurídico, consideraciones y resolutivo.",
        "Normalmente recurso o mecanismo judicial; no usar vigilancia para cambiar la decisión.",
    ),
    "Omisión probatoria posible": (
        "Despacho judicial",
        "Constitución Política, artículo 29",
        "Índice, anexos, constancia de incorporación y valoración expresa.",
        "Recurso o actuación judicial correspondiente.",
    ),
    "Confusión de partes, radicado u objeto": (
        "Despacho o abogado litigante",
        "Constitución Política, artículo 29; exactitud y lealtad procesal",
        "Carátula, poderes, pretensiones, providencias y documento fuente.",
        "Corrección, aclaración, recurso o subsanación.",
    ),
    "Petición o pretensión imprecisa": (
        "Abogado litigante",
        "Deberes de claridad, lealtad y diligencia procesal",
        "Comparar hechos, pretensiones, fundamentos y anexos.",
        "Corregir o complementar antes de radicar.",
    ),
    "Falta de soporte de radicación o recepción": (
        "Abogado litigante",
        "Carga de acreditar la actuación procesal invocada",
        "Correo, acuse, sello, radicación o constancia del sistema.",
        "Obtener prueba de envío o recepción.",
    ),
    "Cita normativa posiblemente inadecuada": (
        "Despacho o abogado litigante",
        "Principio de legalidad y deber de fundamentación",
        "Confirmar vigencia, artículo, materia y régimen procesal.",
        "Corregir la fundamentación y distinguir norma general de especial.",
    ),
    "Argumento contradictorio entre escritos": (
        "Abogado litigante",
        "Buena fe, lealtad procesal y coherencia de la teoría del caso",
        "Comparar versiones, fechas, pretensiones y pruebas.",
        "Explicar o corregir la diferencia antes de continuar.",
    ),
    "Cumplimiento de tutela posiblemente insuficiente": (
        "Despacho judicial o parte obligada",
        "Decreto 2591 de 1991, artículos 27 y 52",
        "Fallo, obligado, plazo, cumplimiento material y medidas adoptadas.",
        "Solicitud de cumplimiento, desacato o vigilancia por demora.",
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


@st.cache_data(show_spinner=False, max_entries=300)
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
        if len(item.strip()) >= 28
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
    ):
        values.extend(re.findall(pattern, text or ""))
    return list(dict.fromkeys(values))


def source_type(text: str) -> str:
    clean = normalize(text)
    if any(x in clean for x in ("juzgado", "tribunal", "resuelve", "dispone", "notifiquese")):
        return "Providencia o documento del despacho"
    if any(x in clean for x in ("solicito", "pretensiones", "apoderado", "memorial", "recurso")):
        return "Escrito de abogado o parte"
    return "Documento por clasificar"


def add_finding(rows, document, page, finding, evidence, explanation, severity, confidence):
    actor, norm, verify, route = CATALOG[finding]
    rows.append({
        "Documento": document,
        "Página": page,
        "Actor posible": actor,
        "Posible hallazgo": finding,
        "Severidad": severity,
        "Confianza preliminar": confidence,
        "Evidencia textual": evidence,
        "Explicación": explanation,
        "Norma o principio posible": norm,
        "Cómo comprobarlo": verify,
        "Ruta procesal posible": route,
        "Confirmado por revisor": False,
        "Conclusión revisada": "",
    })


def analyze_document(document: str, pages: list[PageTrace]) -> list[dict]:
    rows = []
    full_text = "\n".join(page.text or "" for page in pages)
    clean = normalize(full_text)
    doc_type = source_type(full_text)
    radications = extract_radications(full_text)
    dates = extract_dates(full_text)

    if len(radications) > 1:
        add_finding(
            rows, document, "Varias",
            "Confusión de partes, radicado u objeto",
            " / ".join(radications),
            "El archivo contiene varios radicados. Puede ser cita válida o mezcla de procesos.",
            "Alta", 85,
        )

    if "Providencia" in doc_type:
        if any(x in clean for x in ("se encuentra a despacho", "pase a despacho", "pendiente de decision")):
            if dates:
                elapsed = (date.today() - min(dates)).days
                if elapsed >= 30:
                    add_finding(
                        rows, document, "Varias",
                        "Mora o inactividad aparente",
                        f"Fecha detectada: {min(dates):%d/%m/%Y}; días transcurridos: {elapsed}",
                        "La actuación aparece al despacho o pendiente y ha transcurrido un periodo relevante.",
                        "Alta" if elapsed >= 90 else "Media",
                        min(95, 55 + elapsed // 10),
                    )

        if any(x in clean for x in ("no obra prueba", "no se acredito", "no se aporto")):
            if any(x in clean for x in ("anexo", "dictamen", "constancia", "historia clinica", "correo")):
                add_finding(
                    rows, document, "Varias",
                    "Omisión probatoria posible",
                    "El texto niega acreditación y también menciona anexos o soportes.",
                    "Debe verificarse si la prueba fue aportada, incorporada y valorada.",
                    "Alta", 78,
                )

        if "sin mas consideraciones" in clean and any(x in clean for x in ("no procede", "negar", "rechazar")):
            add_finding(
                rows, document, "Varias",
                "Incongruencia entre motivación y decisión",
                "La providencia adopta una decisión adversa con motivación aparentemente limitada.",
                "Debe compararse el razonamiento completo con la parte resolutiva.",
                "Media", 60,
            )

        if any(x in clean for x in ("notificar", "notificacion", "correo electronico")):
            if not any(x in clean for x in ("constancia", "acuse", "entregado", "recibido", "fecha de envio")):
                add_finding(
                    rows, document, "Varias",
                    "Notificación posiblemente incompleta",
                    "Se menciona notificación sin constancia visible de entrega o acceso.",
                    "Puede faltar soporte de la notificación efectiva.",
                    "Media", 58,
                )

        if any(x in clean for x in ("incidente de desacato", "cumplimiento del fallo", "continua el incumplimiento")):
            add_finding(
                rows, document, "Varias",
                "Cumplimiento de tutela posiblemente insuficiente",
                "El documento muestra discusión persistente sobre cumplimiento.",
                "Debe verificarse si el despacho adoptó medidas eficaces y si hubo cumplimiento material.",
                "Alta", 75,
            )

    if "Escrito de abogado" in doc_type:
        if any(x in clean for x in ("solicito", "pretensiones")):
            if not any(x in clean for x in ("primero", "segundo", "tercero", "peticion concreta")):
                add_finding(
                    rows, document, "Varias",
                    "Petición o pretensión imprecisa",
                    "El escrito formula solicitudes sin una estructura clara de pretensiones.",
                    "Puede dificultar que el despacho identifique exactamente lo pedido.",
                    "Media", 65,
                )

        if any(x in clean for x in ("remiti", "radique", "presente", "envie")):
            if not any(x in clean for x in ("acuse", "radicado", "recibido", "constancia", "sello")):
                add_finding(
                    rows, document, "Varias",
                    "Falta de soporte de radicación o recepción",
                    "El escrito afirma envío o presentación sin soporte visible.",
                    "Debe aportarse prueba de recepción antes de alegar falta de trámite.",
                    "Alta", 72,
                )

        cited_articles = re.findall(r"articulo\s+\d+[a-z]?", clean)
        if len(cited_articles) >= 4:
            add_finding(
                rows, document, "Varias",
                "Cita normativa posiblemente inadecuada",
                " / ".join(cited_articles[:8]),
                "La cantidad de citas exige comprobar vigencia, pertinencia y régimen aplicable.",
                "Media", 50,
            )

    technical = [
        token
        for token in ("phonak sky", "phonak naida", "naida lumity", "sky l90", "l90-up", "up l90")
        if token in clean
    ]

    if len(set(technical)) >= 2:
        add_finding(
            rows, document, "Varias",
            "Confusión de partes, radicado u objeto",
            " / ".join(sorted(set(technical))),
            "Se mencionan objetos técnicos distintos; puede ser comparación válida o confusión.",
            "Alta", 88,
        )

    return rows


def cross_document_analysis(documents: dict[str, list[PageTrace]]) -> list[dict]:
    rows = []
    radicado_map = defaultdict(list)
    claims = []

    for document, pages in documents.items():
        text = "\n".join(page.text or "" for page in pages)
        for radicado in extract_radications(text):
            radicado_map[radicado].append(document)

        for page in pages:
            for fragment in split_fragments(page.text):
                clean = normalize(fragment)
                if any(x in clean for x in ("cumplio", "entrego", "respondio", "notifico")):
                    polarity = "Positiva"
                elif any(x in clean for x in ("no cumplio", "no entrego", "sin respuesta", "no notifico", "incumplimiento")):
                    polarity = "Negativa"
                else:
                    continue

                topic = None
                for candidate in ("cumplimiento", "entrega", "respuesta", "notificacion"):
                    if candidate[:5] in clean:
                        topic = candidate
                        break

                if topic:
                    claims.append({
                        "Documento": document,
                        "Página": page.page,
                        "Fragmento": fragment,
                        "Polaridad": polarity,
                        "Tema": topic,
                    })

    if len(radicado_map) > 1:
        add_finding(
            rows, "Comparación del expediente", "Varias",
            "Confusión de partes, radicado u objeto",
            "; ".join(f"{rad}: {', '.join(files)}" for rad, files in radicado_map.items()),
            "Los archivos contienen radicados distintos y deben separarse o justificarse.",
            "Alta", 90,
        )

    for i, left in enumerate(claims):
        for right in claims[i + 1:]:
            if left["Tema"] == right["Tema"] and left["Polaridad"] != right["Polaridad"]:
                add_finding(
                    rows,
                    f"{left['Documento']} / {right['Documento']}",
                    f"{left['Página']} / {right['Página']}",
                    "Argumento contradictorio entre escritos",
                    f"Versión 1: {left['Fragmento']} | Versión 2: {right['Fragmento']}",
                    "Existen afirmaciones opuestas sobre el mismo tema. Debe establecerse cuál tiene respaldo documental.",
                    "Alta", 82,
                )

    return rows


def risk_summary(df: pd.DataFrame):
    if df.empty:
        return "Verde", 10, "Sin hallazgos claros con las reglas actuales"

    weights = {"Alta": 25, "Media": 12, "Baja": 5}
    score = min(100, sum(weights.get(value, 5) for value in df["Severidad"]))

    if score >= 70:
        return "Rojo", score, "Revisión forense prioritaria"
    if score >= 30:
        return "Amarillo", score, "Requiere comprobación y corrección"
    return "Verde", score, "Hallazgos leves o insuficientes"


with st.sidebar:
    st.header("OCR")
    enabled = st.checkbox("Aplicar OCR", value=True)
    min_chars = st.slider("Mínimo de caracteres útiles", 20, 300, 80, 10)
    max_pages = st.slider("Máximo de páginas OCR", 5, 200, 75, 5)
    dpi = st.select_slider("Resolución OCR", [150, 200, 220, 250, 300], value=220)


uploaded_files = st.file_uploader(
    "Carga documentos del despacho y escritos de abogados",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.stop()


documents = {}
loading_errors = []

with st.spinner("Leyendo y cruzando documentos..."):
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
            documents[uploaded.name] = [restore(item) for item in raw]
        except Exception as error:
            loading_errors.append(f"{uploaded.name}: {error}")
            documents[uploaded.name] = []


if loading_errors:
    st.warning("\n".join(loading_errors))


st.subheader("1. Clasificación de documentos")

classification = []

for document, pages in documents.items():
    full_text = "\n".join(page.text or "" for page in pages)
    classification.append({
        "Documento": document,
        "Tipo detectado": source_type(full_text),
        "Páginas": len(pages),
        "Radicados": " | ".join(extract_radications(full_text)),
        "Fechas": " | ".join(value.strftime("%d/%m/%Y") for value in extract_dates(full_text)),
    })

st.dataframe(pd.DataFrame(classification), use_container_width=True, hide_index=True)


st.subheader("2. Hallazgos por documento")

findings = []

for document, pages in documents.items():
    findings.extend(analyze_document(document, pages))

findings.extend(cross_document_analysis(documents))

findings_df = pd.DataFrame(findings)

if findings_df.empty:
    st.success(
        "No se detectaron errores claros con las reglas automáticas. "
        "Esto no demuestra que los documentos estén libres de problemas."
    )
    st.stop()


edited = st.data_editor(
    findings_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Evidencia textual": st.column_config.TextColumn("Evidencia textual", width="large"),
        "Explicación": st.column_config.TextColumn("Explicación", width="large"),
        "Cómo comprobarlo": st.column_config.TextColumn("Cómo comprobarlo", width="large"),
        "Ruta procesal posible": st.column_config.TextColumn("Ruta procesal posible", width="large"),
        "Confianza preliminar": st.column_config.ProgressColumn(
            "Confianza preliminar", min_value=0, max_value=100, format="%d"
        ),
        "Severidad": st.column_config.SelectboxColumn(
            "Severidad", options=["Alta", "Media", "Baja"]
        ),
        "Confirmado por revisor": st.column_config.CheckboxColumn("Confirmado por revisor"),
        "Conclusión revisada": st.column_config.TextColumn("Conclusión revisada", width="large"),
    },
    key="forensic_findings",
)


st.subheader("3. Semáforo forense")

color, score, title = risk_summary(edited)
icon = {"Rojo": "🔴", "Amarillo": "🟡", "Verde": "🟢"}[color]

if color == "Rojo":
    st.error(f"{icon} {title} — {score}/100")
elif color == "Amarillo":
    st.warning(f"{icon} {title} — {score}/100")
else:
    st.success(f"{icon} {title} — {score}/100")


st.subheader("4. Separación por actor")

for actor in edited["Actor posible"].dropna().unique():
    actor_df = edited[edited["Actor posible"] == actor]

    with st.expander(f"{actor} — {len(actor_df)} hallazgo(s)", expanded=True):
        st.dataframe(actor_df, use_container_width=True, hide_index=True)


st.subheader("5. Explicación detallada")

for index, row in edited.iterrows():
    with st.expander(
        f"{index + 1}. {row['Posible hallazgo']} — {row['Documento']}",
        expanded=row["Severidad"] == "Alta",
    ):
        st.markdown(f"**Actor posible:** {row['Actor posible']}")
        st.markdown(f"**Evidencia:** {row['Evidencia textual']}")
        st.markdown(f"**Explicación:** {row['Explicación']}")
        st.markdown(f"**Norma o principio posible:** {row['Norma o principio posible']}")
        st.markdown(f"**Cómo comprobarlo:** {row['Cómo comprobarlo']}")
        st.markdown(f"**Ruta procesal posible:** {row['Ruta procesal posible']}")
        st.caption(
            "Antes de usar este hallazgo, revisa el documento completo, "
            "la versión oficial y la etapa procesal."
        )


st.subheader("6. Actuaciones recomendadas")

recommended = []

if (edited["Actor posible"].str.contains("Despacho", na=False)).any():
    recommended.extend([
        "Confirmar la última actuación oficial y la fecha real de notificación.",
        "Separar errores de decisión de fallas de gestión administrativa.",
        "Usar recursos o actuaciones judiciales para controvertir el contenido de providencias.",
        "Usar Vigilancia Judicial únicamente para mora, falta de trámite o gestión ineficaz.",
    ])

if (edited["Actor posible"].str.contains("Abogado", na=False)).any():
    recommended.extend([
        "Corregir pretensiones ambiguas y ordenar hechos, solicitudes y anexos.",
        "Aportar constancias de radicación y recepción.",
        "Revisar vigencia y pertinencia de cada cita normativa.",
        "Explicar contradicciones entre escritos antes de continuar.",
    ])

for number, item in enumerate(dict.fromkeys(recommended), start=1):
    st.markdown(f"{number}. {item}")


st.subheader("7. Exportar auditoría")

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    pd.DataFrame(classification).to_excel(writer, sheet_name="Clasificación", index=False)
    edited.to_excel(writer, sheet_name="Hallazgos", index=False)

    summary = (
        edited.groupby(
            ["Actor posible", "Posible hallazgo", "Severidad"],
            dropna=False,
        )
        .size()
        .reset_index(name="Cantidad")
    )

    summary.to_excel(writer, sheet_name="Resumen", index=False)

st.download_button(
    "Descargar auditoría forense en Excel",
    data=output.getvalue(),
    file_name="auditoria_forense_judicial_litigantes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)
