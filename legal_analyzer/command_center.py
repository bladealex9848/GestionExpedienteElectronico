from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .case_extractor import classify_document
from .models import PageTrace
from .petition_comparator import compare_requests_with_answers, extract_requests
from .text_utils import normalize, split_fragments


NEGATIONS = (
    "no se entrego",
    "no fue entregado",
    "no se realizo",
    "no se autorizo",
    "no se respondio",
    "no se cumplio",
    "no existe",
    "no obra",
    "no consta",
    "pendiente",
    "incumplimiento",
)

AFFIRMATIONS = (
    "se entrego",
    "fue entregado",
    "se realizo",
    "se autorizo",
    "se respondio",
    "se cumplio",
    "se dio cumplimiento",
    "obra constancia",
    "se adjunta",
    "se aporta",
)

IMPORTANT_TERMS = (
    "entrega",
    "autorizacion",
    "audifono",
    "medicamento",
    "respuesta",
    "tratamiento",
    "valoracion",
    "cita",
    "pago",
    "reintegro",
    "expediente",
    "concepto medico",
    "notificacion",
)

REVIEW_GUIDE = {
    "entrega": {
        "importance": (
            "La entrega material no puede darse por demostrada únicamente con una afirmación."
        ),
        "review": (
            "Acta firmada, fecha, persona que recibió, identificación del bien, "
            "modelo, cantidad, estado y constancia de recibido."
        ),
        "missing": (
            "Acta de entrega o soporte equivalente que permita verificar quién recibió, "
            "qué recibió y cuándo."
        ),
    },
    "autorizacion": {
        "importance": (
            "Una autorización no demuestra por sí sola que el servicio se haya prestado."
        ),
        "review": (
            "Número de autorización, vigencia, prestador asignado, servicio exacto, "
            "fecha de expedición y prueba de ejecución."
        ),
        "missing": (
            "Autorización completa y soporte de que el servicio autorizado fue efectivamente prestado."
        ),
    },
    "audifono": {
        "importance": (
            "Puede existir diferencia entre el dispositivo prescrito, autorizado y entregado."
        ),
        "review": (
            "Marca, modelo, referencia, características, serial, fórmula médica, "
            "concepto del médico tratante y acta de entrega."
        ),
        "missing": (
            "Prueba técnica que permita comparar el audífono prescrito con el realmente entregado."
        ),
    },
    "medicamento": {
        "importance": (
            "La autorización o despacho parcial no equivale necesariamente al suministro completo."
        ),
        "review": (
            "Nombre, dosis, cantidad, periodicidad, fechas de entrega, fórmula vigente "
            "y continuidad del tratamiento."
        ),
        "missing": (
            "Soporte completo del suministro conforme a la prescripción médica."
        ),
    },
    "respuesta": {
        "importance": (
            "Una respuesta puede existir formalmente y aun así ser incompleta, evasiva o incongruente."
        ),
        "review": (
            "Cada solicitud formulada, respuesta concreta, documentos anexos, fecha de envío, "
            "fecha de recepción y competencia de quien respondió."
        ),
        "missing": (
            "Respuesta expresa, completa y verificable frente a cada punto solicitado."
        ),
    },
    "tratamiento": {
        "importance": (
            "El cumplimiento debe revisarse de manera integral y no solo frente a una actuación aislada."
        ),
        "review": (
            "Continuidad, oportunidad, órdenes médicas, citas, autorizaciones, entregas, "
            "controles y barreras de acceso."
        ),
        "missing": (
            "Soportes que acrediten continuidad e integralidad del tratamiento."
        ),
    },
    "valoracion": {
        "importance": (
            "La sola programación de una valoración no demuestra que haya sido realizada."
        ),
        "review": (
            "Fecha programada, asistencia, profesional tratante, resultado, recomendaciones "
            "y órdenes derivadas."
        ),
        "missing": (
            "Historia o concepto que acredite la realización efectiva de la valoración."
        ),
    },
    "cita": {
        "importance": (
            "Asignar una cita no equivale a prestar efectivamente el servicio."
        ),
        "review": (
            "Fecha, hora, prestador, asistencia, cancelaciones, reprogramaciones y resultado."
        ),
        "missing": (
            "Constancia de atención o historia clínica de la cita efectivamente realizada."
        ),
    },
    "pago": {
        "importance": (
            "El anuncio de pago no demuestra que los recursos hayan sido recibidos."
        ),
        "review": (
            "Comprobante bancario, fecha, valor, beneficiario, referencia y concepto del pago."
        ),
        "missing": (
            "Soporte financiero verificable del pago o transferencia."
        ),
    },
    "reintegro": {
        "importance": (
            "La aprobación del reintegro no acredita que el dinero haya sido desembolsado."
        ),
        "review": (
            "Valor aprobado, fecha de giro, cuenta receptora, comprobante y fecha de disponibilidad."
        ),
        "missing": (
            "Comprobante de desembolso y recepción efectiva del reintegro."
        ),
    },
    "expediente": {
        "importance": (
            "La remisión incompleta del expediente puede impedir el ejercicio de defensa y seguimiento."
        ),
        "review": (
            "Índice, memoriales, anexos, correos, constancias, autos, notificaciones "
            "y documentos mencionados pero ausentes."
        ),
        "missing": (
            "Copia íntegra y organizada del expediente electrónico."
        ),
    },
    "concepto medico": {
        "importance": (
            "Debe verificarse que el concepto provenga del profesional competente y se base en valoración suficiente."
        ),
        "review": (
            "Identidad del médico, especialidad, adscripción, fecha, examen del paciente, "
            "fundamento clínico y relación con la orden judicial."
        ),
        "missing": (
            "Concepto médico completo, firmado y sustentado clínicamente."
        ),
    },
    "notificacion": {
        "importance": (
            "La fecha de notificación puede determinar el inicio de términos y la validez de actuaciones."
        ),
        "review": (
            "Medio utilizado, destinatario, fecha y hora, acuse, dirección correcta y anexos remitidos."
        ),
        "missing": (
            "Constancia completa de notificación o recepción."
        ),
    },
}


