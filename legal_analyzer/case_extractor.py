from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

from .models import PageTrace
from .text_utils import clean_text, normalize


MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

TYPES = {
    "Derecho de petición": ("derecho de peticion", "ley 1755", "peticion respetuosa"),
    "Acción de tutela": ("accion de tutela", "decreto 2591", "solicitud de amparo"),
    "Auto admisorio": ("auto admisorio", "correr traslado"),
    "Contestación": ("contestacion", "respuesta a la accion", "informe rendido"),
    "Fallo de tutela": ("fallo de tutela", "administrando justicia", "resuelve"),
    "Impugnación": ("impugnacion", "segunda instancia"),
    "Incidente de desacato": ("incidente de desacato", "incumplimiento del fallo"),
    "Auto de requerimiento": ("auto de requerimiento", "requierase"),
    "Respuesta de cumplimiento": ("informe de cumplimiento", "se dio cumplimiento"),
    "Notificación o constancia": ("constancia de notificacion", "constancia de envio"),
}


def joined_text(pages: list[PageTrace]) -> str:
    return clean_text("\n".join(page.text for page in pages))


def classify_document(pages: list[PageTrace]) -> tuple[str, int]:
    text = normalize(joined_text(pages))
    best, score_best = "Documento no clasificado", 0
    for kind, expressions in TYPES.items():
        score = sum(exp in text for exp in expressions)
        if score > score_best:
            best, score_best = kind, score
    return best, score_best


def extract_dates(text: str) -> list[str]:
    text_n = normalize(text)
    dates = []
    for d, m, y in re.findall(r"\b([0-3]?\d)[/-]([01]?\d)[/-]((?:19|20)\d{2})\b", text_n):
        try:
            dates.append(datetime(int(y), int(m), int(d)).strftime("%Y-%m-%d"))
        except ValueError:
            pass
    pattern = r"\b([0-3]?\d)\s+de\s+(" + "|".join(MONTHS) + r")\s+de\s+((?:19|20)\d{2})\b"
    for d, month, y in re.findall(pattern, text_n):
        try:
            dates.append(datetime(int(y), MONTHS[month], int(d)).strftime("%Y-%m-%d"))
        except ValueError:
            pass
    return list(dict.fromkeys(dates))


def extract_radicado(text: str) -> str:
    patterns = [
        r"\b\d{2}[-\s]\d{3}[-\s]\d{2}[-\s]\d{2}[-\s]\d{3}[-\s]\d{4}[-\s]\d{5}[-\s]\d{2}\b",
        r"\b\d{23}\b",
        r"radicaci[oó]n\s*[:#]?\s*([0-9\-\s]{15,35})",
        r"radicado\s*[:#]?\s*([0-9\-\s]{10,35})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1) if match.lastindex else match.group(0)
            return re.sub(r"\s+", "", value).strip(":- ")
    return ""


def after_label(text: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        match = re.search(rf"{label}\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()[:220]
    return ""


def extract_case_metadata(documents: dict[str, list[PageTrace]]) -> dict[str, str]:
    all_text = "\n".join(joined_text(pages) for pages in documents.values())
    radicados = [extract_radicado(joined_text(pages)) for pages in documents.values()]
    radicados = [x for x in radicados if x]
    common = Counter(radicados).most_common(1)[0][0] if radicados else ""
    return {
        "Radicado": common,
        "Juzgado": after_label(all_text, ("juzgado", "despacho judicial")),
        "Accionante": after_label(all_text, ("accionante", "actor", "demandante")),
        "Accionado": after_label(all_text, ("accionado", "accionada", "entidad accionada")),
        "Vinculados": after_label(all_text, ("vinculados", "entidades vinculadas")),
        "Derechos invocados": after_label(all_text, ("derechos vulnerados", "derechos fundamentales")),
    }


def build_timeline(documents: dict[str, list[PageTrace]]) -> list[dict]:
    rows = []
    for name, pages in documents.items():
        text = joined_text(pages)
        kind, confidence = classify_document(pages)
        dates = extract_dates(text)
        rows.append({
            "Fecha principal": dates[0] if dates else "",
            "Fechas detectadas": ", ".join(dates[:8]),
            "Documento": name,
            "Tipo": kind,
            "Confianza clasificación": confidence,
            "Radicado": extract_radicado(text),
            "Páginas": len(pages),
            "Métodos de lectura": ", ".join(sorted({p.extraction_method for p in pages})),
        })
    return rows
