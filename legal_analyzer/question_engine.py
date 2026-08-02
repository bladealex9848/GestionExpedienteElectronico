from __future__ import annotations

import math
import re
from collections import Counter

from .models import PageTrace
from .text_utils import meaningful_words, normalize, split_fragments


LEGAL_INTENTS = {
    "orden": (
        "orden", "ordeno", "ordenar", "resuelve", "dispone", "requiere",
    ),
    "cumplimiento": (
        "cumplimiento", "cumplio", "entrega", "autorizacion", "realizo",
    ),
    "plazo": (
        "plazo", "termino", "horas", "dias", "vencimiento", "oportunidad",
    ),
    "respuesta": (
        "respuesta", "respondio", "peticion", "solicitud", "pregunta",
    ),
    "prueba": (
        "prueba", "anexo", "acta", "constancia", "concepto", "certificacion",
    ),
    "contradiccion": (
        "contradiccion", "inconsistencia", "diferencia", "version",
    ),
    "ultima_actuacion": (
        "ultima", "reciente", "actuacion", "fecha", "cronologia",
    ),
}


def _intent_bonus(question: str, fragment: str) -> float:
    q = normalize(question)
    f = normalize(fragment)
    bonus = 0.0

    for terms in LEGAL_INTENTS.values():
        if any(term in q for term in terms):
            hits = sum(term in f for term in terms)
            bonus += min(0.20, hits * 0.04)

    return bonus


def _idf(documents: list[set[str]]) -> dict[str, float]:
    total = max(len(documents), 1)
    frequencies: Counter[str] = Counter()

    for words in documents:
        for word in words:
            frequencies[word] += 1

    return {
        word: math.log((total + 1) / (count + 1)) + 1
        for word, count in frequencies.items()
    }


def build_fragment_index(
    documents: dict[str, list[PageTrace]],
) -> list[dict]:
    fragments: list[dict] = []

    for document_name, pages in documents.items():
        for page in pages:
            for fragment_number, fragment in enumerate(
                split_fragments(page.text, min_length=35),
                start=1,
            ):
                words = meaningful_words(fragment)

                if not words:
                    continue

                fragments.append(
                    {
                        "document": document_name,
                        "page": page.page,
                        "fragment_number": fragment_number,
                        "fragment": fragment[:1600],
                        "words": words,
                        "method": page.extraction_method,
                        "ocr_confidence": page.ocr_confidence,
                    }
                )

    word_sets = [item["words"] for item in fragments]
    idf = _idf(word_sets)

    for item in fragments:
        item["vector"] = {
            word: idf.get(word, 1.0)
            for word in item["words"]
        }

    return fragments


def _weighted_overlap(
    question_words: set[str],
    fragment_vector: dict[str, float],
) -> float:
    if not question_words or not fragment_vector:
        return 0.0

    numerator = sum(
        fragment_vector[word]
        for word in question_words
        if word in fragment_vector
    )

    denominator = sum(
        fragment_vector.get(word, 1.0)
        for word in question_words
    )

    return numerator / max(denominator, 1e-9)


def answer_question(
    question: str,
    index: list[dict],
    top_k: int = 5,
) -> dict:
    question_words = meaningful_words(question)

    scored: list[dict] = []

    for item in index:
        score = _weighted_overlap(
            question_words,
            item["vector"],
        )
        score += _intent_bonus(
            question,
            item["fragment"],
        )

        if score <= 0:
            continue

        scored.append(
            {
                **item,
                "score": min(1.0, score),
            }
        )

    scored.sort(
        key=lambda row: row["score"],
        reverse=True,
    )

    top = scored[:top_k]

    if not top or top[0]["score"] < 0.10:
        return {
            "answer": (
                "No encontré evidencia documental suficiente para responder "
                "con seguridad."
            ),
            "confidence": 0.0,
            "sources": [],
            "status": "Sin evidencia suficiente",
        }

    best = top[0]
    confidence = round(
        min(
            100.0,
            (
                best["score"] * 70
                + min(len(top), 3) * 6
                + (
                    8
                    if best["ocr_confidence"] is None
                    or best["ocr_confidence"] >= 70
                    else 0
                )
            ),
        ),
        1,
    )

    answer = best["fragment"]

    if len(top) >= 2 and top[1]["score"] >= best["score"] * 0.72:
        answer += (
            "\n\nTambién existe otra pieza relacionada que conviene revisar: "
            + top[1]["fragment"][:500]
        )

    return {
        "answer": answer,
        "confidence": confidence,
        "sources": top,
        "status": (
            "Evidencia fuerte"
            if confidence >= 75
            else "Evidencia moderada"
            if confidence >= 50
            else "Evidencia débil"
        ),
    }


def suggested_questions(
    documents: dict[str, list[PageTrace]],
) -> list[str]:
    suggestions = [
        "¿Qué ordenó exactamente el juez?",
        "¿Cuál fue el plazo fijado para cumplir?",
        "¿Qué pruebas existen sobre el cumplimiento?",
        "¿Qué solicitudes no fueron respondidas?",
        "¿Cuál es la última actuación del expediente?",
        "¿Dónde aparece el radicado del proceso?",
        "¿Qué documentos mencionan una entrega o autorización?",
        "¿Hay contradicciones entre las respuestas de las entidades?",
    ]

    names = " ".join(documents.keys()).lower()

    if "desacato" in names:
        suggestions.insert(
            0,
            "¿Qué incumplimientos sustentan el incidente de desacato?",
        )

    if "peticion" in names:
        suggestions.insert(
            0,
            "¿Cuáles preguntas del derecho de petición siguen sin respuesta?",
        )

    return suggestions[:10]