@dataclass
class RiskResult:
    score: int
    level: str
    reasons: list[str]
    next_actions: list[str]


def flatten_pages(documents: dict[str, list[PageTrace]]) -> list[PageTrace]:
    return [page for pages in documents.values() for page in pages]


def document_inventory(documents: dict[str, list[PageTrace]]) -> Counter:
    return Counter(
        classify_document(pages)[0]
        for pages in documents.values()
    )


def _build_explanation(shared_topics: list[str]) -> dict[str, str]:
    topic = shared_topics[0] if shared_topics else "hecho discutido"
    guide = REVIEW_GUIDE.get(
        topic,
        {
            "importance": (
                "Las dos fuentes presentan versiones opuestas sobre un mismo hecho relevante."
            ),
            "review": (
                "Documento original, fecha, autor, anexos, contexto completo, "
                "firma, autenticidad y demás soportes relacionados."
            ),
            "missing": (
                "Prueba independiente que permita establecer cuál versión está respaldada."
            ),
        },
    )

    return {
        "Qué se contradice": (
            f"Las fuentes presentan versiones opuestas sobre: {', '.join(shared_topics)}."
        ),
        "Por qué importa": guide["importance"],
        "Todo lo que debe revisarse": guide["review"],
        "Prueba que puede faltar": guide["missing"],
        "Conclusión preliminar": (
            "No es posible determinar automáticamente cuál versión es correcta. "
            "Debe verificarse el contexto completo y la prueba de respaldo."
        ),
    }


def detect_contradictions(
    documents: dict[str, list[PageTrace]],
) -> list[dict]:
    statements: list[dict] = []

    for name, pages in documents.items():
        for page in pages:
            for fragment in split_fragments(page.text, min_length=20):
                normalized = normalize(fragment)

                polarity = ""
                if any(term in normalized for term in NEGATIONS):
                    polarity = "negativa"
                elif any(term in normalized for term in AFFIRMATIONS):
                    polarity = "afirmativa"

                if not polarity:
                    continue

                topics = [
                    term
                    for term in IMPORTANT_TERMS
                    if term in normalized
                ]

                if not topics:
                    continue

                statements.append(
                    {
                        "document": name,
                        "page": page.page,
                        "fragment": fragment.strip(),
                        "polarity": polarity,
                        "topics": topics,
                        "method": page.extraction_method,
                        "ocr_confidence": page.ocr_confidence,
                    }
                )

    contradictions: list[dict] = []
    seen: set[tuple] = set()

    for index, left in enumerate(statements):
        for right in statements[index + 1:]:
            if (
                left["document"] == right["document"]
                and left["page"] == right["page"]
            ):
                continue

            shared = sorted(
                set(left["topics"]).intersection(right["topics"])
            )

            if not shared or left["polarity"] == right["polarity"]:
                continue

            key = (
                left["document"],
                left["page"],
                left["fragment"],
                right["document"],
                right["page"],
                right["fragment"],
            )

            reverse_key = (
                right["document"],
                right["page"],
                right["fragment"],
                left["document"],
                left["page"],
                left["fragment"],
            )

            if key in seen or reverse_key in seen:
                continue

            seen.add(key)
            explanation = _build_explanation(shared)

            contradictions.append(
                {
                    "Tema": ", ".join(shared),
                    "Versión 1 completa": left["fragment"],
                    "Documento de la versión 1": left["document"],
                    "Página de la versión 1": left["page"],
                    "Fuente 1": f"{left['document']}, página {left['page']}",
                    "Método 1": left["method"],
                    "Confianza OCR 1": left["ocr_confidence"],
                    "Versión 2 completa": right["fragment"],
                    "Documento de la versión 2": right["document"],
                    "Página de la versión 2": right["page"],
                    "Fuente 2": f"{right['document']}, página {right['page']}",
                    "Método 2": right["method"],
                    "Confianza OCR 2": right["ocr_confidence"],
                    "Tipo de oposición": (
                        f"{left['polarity']} ↔ {right['polarity']}"
                    ),
                    **explanation,
                    "Conclusión revisada": "",
                    "Observaciones": "",
                }
            )

    return contradictions


