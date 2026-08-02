from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable

from legal_analyzer.models import PageTrace


STOPWORDS = {
    "para", "como", "este", "esta", "esto", "desde", "hasta", "entre",
    "sobre", "donde", "cuando", "cual", "porque", "tambien", "debe",
    "puede", "tiene", "haber", "hacer", "ante", "bajo", "segun", "sin",
    "con", "por", "del", "las", "los", "una", "uno", "que", "sus",
}

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

TOPICS = {
    "cumplimiento": (
        "cumplimiento", "incumplimiento", "cumplio", "no cumplio",
        "dar cumplimiento",
    ),
    "respuesta": (
        "respuesta", "respondio", "no respondio", "sin respuesta",
        "pronunciamiento",
    ),
    "notificacion": (
        "notificacion", "notificado", "no notificado", "correo electronico",
        "mensaje de datos",
    ),
    "entrega": (
        "entrega", "entregado", "no entregado", "suministro",
    ),
    "decision": (
        "decision", "decidir", "sin decidir", "pendiente de decision",
        "pase a despacho",
    ),
    "dictamen": (
        "dictamen", "concepto medico", "informe medico",
    ),
    "expediente": (
        "expediente", "radicado", "proceso",
    ),
}

NEGATIVE_MARKERS = (
    "no ", "sin ", "nunca", "incumpl", "omit", "pendiente",
    "vencido", "extemporaneo", "falt",
)

POSITIVE_MARKERS = (
    "si ", "cumplio", "entrego", "respondio", "notifico",
    "acredito", "aporto", "realizo",
)

CONDUCT_RULES = [
    {
        "name": "Mora o inactividad aparente",
        "phrases": (
            "pendiente de decision", "sin decidir", "sin resolver",
            "se encuentra a despacho", "pase a despacho",
            "vencido el termino", "mora",
        ),
        "norm": "Ley 270 de 1996, artículos 4 y 7; Acuerdo PSAA11-8716 de 2011",
        "verification": "Confirmar última actuación, término aplicable y justificación de la demora.",
    },
    {
        "name": "Falta de trámite de solicitud o memorial",
        "phrases": (
            "memorial de impulso", "solicitud de decision",
            "solicitud sin respuesta", "no se dio tramite",
        ),
        "norm": "Constitución Política, artículos 29 y 229; Ley 270 de 1996",
        "verification": "Aportar memorial, constancia de recepción y consulta posterior.",
    },
    {
        "name": "Notificación posiblemente defectuosa",
        "phrases": (
            "sin constancia de notificacion", "no fue notificado",
            "correo electronico", "mensaje de datos",
        ),
        "norm": "Norma procesal especial; Ley 2213 de 2022, artículo 8, cuando aplique",
        "verification": "Revisar envío, entrega, acceso y fecha efectiva de notificación.",
    },
    {
        "name": "Seguimiento insuficiente del cumplimiento de tutela",
        "phrases": (
            "incidente de desacato", "incumplimiento del fallo",
            "continua el incumplimiento", "no se cumplio la tutela",
        ),
        "norm": "Decreto 2591 de 1991, artículos 27 y 52",
        "verification": "Comparar orden, obligado, plazo, cumplimiento material y medidas adoptadas.",
    },
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


def sentence_split(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[.;:!?])\s+|\n+", text or "")
        if len(item.strip()) >= 25
    ]


def token_set(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\b[a-z0-9]{4,}\b", normalize(text))
        if token not in STOPWORDS
    }


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


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

    textual = (
        r"\b([0-3]?\d)\s+de\s+("
        + "|".join(MONTHS.keys())
        + r")\s+de\s+((?:19|20)\d{2})\b"
    )

    for day, month_name, year in re.findall(textual, clean):
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
    values = []
    for pattern in (
        r"\b\d{2}-\d{3}-\d{2}-\d{2}-\d{3}-\d{4}-\d{5}-\d{2}\b",
        r"\b\d{23}\b",
    ):
        values.extend(re.findall(pattern, text or ""))
    return list(dict.fromkeys(values))


