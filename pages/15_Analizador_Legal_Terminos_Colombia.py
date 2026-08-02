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

from legal_ui.case_context import LOADED_FILES_KEY
from legal_ui.colombia_calendar import calculate_deadline_colombia as calculate_deadline
from legal_ui.colombia_calendar import colombia_holidays, next_business_day
from legal_ui.tool_bridge import render_active_case_banner, render_sync_terms_to_lexivox


st.set_page_config(
    page_title="Analizador Legal de Términos Colombia",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ Analizador Legal de Términos Colombia")
st.caption(
    "Detecta el término, calcula cuándo vence y propone la actuación que puede continuar."
)

st.warning(
    "El resultado es preliminar. Debes confirmar la fecha efectiva de notificación, "
    "la regla de cómputo, los festivos y la norma aplicable."
)


NUMBER_WORDS = {
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "quince": 15,
    "veinte": 20,
    "treinta": 30,
    "cuarenta": 40,
    "cuarenta y ocho": 48,
}


RULES = [
    {
        "clase": "Término judicial otorgado en auto o providencia",
        "regimen": "Proceso judicial / tutela",
        "norma": "Providencia judicial y regla procesal aplicable",
        "articulo": "Verificar artículo citado y artículo 118 CGP, si procede",
        "inicio": "Día siguiente a la notificación, salvo regla especial",
        "palabras": (
            "ordena",
            "requerir",
            "termino improrrogable",
            "dentro de",
            "plazo de",
            "vencido el termino",
        ),
    },
    {
        "clase": "Impugnación de fallo de tutela",
        "regimen": "Acción de tutela",
        "norma": "Decreto 2591 de 1991",
        "articulo": "Artículo 31",
        "inicio": "Notificación del fallo",
        "palabras": (
            "impugnacion",
            "impugnar",
            "fallo de tutela",
        ),
    },
    {
        "clase": "Respuesta general a derecho de petición",
        "regimen": "Derecho de petición",
        "norma": "Ley 1755 de 2015",
        "articulo": "Artículo 14",
        "inicio": "Recepción de la petición",
        "palabras": (
            "derecho de peticion",
            "peticion general",
        ),
    },
    {
        "clase": "Petición de documentos o información",
        "regimen": "Derecho de petición",
        "norma": "Ley 1755 de 2015",
        "articulo": "Artículo 14",
        "inicio": "Recepción de la petición",
        "palabras": (
            "solicitud de documentos",
            "solicitud de informacion",
            "copias",
            "expediente",
        ),
    },
    {
        "clase": "Recurso administrativo",
        "regimen": "Procedimiento administrativo",
        "norma": "Ley 1437 de 2011",
        "articulo": "Artículo 76",
        "inicio": "Notificación del acto administrativo",
        "palabras": (
            "recurso de reposicion",
            "recurso de apelacion",
            "acto administrativo",
        ),
    },
]


def norm(text: str) -> str:
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


@st.cache_data(show_spinner=False, max_entries=40)
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


def explicit_term(text: str) -> tuple[int | None, str | None, str]:
    clean = norm(text)

    word_pattern = (
        "cuarenta y ocho|cuarenta|treinta|veinte|quince|diez|"
        "nueve|ocho|siete|seis|cinco|cuatro|tres|dos|un|uno|una"
    )

    patterns = [
        (
            rf"(?:dentro de|por el termino de|"
            rf"termino(?: \w+){{0,4}} de|plazo(?: \w+){{0,4}} de)\s+"
            rf"(?P<number>{word_pattern}|\d{{1,3}})\s*"
            rf"(?P<unit>horas?|dias?)"
            rf"(?:\s*\((?P<paren>\d{{1,3}})\)\s*(?:horas?|dias?)?)?"
        ),
        (
            rf"\b(?P<number>{word_pattern}|\d{{1,3}})\s+"
            rf"(?P<unit>horas?|dias?)\s*"
            rf"(?:\((?P<paren>\d{{1,3}})\)\s*(?:horas?|dias?)?)?"
            rf"\s*(?:siguientes|habiles|calendario|improrrogables)?"
        ),
    ]

    for pattern in patterns:
        match = re.search(pattern, clean)

        if not match:
            continue

        raw_number = match.group("number").strip()
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
        character = "Improrrogable" if "improrrogable" in clean else "Ordinario o por confirmar"

        return quantity, unit, character

    return None, None, ""


def action_detected(fragment: str) -> str:
    clean = norm(fragment)

    actions = (
        ("rendir informe o dictamen", ("informe", "dictamen")),
        ("pronunciarse", ("pronuncien", "pronunciarse")),
        ("dar cumplimiento", ("dar cumplimiento", "cumplimiento")),
        ("entregar", ("entregar", "entrega")),
        ("responder", ("responder", "respuesta")),
        ("aportar documentos", ("aportar", "allegar", "remitir")),
        ("impugnar", ("impugnar", "impugnacion")),
    )

    for label, words in actions:
        if any(word in clean for word in words):
            return label

    return "Actuación por confirmar"


def post_expiry_instruction(full_text: str) -> str:
    clean = norm(full_text)

    patterns = [
        r"vencido el termino[^\.]{0,350}",
        r"una vez vencido el termino[^\.]{0,350}",
        r"cumplido el termino[^\.]{0,350}",
    ]

    for pattern in patterns:
        match = re.search(pattern, clean)

        if match:
            return match.group(0).strip().capitalize()

    return ""


def classify(fragment: str) -> list[dict]:
    clean = norm(fragment)
    quantity, unit, character = explicit_term(fragment)

    if quantity is None:
        return []

    results = []

    for rule in RULES:
        hits = sum(word in clean for word in rule["palabras"])

        if hits == 0 and rule["clase"] != "Término judicial otorgado en auto o providencia":
            continue

        day_rule = "Por confirmar"

        if unit == "Horas":
            day_rule = "Horas continuas o por confirmar"
        elif "habil" in clean:
            day_rule = "Hábiles"
        elif "calendario" in clean:
            day_rule = "Calendario"

        results.append(
            {
                "Clase de término": rule["clase"],
                "Régimen jurídico": rule["regimen"],
                "Norma sugerida": rule["norma"],
                "Artículo": rule["articulo"],
                "Cantidad": quantity,
                "Unidad": unit,
                "Tipo de días": day_rule,
                "Carácter": character,
                "Hecho inicial sugerido": rule["inicio"],
                "Actuación exigida": action_detected(fragment),
                "Seguridad preliminar": min(95, 60 + hits * 10),
            }
        )

        if hits:
            break

    return results


def detect(pages: list[PageTrace]) -> list[dict]:
    full_text = "\n".join(page.text for page in pages)
    after_expiry = post_expiry_instruction(full_text)
    rows = []

    for page in pages:
        fragments = [
            item.strip()
            for item in re.split(r"(?<=[\.\;\:])\s+|\n+", page.text)
            if len(item.strip()) >= 20
        ]

        for fragment in fragments:
            for candidate in classify(fragment):
                rows.append(
                    {
                        "Documento": page.document,
                        "Página": page.page,
                        "Fragmento completo": fragment,
                        **candidate,
                        "Actuación indicada después del vencimiento": after_expiry,
                        "Fecha de notificación confirmada": None,
                        "Hora de notificación": time(8, 0),
                        "Regla de inicio": "Comienza al día siguiente",
                        "Aplicar cálculo": False,
                        "Conclusión revisada": "",
                    }
                )

    unique = []
    seen = set()

    for row in rows:
        key = (
            row["Documento"],
            row["Página"],
            row["Fragmento completo"],
            row["Clase de término"],
        )

        if key not in seen:
            seen.add(key)
            unique.append(row)

    return unique


def status(deadline: datetime) -> tuple[str, str, float]:
    hours = (deadline - datetime.now()).total_seconds() / 3600

    if hours < 0:
        return "Rojo", "Vencido", hours
    if hours <= 24:
        return "Rojo", "Urgente", hours
    if hours <= 72:
        return "Amarillo", "Próximo", hours

    return "Verde", "En plazo", hours


def continuation(
    row: pd.Series,
    deadline_state: str,
) -> str:
    required = str(row.get("Actuación exigida", ""))
    after_expiry = str(
        row.get(
            "Actuación indicada después del vencimiento",
            "",
        )
    )

    if deadline_state != "Vencido":
        return (
            f"Esperar el vencimiento y verificar si se presentó: {required}. "
            "Mientras tanto, revisar el expediente y preparar observaciones."
        )

    if after_expiry:
        return (
            f"Verificar que el despacho ejecute lo ordenado después del vencimiento: "
            f"{after_expiry}. Solicitar copia de la respuesta presentada y constancia "
            "de la actuación posterior."
        )

    clean = norm(required)

    if "informe" in clean or "dictamen" in clean:
        return (
            "Consultar si el informe o dictamen fue presentado. Si existe, solicitar copia "
            "y pronunciarse sobre su suficiencia. Si no existe, solicitar al juzgado que "
            "continúe el trámite, requiera el cumplimiento y adopte las medidas procedentes."
        )

    if "cumplimiento" in clean:
        return (
            "Solicitar verificación material del cumplimiento. Si continúa el incumplimiento, "
            "pedir medidas de cumplimiento y la continuación del incidente de desacato."
        )

    if "respuesta" in clean:
        return (
            "Verificar si se respondió de fondo. Si no hubo respuesta, preparar requerimiento, "
            "tutela o actuación procesal según el régimen identificado."
        )

    return (
        "Solicitar constancia de vencimiento, revisar si la parte obligada actuó y pedir "
        "que el despacho continúe con la etapa procesal correspondiente."
    )


MONTHS_AUTO = {
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


def extract_dates_from_text(text: str) -> list[date]:
    """
    Extrae fechas numéricas y fechas escritas en español.
    """
    values: list[date] = []
    clean = norm(text)

    for day, month, year in re.findall(
        r"\b([0-3]?\d)[/-]([01]?\d)[/-]((?:19|20)\d{2})\b",
        clean,
    ):
        try:
            values.append(
                date(int(year), int(month), int(day))
            )
        except ValueError:
            pass

    textual_pattern = (
        r"\b([0-3]?\d)\s+de\s+("
        + "|".join(MONTHS_AUTO.keys())
        + r")\s+de\s+((?:19|20)\d{2})\b"
    )

    for day, month_name, year in re.findall(
        textual_pattern,
        clean,
    ):
        try:
            values.append(
                date(
                    int(year),
                    MONTHS_AUTO[month_name],
                    int(day),
                )
            )
        except ValueError:
            pass

    return list(dict.fromkeys(values))


def detect_notification_date(full_text: str) -> tuple[date | None, str, int]:
    """
    Busca primero una fecha cercana a palabras de notificación o recepción.
    Si no existe, usa la fecha principal del documento como estimación de baja confianza.
    """
    clean = norm(full_text)

    notification_patterns = [
        r"(?:notificado|notificacion|comunicado|recibido|recepcionado|enviado)"
        r"[^\.]{0,180}",
        r"(?:correo electronico|mensaje de datos)[^\.]{0,180}",
    ]

    for pattern in notification_patterns:
        for match in re.finditer(pattern, clean):
            fragment = match.group(0)
            dates = extract_dates_from_text(fragment)

            if dates:
                return (
                    dates[0],
                    "Fecha localizada cerca de una expresión de notificación o recepción",
                    85,
                )

    all_dates = extract_dates_from_text(full_text)

    if all_dates:
        return (
            all_dates[0],
            "Fecha principal del documento usada como estimación; confirmar notificación",
            40,
        )

    return (
        None,
        "No se encontró una fecha utilizable",
        0,
    )


def automatic_day_rule(
    unit: str,
    detected_rule: str,
    fragment: str,
) -> tuple[str, str]:
    """
    Aplica una regla automática conservadora.
    """
    clean = norm(fragment)

    if unit == "Horas":
        return (
            "Horas continuas o por confirmar",
            "El término está expresado en horas; confirmar si corre de forma continua.",
        )

    if detected_rule in {"Hábiles", "Calendario"}:
        return (
            detected_rule,
            "La regla aparece expresamente o ya fue clasificada.",
        )

    if "habil" in clean:
        return (
            "Hábiles",
            "El fragmento menciona días hábiles.",
        )

    if "calendario" in clean:
        return (
            "Calendario",
            "El fragmento menciona días calendario.",
        )

    return (
        "Hábiles",
        "Regla automática provisional para actuación judicial; debe confirmarse.",
    )


def automatic_start_rule(fragment: str) -> tuple[str, str]:
    clean = norm(fragment)

    if "a partir del mismo dia" in clean or "desde hoy" in clean:
        return (
            "Comienza el mismo día",
            "El texto parece ordenar inicio inmediato.",
        )

    return (
        "Comienza al día siguiente",
        "Regla automática provisional; confirmar con la notificación y la norma aplicable.",
    )


def build_automatic_results(
    rows: list[dict],
    pages: list[PageTrace],
) -> pd.DataFrame:
    full_text = "\n".join(page.text for page in pages)
    notification_date, date_reason, date_confidence = detect_notification_date(
        full_text
    )

    results = []

    for row in rows:
        fragment = str(row.get("Fragmento completo", ""))
        day_rule, day_reason = automatic_day_rule(
            str(row.get("Unidad", "Días")),
            str(row.get("Tipo de días", "Por confirmar")),
            fragment,
        )
        start_rule, start_reason = automatic_start_rule(fragment)

        if notification_date is None:
            results.append(
                {
                    "Documento": row.get("Documento", ""),
                    "Página": row.get("Página", ""),
                    "Clase de término": row.get("Clase de término", ""),
                    "Fecha base automática": None,
                    "Inicio automático": None,
                    "Vencimiento automático": None,
                    "Semáforo": "Amarillo",
                    "Estado": "Falta fecha de notificación",
                    "Actuación exigida": row.get("Actuación exigida", ""),
                    "Actuación que puede continuar": (
                        "Confirmar la fecha efectiva de notificación antes de calcular."
                    ),
                    "Confianza fecha": date_confidence,
                    "Fundamento fecha": date_reason,
                    "Regla usada": day_rule,
                    "Fundamento regla": day_reason,
                    "Regla de inicio": start_rule,
                    "Fundamento inicio": start_reason,
                    "Revisión obligatoria": True,
                }
            )
            continue

        notification = datetime.combine(
            notification_date,
            time(8, 0),
        )

        calculation_rule = (
            "Hábiles"
            if day_rule == "Horas continuas o por confirmar"
            else day_rule
        )

        start, deadline = calculate_deadline(
            notification=notification,
            quantity=int(row.get("Cantidad", 0)),
            unit=str(row.get("Unidad", "Días")),
            day_rule=calculation_rule,
            start_rule=start_rule,
            excluded=colombia_holidays(
                notification.date(),
                notification.date() + timedelta(days=730),
            ),
        )

        color, deadline_state, remaining_hours = status(deadline)

        results.append(
            {
                "Documento": row.get("Documento", ""),
                "Página": row.get("Página", ""),
                "Clase de término": row.get("Clase de término", ""),
                "Fecha base automática": notification,
                "Inicio automático": start,
                "Vencimiento automático": deadline,
                "Semáforo": color,
                "Estado": deadline_state,
                "Horas restantes": round(remaining_hours, 1),
                "Actuación exigida": row.get("Actuación exigida", ""),
                "Actuación que puede continuar": continuation(
                    pd.Series(row),
                    deadline_state,
                ),
                "Confianza fecha": date_confidence,
                "Fundamento fecha": date_reason,
                "Regla usada": day_rule,
                "Fundamento regla": day_reason,
                "Regla de inicio": start_rule,
                "Fundamento inicio": start_reason,
                "Revisión obligatoria": (
                    date_confidence < 80
                    or "provisional" in day_reason.lower()
                    or "provisional" in start_reason.lower()
                ),
            }
        )

    return pd.DataFrame(results)

with st.sidebar:
    st.header("OCR")
    enabled = st.checkbox("Aplicar OCR", value=True)
    min_chars = st.slider("Mínimo de caracteres útiles", 20, 300, 80, 10)
    max_pages = st.slider("Máximo de páginas OCR", 5, 100, 40, 5)
    dpi = st.select_slider(
        "Resolución OCR",
        [150, 200, 220, 250, 300],
        value=220,
    )


render_active_case_banner()

uploaded = st.file_uploader(
    "Sube el documento que quieres analizar",
    type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "eml"],
)

if not uploaded:
    loaded = st.session_state.get(LOADED_FILES_KEY) or []
    if loaded:
        uploaded = loaded[0]

if not uploaded:
    st.info("Sube un auto, fallo, requerimiento, notificación o constancia.")
    st.stop()


content = uploaded.getvalue()

with st.spinner("Analizando término, vencimiento y actuación posterior..."):
    raw = cached_load(
        uploaded.name,
        digest(content),
        content,
        enabled,
        min_chars,
        max_pages,
        dpi,
    )
    pages = [restore(item) for item in raw]
    rows = detect(pages)


if not rows:
    st.warning(
        "No se encontró un término expreso con las reglas actuales. "
        "Esto no demuestra que el documento no contenga términos."
    )
    st.stop()


st.success(f"Se detectaron {len(rows)} posible(s) término(s).")

automatic_results = build_automatic_results(
    rows,
    pages,
)

st.subheader("Resultado automático")

if automatic_results.empty:
    st.warning(
        "No fue posible generar un cálculo automático."
    )
else:
    st.dataframe(
        automatic_results,
        use_container_width=True,
        hide_index=True,
    )

    for _, result in automatic_results.iterrows():
        icon = {
            "Rojo": "🔴",
            "Amarillo": "🟡",
            "Verde": "🟢",
        }.get(result["Semáforo"], "⚪")

        st.info(
            f"{icon} **{result['Clase de término']}**\n\n"
            f"**Vencimiento automático:** "
            f"{result['Vencimiento automático'] or 'No calculado'}\n\n"
            f"**Estado:** {result['Estado']}\n\n"
            f"**Actuación siguiente:** "
            f"{result['Actuación que puede continuar']}\n\n"
            f"**Fecha usada:** {result['Fundamento fecha']}\n\n"
            f"**Regla usada:** {result['Regla usada']} — "
            f"{result['Fundamento regla']}"
        )

    st.warning(
        "Los resultados automáticos que usen la fecha principal del documento "
        "o una regla provisional deben confirmarse antes de presentar una actuación."
    )

    render_sync_terms_to_lexivox(
        automatic_results.to_dict(orient="records"),
        source="colombia",
        key="sync_colombia_auto_terms",
    )

    st.session_state["automatic_expiry_results"] = automatic_results

data = pd.DataFrame(rows)

edited = st.data_editor(
    data,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fragmento completo": st.column_config.TextColumn(
            "Fragmento completo",
            width="large",
        ),
        "Tipo de días": st.column_config.SelectboxColumn(
            "Tipo de días",
            options=[
                "Hábiles",
                "Calendario",
                "Horas continuas o por confirmar",
                "Por confirmar",
            ],
        ),
        "Fecha de notificación confirmada": st.column_config.DateColumn(
            "Fecha de notificación confirmada",
            format="YYYY-MM-DD",
        ),
        "Hora de notificación": st.column_config.TimeColumn(
            "Hora de notificación",
            format="HH:mm",
        ),
        "Regla de inicio": st.column_config.SelectboxColumn(
            "Regla de inicio",
            options=[
                "Comienza al día siguiente",
                "Comienza el mismo día",
            ],
        ),
        "Seguridad preliminar": st.column_config.ProgressColumn(
            "Seguridad preliminar",
            min_value=0,
            max_value=100,
            format="%d",
        ),
        "Aplicar cálculo": st.column_config.CheckboxColumn(
            "Calcular",
        ),
        "Conclusión revisada": st.column_config.TextColumn(
            "Conclusión revisada",
            width="large",
        ),
    },
    key="expiry_action_editor",
)


