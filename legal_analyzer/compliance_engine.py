from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ComplianceAssessment,
    EvidenceRecord,
    OrderRecord,
    PageTrace,
)
from .ocr_engine import quality_score
from .text_utils import meaningful_words, normalize, split_fragments, text_similarity


COMPLIANCE_EXPRESSIONS = (
    "se dio cumplimiento",
    "dimos cumplimiento",
    "cumplimiento del fallo",
    "se cumplio",
    "fue entregado",
    "se realizo",
    "se autorizo",
    "se programo",
    "se remitio",
    "se respondio",
    "se adjunta",
    "se aporta",
    "acta de entrega",
    "constancia de entrega",
    "recibido a satisfaccion",
)

NONCOMPLIANCE_EXPRESSIONS = (
    "no se ha cumplido",
    "incumplimiento",
    "no fue entregado",
    "no se realizo",
    "no se autorizo",
    "no ha sido posible",
    "pendiente",
    "sin respuesta",
    "no existe prueba",
    "cumplimiento parcial",
)

TIMELINESS_EXPRESSIONS = (
    "dentro del termino",
    "dentro del plazo",
    "oportunamente",
    "en tiempo",
    "antes del vencimiento",
)

LATE_EXPRESSIONS = (
    "fuera del termino",
    "extemporaneo",
    "vencido el plazo",
    "despues del vencimiento",
)

INTEGRITY_EXPRESSIONS = (
    "cumplimiento integral",
    "en su totalidad",
    "totalmente",
    "de manera completa",
)

PARTIAL_EXPRESSIONS = (
    "parcialmente",
    "cumplimiento parcial",
    "solo se",
    "unicamente",
    "queda pendiente",
)


@dataclass(frozen=True)
class ScoringWeights:
    conduct: float = 0.30
    responsible: float = 0.15
    evidence: float = 0.25
    timeliness: float = 0.10
    integrity: float = 0.10
    ocr_quality: float = 0.10


def phrase_signal(text: str, positives: tuple[str, ...], negatives: tuple[str, ...]) -> float:
    normalized = normalize(text)
    positive_hits = sum(phrase in normalized for phrase in positives)
    negative_hits = sum(phrase in normalized for phrase in negatives)

    if positive_hits and not negative_hits:
        return 1.0
    if negative_hits and not positive_hits:
        return 0.0
    if positive_hits and negative_hits:
        return 0.5
    return 0.35


def responsible_signal(order: OrderRecord, fragment: str) -> float:
    responsible = normalize(order.responsible)
    if not responsible or "requiere identificacion manual" in responsible:
        return 0.5

    responsible_words = meaningful_words(responsible)
    fragment_words = meaningful_words(fragment)

    if not responsible_words:
        return 0.5

    overlap = len(responsible_words.intersection(fragment_words))
    return min(1.0, overlap / max(len(responsible_words), 1))


def evidence_strength(fragment: str) -> float:
    normalized = normalize(fragment)

    documentary_signals = (
        "anexo", "adjunto", "acta", "constancia", "certificacion",
        "historia clinica", "factura", "recibo", "correo", "radicado",
        "captura", "comprobante", "concepto", "informe",
    )

    hits = sum(signal in normalized for signal in documentary_signals)
    compliance = phrase_signal(
        fragment,
        COMPLIANCE_EXPRESSIONS,
        NONCOMPLIANCE_EXPRESSIONS,
    )

    return min(1.0, (hits * 0.12) + (compliance * 0.64))


def timeliness_signal(fragment: str) -> float:
    return phrase_signal(fragment, TIMELINESS_EXPRESSIONS, LATE_EXPRESSIONS)


def integrity_signal(fragment: str) -> float:
    return phrase_signal(fragment, INTEGRITY_EXPRESSIONS, PARTIAL_EXPRESSIONS)


