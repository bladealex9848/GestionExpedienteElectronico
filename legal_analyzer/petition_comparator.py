from __future__ import annotations

import re

from .models import PageTrace
from .text_utils import normalize, split_fragments, text_similarity


MARKERS = (
    "solicito", "peticion", "peticiones", "pretensiones", "se sirva",
    "informar", "entregar", "remitir", "expedir", "certificar", "responder",
)

ANSWER_SIGNALS = (
    "en respuesta", "respecto de", "frente a", "se informa", "informamos",
    "se adjunta", "se remite", "se certifica", "no es posible", "no procede",
)


def extract_requests(pages: list[PageTrace]) -> list[dict]:
    rows, idx = [], 1
    for page in pages:
        for fragment in split_fragments(page.text, min_length=20):
            n = normalize(fragment)
            numbered = bool(re.match(
                r"^\s*(?:\d+|primero|segundo|tercero|cuarto|quinto)[\.\):\-]",
                fragment, flags=re.IGNORECASE
            ))
            if not (any(marker in n for marker in MARKERS) or numbered):
                continue
            rows.append({
                "N.º": idx,
                "Solicitud": fragment[:1200],
                "Documento solicitud": page.document,
                "Página solicitud": page.page,
            })
            idx += 1
    return rows[:60]


def compare_requests_with_answers(requests: list[dict], pages: list[PageTrace]) -> list[dict]:
    results = []
    for request in requests:
        best = {"score": 0.0, "document": "", "page": "", "fragment": "", "signal": False}
        for page in pages:
            for fragment in split_fragments(page.text):
                score = text_similarity(request["Solicitud"], fragment)
                if score <= best["score"]:
                    continue
                n = normalize(fragment)
                best = {
                    "score": score,
                    "document": page.document,
                    "page": page.page,
                    "fragment": fragment[:1200],
                    "signal": any(signal in n for signal in ANSWER_SIGNALS),
                }
        if best["score"] >= 0.16 and best["signal"]:
            status = "Posible respuesta de fondo"
        elif best["score"] >= 0.10:
            status = "Respuesta parcial o relacionada"
        elif best["score"] >= 0.055:
            status = "Coincidencia débil; revisar"
        else:
            status = "Sin respuesta localizada"

        results.append({
            **request,
            "Respuesta localizada": best["fragment"],
            "Documento respuesta": best["document"],
            "Página respuesta": best["page"],
            "Coincidencia": f"{best['score'] * 100:.1f}%",
            "Evaluación automática": status,
            "Evaluación revisada": status,
            "Observaciones": "",
        })
    return results