st.subheader("Explicación del documento")

for index, row in edited.iterrows():
    with st.expander(
        f"{index + 1}. {row['Clase de término']} — "
        f"{row['Documento']}, página {row['Página']}",
        expanded=index == 0,
    ):
        st.markdown(f"**Texto detectado:** {row['Fragmento completo']}")
        st.markdown(
            f"**Término:** {row['Cantidad']} {str(row['Unidad']).lower()} "
            f"— {row['Carácter']}"
        )
        st.markdown(f"**Actuación exigida:** {row['Actuación exigida']}")
        st.markdown(
            f"**Después del vencimiento:** "
            f"{row['Actuación indicada después del vencimiento'] or 'No se detectó instrucción expresa.'}"
        )
        st.markdown(
            f"**Norma sugerida:** {row['Norma sugerida']} — {row['Artículo']}"
        )


st.subheader("Vencimiento y actuación siguiente — cálculo automático")

st.warning(
    "El sistema usa automáticamente la fecha del escrito como fecha base. "
    "Este resultado es estimado: jurídicamente el término puede comenzar con "
    "la notificación, recepción, ejecutoria o una regla especial."
)


def document_date_from_pages(
    pages: list[PageTrace],
) -> tuple[date | None, str]:
    """
    Detecta la fecha principal incluso cuando está escrita así:
    Veintinueve (29) de julio de dos mil veintiséis (2026).
    """
    full_text = "\n".join(
        page.text or ""
        for page in pages
    )

    clean = norm(full_text)

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

    candidates: list[tuple[int, date, str]] = []

    # Caso principal del Auto 916:
    # "(29) de julio de ... (2026)"
    parenthetical_pattern = (
        r"\((?P<day>[0-3]?\d)\)\s+de\s+"
        r"(?P<month>"
        + "|".join(months.keys())
        + r")\s+de\s+[^()\n]{0,100}"
        r"\((?P<year>(?:19|20)\d{2})\)"
    )

    for match in re.finditer(
        parenthetical_pattern,
        clean,
        flags=re.IGNORECASE,
    ):
        try:
            value = date(
                int(match.group("year")),
                months[match.group("month")],
                int(match.group("day")),
            )

            candidates.append(
                (
                    match.start(),
                    value,
                    "Fecha judicial con día y año entre paréntesis",
                )
            )
        except ValueError:
            pass

    # "(29) de julio de 2026"
    mixed_pattern = (
        r"\((?P<day>[0-3]?\d)\)\s+de\s+"
        r"(?P<month>"
        + "|".join(months.keys())
        + r")\s+de\s+"
        r"(?P<year>(?:19|20)\d{2})"
    )

    for match in re.finditer(
        mixed_pattern,
        clean,
        flags=re.IGNORECASE,
    ):
        try:
            value = date(
                int(match.group("year")),
                months[match.group("month")],
                int(match.group("day")),
            )

            candidates.append(
                (
                    match.start(),
                    value,
                    "Fecha con día entre paréntesis",
                )
            )
        except ValueError:
            pass

    # "29 de julio de 2026"
    textual_pattern = (
        r"\b(?P<day>[0-3]?\d)\s+de\s+"
        r"(?P<month>"
        + "|".join(months.keys())
        + r")\s+de\s+"
        r"(?P<year>(?:19|20)\d{2})\b"
    )

    for match in re.finditer(
        textual_pattern,
        clean,
        flags=re.IGNORECASE,
    ):
        try:
            value = date(
                int(match.group("year")),
                months[match.group("month")],
                int(match.group("day")),
            )

            candidates.append(
                (
                    match.start(),
                    value,
                    "Fecha textual localizada",
                )
            )
        except ValueError:
            pass

    # "29/07/2026" o "29-07-2026"
    numeric_pattern = (
        r"\b(?P<day>[0-3]?\d)[/-]"
        r"(?P<month>[01]?\d)[/-]"
        r"(?P<year>(?:19|20)\d{2})\b"
    )

    for match in re.finditer(
        numeric_pattern,
        clean,
    ):
        try:
            value = date(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            )

            candidates.append(
                (
                    match.start(),
                    value,
                    "Fecha numérica localizada",
                )
            )
        except ValueError:
            pass

    if not candidates:
        return (
            None,
            "No se encontró una fecha válida en el texto extraído",
        )

    # La primera fecha válida del documento normalmente es la del encabezado.
    candidates.sort(
        key=lambda item: item[0]
    )

    _, selected, reason = candidates[0]

    return selected, reason