def extract_terms(page: PageTrace) -> list[dict]:
    rows = []
    word_pattern = (
        "cuarenta y ocho|treinta|veinte|quince|diez|nueve|ocho|"
        "siete|seis|cinco|cuatro|tres|dos|un|uno|una"
    )
    pattern = (
        rf"(?:dentro de|por el termino de|termino(?: \w+){{0,5}} de|"
        rf"plazo(?: \w+){{0,5}} de)\s+"
        rf"(?P<number>{word_pattern}|\d{{1,3}})\s*"
        rf"(?P<unit>horas?|dias?)"
        rf"(?:\s*\((?P<paren>\d{{1,3}})\)\s*(?:horas?|dias?)?)?"
    )

    page_dates = extract_dates(page.text)
    base_date = page_dates[0] if page_dates else None

    for fragment in sentence_split(page.text):
        clean = normalize(fragment)
        match = re.search(pattern, clean)
        if not match:
            continue

        raw = match.group("number")
        parenthetical = match.groupdict().get("paren")
        quantity = (
            int(parenthetical)
            if parenthetical
            else int(raw)
            if raw.isdigit()
            else NUMBER_WORDS.get(raw)
        )

        if quantity is None:
            continue

        unit = "Horas" if "hora" in match.group("unit") else "Días"
        day_type = (
            "Calendario"
            if "calendario" in clean
            else "Hábiles"
        )

        start = None
        deadline = None

        if base_date:
            start = datetime.combine(base_date + timedelta(days=1), datetime.min.time())

            if unit == "Horas":
                deadline = start + timedelta(hours=quantity)
            elif day_type == "Calendario":
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
            "Documento": page.document,
            "Página": page.page,
            "Fragmento": fragment,
            "Cantidad": quantity,
            "Unidad": unit,
            "Tipo de días": day_type,
            "Fecha base": base_date,
            "Inicio estimado": start,
            "Vencimiento estimado": deadline,
            "Estado": (
                "Vencido"
                if deadline and deadline < datetime.now()
                else "En plazo o por confirmar"
            ),
            "Confianza": 70 if base_date else 45,
            "Advertencia": (
                "Confirmar notificación, ejecutoria, festivos y norma especial."
            ),
        })

    return rows


def build_claims(pages: list[PageTrace]) -> list[dict]:
    claims = []

    for page in pages:
        for fragment in sentence_split(page.text):
            clean = normalize(fragment)
            polarity = (
                "Negativa"
                if any(marker in clean for marker in NEGATIVE_MARKERS)
                else "Positiva"
                if any(marker in clean for marker in POSITIVE_MARKERS)
                else "Neutra"
            )

            topics = [
                topic
                for topic, phrases in TOPICS.items()
                if any(phrase in clean for phrase in phrases)
            ]

            if topics:
                claims.append({
                    "Documento": page.document,
                    "Página": page.page,
                    "Fragmento": fragment,
                    "Polaridad": polarity,
                    "Temas": topics,
                    "Tokens": token_set(fragment),
                })

    return claims


def detect_contradictions(claims: list[dict]) -> list[dict]:
    rows = []

    for index, left in enumerate(claims):
        for right in claims[index + 1:]:
            if left["Documento"] == right["Documento"] and left["Página"] == right["Página"]:
                continue

            shared_topics = set(left["Temas"]) & set(right["Temas"])
            if not shared_topics:
                continue

            if {left["Polaridad"], right["Polaridad"]} != {"Positiva", "Negativa"}:
                continue

            similarity = jaccard(left["Tokens"], right["Tokens"])
            if similarity < 0.08:
                continue

            rows.append({
                "Tema": ", ".join(sorted(shared_topics)),
                "Documento versión 1": left["Documento"],
                "Página versión 1": left["Página"],
                "Versión 1": left["Fragmento"],
                "Documento versión 2": right["Documento"],
                "Página versión 2": right["Página"],
                "Versión 2": right["Fragmento"],
                "Similitud temática": round(similarity * 100),
                "Qué debe revisarse": (
                    "Determinar cuál versión está respaldada por constancia, prueba "
                    "o actuación posterior."
                ),
            })

    return rows


def detect_errors(pages: list[PageTrace]) -> list[dict]:
    rows = []
    documents = defaultdict(list)

    for page in pages:
        documents[page.document].append(page)

    all_radications = defaultdict(list)

    for document, document_pages in documents.items():
        full_text = "\n".join(page.text or "" for page in document_pages)
        clean = normalize(full_text)
        radications = extract_radications(full_text)

        for radicado in radications:
            all_radications[radicado].append(document)

        if len(radications) > 1:
            rows.append({
                "Documento": document,
                "Página": "Varias",
                "Categoría": "Identificación",
                "Posible error": "Más de un radicado en el mismo archivo",
                "Severidad": "Alta",
                "Evidencia": " / ".join(radications),
                "Norma posible": "Constitución Política, artículo 29",
                "Verificación necesaria": "Comparar carátula, antecedentes y expediente oficial.",
            })

        technical = [
            token
            for token in (
                "phonak sky", "phonak naida", "naida lumity",
                "sky l90", "l90-up", "up l90",
            )
            if token in clean
        ]

        if len(set(technical)) >= 2:
            rows.append({
                "Documento": document,
                "Página": "Varias",
                "Categoría": "Fáctico",
                "Posible error": "Confusión del objeto ordenado, autorizado o entregado",
                "Severidad": "Alta",
                "Evidencia": " / ".join(sorted(set(technical))),
                "Norma posible": "Constitución Política, artículo 29",
                "Verificación necesaria": (
                    "Comparar prescripción, fallo, autorización, ficha técnica y entrega."
                ),
            })

        if any(term in clean for term in ("no obra prueba", "no se acredito", "no se aporto")):
            if any(term in clean for term in ("anexo", "dictamen", "constancia", "historia clinica")):
                rows.append({
                    "Documento": document,
                    "Página": "Varias",
                    "Categoría": "Probatorio",
                    "Posible error": "Posible omisión de prueba relevante",
                    "Severidad": "Alta",
                    "Evidencia": "El archivo niega acreditación y también menciona soportes.",
                    "Norma posible": "Constitución Política, artículo 29",
                    "Verificación necesaria": "Revisar índice, anexos y valoración expresa.",
                })

    if len(all_radications) > 1:
        rows.append({
            "Documento": "Comparación del expediente",
            "Página": "Varias",
            "Categoría": "Identificación",
            "Posible error": "Documentos de procesos distintos mezclados",
            "Severidad": "Alta",
            "Evidencia": "; ".join(
                f"{rad}: {', '.join(files)}"
                for rad, files in all_radications.items()
            ),
            "Norma posible": "Constitución Política, artículo 29",
            "Verificación necesaria": "Separar los archivos por radicado.",
        })

    return rows