def assess_risk(
    documents: dict[str, list[PageTrace]],
    quality_rows: list[dict],
) -> RiskResult:
    inventory = document_inventory(documents)
    reasons: list[str] = []
    actions: list[str] = []
    score = 0

    if inventory["Acción de tutela"] > 0 and inventory["Fallo de tutela"] == 0:
        score += 18
        reasons.append("Se identificó tutela, pero no fallo.")
        actions.append(
            "Verificar el estado del proceso y solicitar copia del fallo o del expediente."
        )

    if inventory["Fallo de tutela"] > 0 and inventory["Respuesta de cumplimiento"] == 0:
        score += 18
        reasons.append("Existe fallo sin respuesta de cumplimiento identificada.")
        actions.append(
            "Revisar las órdenes del fallo y solicitar prueba material de cumplimiento."
        )

    low_quality = sum(
        row.get("Calidad") == "Baja"
        for row in quality_rows
    )

    if low_quality:
        score += min(20, low_quality * 3)
        reasons.append(
            f"{low_quality} página(s) presentan calidad de lectura baja."
        )
        actions.append(
            "Revisar las páginas de baja calidad o reemplazarlas por copias más legibles."
        )

    petition_docs = [
        name
        for name, pages in documents.items()
        if classify_document(pages)[0] == "Derecho de petición"
    ]

    answer_pages = [
        page
        for name, pages in documents.items()
        if name not in petition_docs
        for page in pages
    ]

    unanswered = 0

    for petition_name in petition_docs:
        requests = extract_requests(documents[petition_name])
        comparison = compare_requests_with_answers(requests, answer_pages)

        unanswered += sum(
            row["Evaluación automática"] == "Sin respuesta localizada"
            for row in comparison
        )

    if unanswered:
        score += min(25, unanswered * 5)
        reasons.append(
            f"Se detectaron {unanswered} solicitud(es) sin respuesta localizada."
        )
        actions.append(
            "Contrastar cada pregunta con la respuesta y preparar la actuación correspondiente."
        )

    contradictions = detect_contradictions(documents)

    if contradictions:
        score += min(20, len(contradictions) * 4)
        reasons.append(
            f"Se detectaron {len(contradictions)} contradicción(es) potencial(es)."
        )
        actions.append(
            "Revisar cada contradicción, su explicación y todos los soportes indicados."
        )

    score = min(100, score)

    if score >= 70:
        level = "Crítico"
    elif score >= 45:
        level = "Alto"
    elif score >= 25:
        level = "Medio"
    else:
        level = "Bajo"

    if not reasons:
        reasons.append(
            "No se detectaron alertas estructurales graves con las reglas actuales."
        )

    if not actions:
        actions.append(
            "Completar la revisión humana y validar fechas, fuentes y anexos."
        )

    return RiskResult(
        score=score,
        level=level,
        reasons=reasons,
        next_actions=list(dict.fromkeys(actions)),
    )


def executive_summary(
    documents: dict[str, list[PageTrace]],
    risk: RiskResult,
    contradictions: list[dict],
) -> str:
    inventory = document_inventory(documents)
    inventory_text = ", ".join(
        f"{kind}: {count}"
        for kind, count in inventory.most_common()
    )

    return (
        f"Se analizaron {len(documents)} documentos. "
        f"Inventario procesal: {inventory_text or 'sin clasificación concluyente'}. "
        f"El nivel de riesgo preliminar es {risk.level} "
        f"({risk.score}/100). "
        f"Se identificaron {len(contradictions)} contradicciones potenciales. "
        "Este resultado es preliminar y debe contrastarse con el expediente original."
    )