document_date, document_date_reason = document_date_from_pages(pages)
automatic_results = []

if document_date is None:
    st.error(
        "No se encontró automáticamente la fecha del escrito."
    )

    st.markdown("### Fecha de respaldo")

    fallback_date = st.date_input(
        "Confirma la fecha que aparece en el encabezado",
        value=date.today(),
        key="fallback_document_date",
    )

    use_fallback = st.checkbox(
        "Usar esta fecha para el cálculo",
        value=False,
        key="use_fallback_document_date",
    )

    with st.expander("Ver texto inicial leído por el sistema"):
        initial_text = "\n".join(
            (page.text or "")[:1200]
            for page in pages[:2]
        )
        st.code(initial_text)

    if use_fallback:
        document_date = fallback_date
        document_date_reason = (
            "Fecha confirmada manualmente porque no fue detectada en el texto"
        )

if document_date is not None:
    st.success(
        f"Fecha del escrito detectada automáticamente: "
        f"{document_date:%d/%m/%Y}"
    )
    st.caption(document_date_reason)

    for _, row in edited.iterrows():
        quantity = int(row.get("Cantidad", 0))

        if quantity <= 0:
            continue

        unit = str(row.get("Unidad", "Días"))
        detected_day_rule = str(
            row.get("Tipo de días", "Por confirmar")
        )

        if unit == "Horas":
            day_rule = "Hábiles"
        elif detected_day_rule in {"Hábiles", "Calendario"}:
            day_rule = detected_day_rule
        else:
            day_rule = "Hábiles"

        document_datetime = datetime.combine(
            document_date,
            time(8, 0),
        )

        start, deadline = calculate_deadline(
            notification=document_datetime,
            quantity=quantity,
            unit=unit,
            day_rule=day_rule,
            start_rule="Comienza al día siguiente",
            excluded=set(),
        )

        color, deadline_state, remaining_hours = status(deadline)

        automatic_results.append(
            {
                "Documento": row.get("Documento", ""),
                "Página": row.get("Página", ""),
                "Clase de término": row.get("Clase de término", ""),
                "Fecha del escrito usada": document_datetime,
                "Inicio estimado": start,
                "Cantidad": quantity,
                "Unidad": unit,
                "Regla automática": day_rule,
                "Vencimiento estimado": deadline,
                "Semáforo": color,
                "Estado": deadline_state,
                "Horas restantes": round(remaining_hours, 1),
                "Actuación exigida": row.get(
                    "Actuación exigida",
                    "",
                ),
                "Actuación que puede continuar": continuation(
                    row,
                    deadline_state,
                ),
                "Advertencia": (
                    "Cálculo efectuado con la fecha del escrito. "
                    "Confirmar la fecha real de notificación antes de actuar."
                ),
            }
        )

    automatic_results_df = pd.DataFrame(
        automatic_results
    )

    if automatic_results_df.empty:
        st.warning(
            "Se encontró la fecha del escrito, pero no un término completo para calcular."
        )
    else:
        st.dataframe(
            automatic_results_df,
            use_container_width=True,
            hide_index=True,
        )

        for _, result in automatic_results_df.iterrows():
            icon = {
                "Rojo": "🔴",
                "Amarillo": "🟡",
                "Verde": "🟢",
            }.get(result["Semáforo"], "⚪")

            st.info(
                f"{icon} **{result['Clase de término']}**\n\n"
                f"**Fecha del escrito usada:** "
                f"{result['Fecha del escrito usada']:%d/%m/%Y}\n\n"
                f"**Inicio estimado:** "
                f"{result['Inicio estimado']:%d/%m/%Y %H:%M}\n\n"
                f"**Vencimiento estimado:** "
                f"{result['Vencimiento estimado']:%d/%m/%Y %H:%M}\n\n"
                f"**Estado:** {result['Estado']}\n\n"
                f"**Actuación siguiente:** "
                f"{result['Actuación que puede continuar']}"
            )

        st.session_state["expiry_action_results"] = automatic_results_df


st.subheader("Exportar")

results_df = st.session_state.get(
    "expiry_action_results",
    pd.DataFrame(),
)

excel = io.BytesIO()

with pd.ExcelWriter(excel, engine="openpyxl") as writer:
    edited.to_excel(
        writer,
        sheet_name="Términos detectados",
        index=False,
    )
    results_df.to_excel(
        writer,
        sheet_name="Vencimientos y actuación",
        index=False,
    )

    st.session_state.get(
        "automatic_expiry_results",
        pd.DataFrame(),
    ).to_excel(
        writer,
        sheet_name="Cálculo automático",
        index=False,
    )

st.download_button(
    "Descargar análisis en Excel",
    data=excel.getvalue(),
    file_name="terminos_vencimientos_actuaciones.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)