def detect_conducts(pages: list[PageTrace]) -> list[dict]:
    rows = []

    for page in pages:
        clean = normalize(page.text)

        for rule in CONDUCT_RULES:
            hits = [phrase for phrase in rule["phrases"] if phrase in clean]
            if not hits:
                continue

            fragments = [
                fragment
                for fragment in sentence_split(page.text)
                if any(hit in normalize(fragment) for hit in hits)
            ]

            rows.append({
                "Documento": page.document,
                "Página": page.page,
                "Conducta posible": rule["name"],
                "Coincidencias": " | ".join(hits),
                "Fragmento": fragments[0] if fragments else "",
                "Norma o marco": rule["norm"],
                "Cómo comprobarla": rule["verification"],
            })

    return rows


def answer_question(question: str, pages: list[PageTrace], limit: int = 8) -> dict:
    query_tokens = token_set(question)
    candidates = []

    for page in pages:
        for fragment in sentence_split(page.text):
            fragment_tokens = token_set(fragment)
            overlap = len(query_tokens & fragment_tokens)
            similarity = jaccard(query_tokens, fragment_tokens)

            topic_bonus = sum(
                1
                for phrases in TOPICS.values()
                if any(phrase in normalize(question) and phrase in normalize(fragment) for phrase in phrases)
            )

            score = overlap * 3 + similarity * 10 + topic_bonus * 2

            if score > 0:
                candidates.append({
                    "Documento": page.document,
                    "Página": page.page,
                    "Fragmento": fragment,
                    "Puntaje": round(score, 2),
                })

    candidates.sort(key=lambda item: item["Puntaje"], reverse=True)
    evidence = candidates[:limit]

    if not evidence:
        return {
            "Respuesta": (
                "No se encontró evidencia suficiente para responder con los documentos cargados."
            ),
            "Evidencia": [],
            "Confianza": 0,
        }

    confidence = min(95, round(40 + evidence[0]["Puntaje"] * 5))
    answer = (
        "La evidencia documental más relacionada indica: "
        + " ".join(item["Fragmento"] for item in evidence[:3])
        + " La conclusión debe verificarse con el documento completo y el estado actual del proceso."
    )

    return {
        "Respuesta": answer,
        "Evidencia": evidence,
        "Confianza": confidence,
    }


def analyze(pages: list[PageTrace]) -> dict:
    terms = []
    for page in pages:
        terms.extend(extract_terms(page))

    claims = build_claims(pages)
    contradictions = detect_contradictions(claims)
    errors = detect_errors(pages)
    conducts = detect_conducts(pages)

    expired = sum(1 for item in terms if item["Estado"] == "Vencido")
    high_errors = sum(1 for item in errors if item["Severidad"] == "Alta")

    score_terms = min(30, expired * 15)
    score_errors = min(30, high_errors * 15)
    score_contradictions = min(20, len(contradictions) * 10)
    score_conducts = min(20, len(conducts) * 10)
    score = min(
        100,
        score_terms + score_errors + score_contradictions + score_conducts,
    )

    color = "Rojo" if score >= 65 else "Amarillo" if score >= 30 else "Verde"

    return {
        "terms": terms,
        "contradictions": contradictions,
        "errors": errors,
        "conducts": conducts,
        "score": score,
        "color": color,
        "score_components": {
            "Términos vencidos": score_terms,
            "Errores graves": score_errors,
            "Contradicciones": score_contradictions,
            "Conductas": score_conducts,
        },
    }