def candidate_evidences(
    order: OrderRecord,
    pages: list[PageTrace],
) -> list[EvidenceRecord]:
    candidates: list[EvidenceRecord] = []

    for page in pages:
        for fragment_index, fragment in enumerate(split_fragments(page.text), start=1):
            similarity = text_similarity(order.text, fragment)

            if similarity < 0.045:
                continue

            candidates.append(
                EvidenceRecord(
                    document=page.document,
                    page=page.page,
                    fragment=fragment[:1200],
                    similarity=similarity,
                    compliance_signal=phrase_signal(
                        fragment,
                        COMPLIANCE_EXPRESSIONS,
                        NONCOMPLIANCE_EXPRESSIONS,
                    ),
                    timeliness_signal=timeliness_signal(fragment),
                    responsibility_signal=responsible_signal(order, fragment),
                    integrity_signal=integrity_signal(fragment),
                    ocr_quality=quality_score(page),
                    trace_id=f"{page.document}#p{page.page}#f{fragment_index}",
                )
            )

    candidates.sort(
        key=lambda item: (
            item.similarity * 0.35
            + item.compliance_signal * 0.20
            + item.responsibility_signal * 0.10
            + item.ocr_quality * 0.10
            + evidence_strength(item.fragment) * 0.25
        ),
        reverse=True,
    )

    return candidates[:10]


def status_from_scores(
    total: float,
    evidence: float,
    integrity: float,
    timeliness: float,
    responsible: float,
) -> str:
    if evidence < 0.28:
        return "No verificable"
    if total >= 0.78 and integrity >= 0.65 and responsible >= 0.55:
        return "Posible cumplimiento integral"
    if total >= 0.60:
        if integrity < 0.55 or timeliness < 0.45 or responsible < 0.45:
            return "Posible cumplimiento parcial"
        return "Posible cumplimiento"
    if total >= 0.42:
        return "Requiere revisión"
    return "Posible incumplimiento"


def assess_order(
    order: OrderRecord,
    evidence_pages: list[PageTrace],
    weights: ScoringWeights | None = None,
) -> ComplianceAssessment:
    weights = weights or ScoringWeights()
    candidates = candidate_evidences(order, evidence_pages)
    best = candidates[0] if candidates else None

    if best is None:
        return ComplianceAssessment(
            order_id=order.order_id,
            conduct_score=0.0,
            responsible_score=0.0,
            evidence_score=0.0,
            timeliness_score=0.0,
            integrity_score=0.0,
            ocr_quality_score=0.0,
            total_score=0.0,
            automatic_status="No verificable",
            reasoning=(
                "No se localizó un fragmento documental suficientemente "
                "relacionado con la orden."
            ),
            best_evidence=None,
        )

    conduct = min(1.0, best.similarity / 0.22)
    responsible = best.responsibility_signal
    evidence = evidence_strength(best.fragment)
    timely = best.timeliness_signal
    integrity = best.integrity_signal
    quality = best.ocr_quality

    total = round(
        conduct * weights.conduct
        + responsible * weights.responsible
        + evidence * weights.evidence
        + timely * weights.timeliness
        + integrity * weights.integrity
        + quality * weights.ocr_quality,
        4,
    )

    status = status_from_scores(
        total,
        evidence,
        integrity,
        timely,
        responsible,
    )

    reasoning = " | ".join(
        [
            f"Coincidencia de conducta: {conduct * 100:.0f}%",
            f"Responsable: {responsible * 100:.0f}%",
            f"Fuerza de la prueba: {evidence * 100:.0f}%",
            f"Oportunidad: {timely * 100:.0f}%",
            f"Integralidad: {integrity * 100:.0f}%",
            f"Calidad OCR/texto: {quality * 100:.0f}%",
        ]
    )

    return ComplianceAssessment(
        order_id=order.order_id,
        conduct_score=conduct,
        responsible_score=responsible,
        evidence_score=evidence,
        timeliness_score=timely,
        integrity_score=integrity,
        ocr_quality_score=quality,
        total_score=total,
        automatic_status=status,
        reasoning=reasoning,
        best_evidence=best,
    )
