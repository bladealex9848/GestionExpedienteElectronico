from __future__ import annotations

from dataclasses import dataclass

from .case_extractor import classify_document
from .command_center import detect_contradictions
from .models import PageTrace
from .petition_comparator import compare_requests_with_answers, extract_requests


@dataclass
class SemaphoreItem:
    area: str
    color: str
    score: int
    reason: str
    action: str
    source: str


def _all_pages(documents: dict[str, list[PageTrace]]) -> list[PageTrace]:
    return [page for pages in documents.values() for page in pages]


def _document_types(documents: dict[str, list[PageTrace]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name, pages in documents.items():
        kind, _ = classify_document(pages)
        result.setdefault(kind, []).append(name)
    return result


def _color_from_score(score: int) -> str:
    if score >= 70:
        return "Rojo"
    if score >= 35:
        return "Amarillo"
    return "Verde"


def _structure_item(documents: dict[str, list[PageTrace]]) -> SemaphoreItem:
    types = _document_types(documents)

    has_origin = bool(
        types.get("Acción de tutela")
        or types.get("Derecho de petición")
    )
    has_answer = bool(
        types.get("Contestación")
        or types.get("Respuesta de cumplimiento")
    )
    has_decision = bool(
        types.get("Fallo de tutela")
        or types.get("Auto de requerimiento")
    )

    missing = []
    if not has_origin:
        missing.append("documento inicial")
    if not has_answer:
        missing.append("respuesta principal")
    if not has_decision:
        missing.append("decisión o auto relevante")

    score = min(100, len(missing) * 35)

    if missing:
        reason = "Faltan piezas estructurales: " + ", ".join(missing) + "."
        action = "Incorporar o localizar las piezas faltantes antes de concluir."
    else:
        reason = "La estructura mínima del expediente está razonablemente completa."
        action = "Mantener control de versiones y verificar que los anexos estén completos."

    source = " | ".join(
        f"{kind}: {', '.join(names)}"
        for kind, names in types.items()
    )[:1200]

    return SemaphoreItem(
        "Estructura del expediente",
        _color_from_score(score),
        score,
        reason,
        action,
        source,
    )


def _quality_item(quality_rows: list[dict]) -> SemaphoreItem:
    total = len(quality_rows)
    low = sum(row.get("Calidad") == "Baja" for row in quality_rows)
    medium = sum(row.get("Calidad") == "Media" for row in quality_rows)

    if total == 0:
        score = 80
        reason = "No fue posible evaluar la calidad de lectura."
        action = "Revisar si los documentos se cargaron correctamente."
        source = ""
    else:
        score = min(100, int((low / total) * 100) + int((medium / total) * 35))
        reason = (
            f"{low} página(s) con calidad baja y "
            f"{medium} con calidad media, de {total} revisadas."
        )
        action = (
            "Reemplazar o revisar manualmente las páginas de baja calidad."
            if low
            else "Conservar los originales y revisar las páginas de calidad media."
        )
        source = " | ".join(
            f"{row.get('Documento')}, p. {row.get('Página')}"
            for row in quality_rows
            if row.get("Calidad") in {"Baja", "Media"}
        )[:1200]

    return SemaphoreItem(
        "Calidad documental",
        _color_from_score(score),
        score,
        reason,
        action,
        source,
    )


def _response_item(documents: dict[str, list[PageTrace]]) -> SemaphoreItem:
    types = _document_types(documents)
    petition_names = types.get("Derecho de petición", [])

    if not petition_names:
        return SemaphoreItem(
            "Respuesta de fondo",
            "Verde",
            0,
            "No se identificó un derecho de petición para comparar.",
            "No aplica por ahora; revisar manualmente si existe una petición no clasificada.",
            "",
        )

    answer_pages = [
        page
        for name, pages in documents.items()
        if name not in petition_names
        for page in pages
    ]

    total_requests = 0
    unanswered = 0
    partial = 0
    sources = []

    for name in petition_names:
        requests = extract_requests(documents[name])
        total_requests += len(requests)
        comparison = compare_requests_with_answers(requests, answer_pages)

        for row in comparison:
            status = row["Evaluación automática"]
            if status == "Sin respuesta localizada":
                unanswered += 1
            elif status in {
                "Respuesta parcial o relacionada",
                "Coincidencia débil; revisar",
            }:
                partial += 1

            if row.get("Documento respuesta"):
                sources.append(
                    f"{row['Documento respuesta']}, p. {row['Página respuesta']}"
                )

    if total_requests == 0:
        score = 45
        reason = "No se detectaron solicitudes individualizadas con las reglas actuales."
        action = "Identificar manualmente cada pregunta o solicitud."
    else:
        score = min(
            100,
            int((unanswered / total_requests) * 100)
            + int((partial / total_requests) * 45),
        )
        reason = (
            f"De {total_requests} solicitud(es), {unanswered} no tienen respuesta "
            f"localizada y {partial} presentan respuesta parcial o débil."
        )
        action = (
            "Preparar requerimiento o actuación frente a los puntos no respondidos."
            if unanswered or partial
            else "Conservar la matriz y verificar que las respuestas sean congruentes y de fondo."
        )

    return SemaphoreItem(
        "Respuesta de fondo",
        _color_from_score(score),
        score,
        reason,
        action,
        " | ".join(dict.fromkeys(sources))[:1200],
    )


def _contradiction_item(documents: dict[str, list[PageTrace]]) -> SemaphoreItem:
    contradictions = detect_contradictions(documents)
    count = len(contradictions)
    score = min(100, count * 20)

    if count:
        reason = f"Se detectaron {count} contradicción(es) potencial(es)."
        action = "Comparar las versiones y exigir soporte documental de la afirmación relevante."
        source = " | ".join(
            f"{row.get('Fuente 1')} ↔ {row.get('Fuente 2')}"
            for row in contradictions[:10]
        )
    else:
        reason = "No se detectaron contradicciones relevantes con las reglas actuales."
        action = "Mantener revisión humana sobre fechas, entregas y autorizaciones."
        source = ""

    return SemaphoreItem(
        "Contradicciones",
        _color_from_score(score),
        score,
        reason,
        action,
        source,
    )


def _evidence_item(documents: dict[str, list[PageTrace]]) -> SemaphoreItem:
    text = " ".join(
        page.text.lower()
        for page in _all_pages(documents)
    )

    expected = {
        "acta de entrega": ("acta de entrega", "recibido a satisfaccion"),
        "constancia de envío": ("constancia de envio", "acuse de recibo", "guia"),
        "autorización": ("autorizacion", "servicio autorizado"),
        "concepto médico": ("concepto medico", "medico tratante"),
        "notificación": ("notificacion", "notificado"),
    }

    found = []
    missing = []

    for label, patterns in expected.items():
        if any(pattern in text for pattern in patterns):
            found.append(label)
        else:
            missing.append(label)

    score = int((len(missing) / len(expected)) * 75)

    reason = (
        f"Pruebas localizadas: {', '.join(found) if found else 'ninguna'}. "
        f"No localizadas: {', '.join(missing) if missing else 'ninguna'}."
    )

    action = (
        "Solicitar o incorporar los soportes faltantes que sean pertinentes al caso."
        if missing
        else "Verificar autenticidad, fecha, integridad y correspondencia de cada soporte."
    )

    return SemaphoreItem(
        "Pruebas y soportes",
        _color_from_score(score),
        score,
        reason,
        action,
        "",
    )


def _deadline_item() -> SemaphoreItem:
    return SemaphoreItem(
        "Términos y vencimientos",
        "Amarillo",
        45,
        (
            "El sistema no puede fijar con seguridad el vencimiento sin confirmar "
            "fecha inicial, tipo de término y si se cuenta en horas, días hábiles o calendario."
        ),
        (
            "Completar manualmente la fecha de notificación, el término aplicable "
            "y la regla de cómputo antes de confiar en un vencimiento."
        ),
        "",
    )


def build_semaphores(
    documents: dict[str, list[PageTrace]],
    quality_rows: list[dict],
) -> list[SemaphoreItem]:
    return [
        _structure_item(documents),
        _response_item(documents),
        _evidence_item(documents),
        _contradiction_item(documents),
        _quality_item(quality_rows),
        _deadline_item(),
    ]


def overall_semaphore(items: list[SemaphoreItem]) -> dict:
    if not items:
        return {
            "color": "Rojo",
            "score": 100,
            "label": "Expediente no evaluable",
        }

    weighted = round(sum(item.score for item in items) / len(items))

    if any(item.color == "Rojo" for item in items):
        weighted = max(weighted, 70)

    color = _color_from_score(weighted)

    label = {
        "Verde": "Expediente controlado",
        "Amarillo": "Expediente con alertas",
        "Rojo": "Expediente crítico",
    }[color]

    return {
        "color": color,
        "score": weighted,
        "label": label,
    }
