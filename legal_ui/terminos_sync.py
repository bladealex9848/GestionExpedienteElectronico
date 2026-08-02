from __future__ import annotations

import hashlib
from datetime import date, datetime, time

import pandas as pd

from legal_ui.despacho_store import find_case, new_id


def term_fingerprint(herramienta: str, actuacion: str, vencimiento: str, documento: str = "") -> str:
    raw = f"{herramienta}|{actuacion}|{vencimiento}|{documento}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _coerce_date(value) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.replace("Z", "")).date()
        except ValueError:
            try:
                return datetime.strptime(value[:10], "%Y-%m-%d").date()
            except ValueError:
                return None
    return None


def _coerce_time(value, default: str = "17:00") -> str:
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, pd.Timestamp):
        return value.strftime("%H:%M")
    return default


def sync_term_to_case(store: dict, case_id: str, payload: dict) -> dict:
    case = find_case(store, case_id)
    if not case:
        return {"status": "missing_case"}

    vence = _coerce_date(payload.get("vencimiento"))
    if not vence:
        return {"status": "invalid_date"}

    actuacion = str(payload.get("actuacion") or payload.get("titulo") or "Actuación procesal").strip()
    herramienta = str(payload.get("herramienta") or "Términos").strip()
    documento = str(payload.get("documento") or "").strip()
    fingerprint = payload.get("origen_id") or term_fingerprint(
        herramienta,
        actuacion,
        vence.isoformat(),
        documento,
    )

    for task in case.get("tareas", []):
        if task.get("origen_id") == fingerprint:
            return {"status": "duplicate", "task_id": task.get("id"), "origen_id": fingerprint}

    titulo = str(payload.get("titulo") or actuacion).strip()
    termino_label = str(payload.get("termino") or "").strip()
    if termino_label and termino_label not in titulo:
        titulo = f"{titulo} ({termino_label})"

    estado_term = str(payload.get("estado") or "").lower()
    task_state = "en_curso" if "vencid" in estado_term else "pendiente"

    notas_parts = [
        str(payload.get("notas") or "").strip(),
        str(payload.get("que_hacer") or "").strip(),
    ]
    soporte = str(payload.get("soporte") or "").strip()
    if soporte:
        notas_parts.append(f"Soporte: {soporte}")
    notas = "\n".join(part for part in notas_parts if part)

    task = {
        "id": new_id("t"),
        "titulo": titulo[:160],
        "estado": task_state,
        "vence": vence.isoformat(),
        "origen": herramienta,
        "origen_id": fingerprint,
        "notas": notas,
    }
    case.setdefault("tareas", []).append(task)

    hora = _coerce_time(payload.get("vencimiento"), payload.get("hora", "17:00"))
    event = {
        "id": new_id("e"),
        "titulo": f"⏳ Vence: {titulo[:100]}",
        "fecha": vence.isoformat(),
        "hora": hora,
        "origen": herramienta,
        "origen_id": fingerprint,
    }
    case.setdefault("eventos", []).append(event)

    return {
        "status": "created",
        "task_id": task["id"],
        "event_id": event["id"],
        "origen_id": fingerprint,
    }


def row_from_control_terminos(row: dict) -> dict:
    return {
        "titulo": row.get("Actuación") or "Actuación procesal",
        "actuacion": row.get("Actuación", ""),
        "termino": row.get("Término", ""),
        "vencimiento": row.get("Vencimiento"),
        "estado": row.get("Estado", ""),
        "herramienta": "Control de Términos",
        "documento": row.get("Documento fuente") or row.get("Expediente") or "",
        "notas": row.get("Revisión humana", ""),
        "que_hacer": row.get("Qué hacer", ""),
        "soporte": row.get("Soporte", ""),
    }


def row_from_analizador_colombia(row: dict) -> dict:
    return {
        "titulo": row.get("Clase de término") or row.get("Actuación exigida") or "Término detectado",
        "actuacion": row.get("Actuación exigida", ""),
        "termino": str(row.get("Clase de término") or row.get("Cantidad") or "").strip(),
        "vencimiento": row.get("Vencimiento automático") or row.get("Vencimiento confirmado"),
        "estado": row.get("Estado", ""),
        "herramienta": "Analizador Términos Colombia",
        "documento": row.get("Documento", ""),
        "notas": row.get("Actuación que puede continuar") or row.get("Conclusión revisada", ""),
        "que_hacer": row.get("Actuación que puede continuar", ""),
        "soporte": f"{row.get('Documento', '')}, pág. {row.get('Página', '')}".strip(", pág. "),
    }


def sync_terms_batch(
    store: dict,
    case_id: str,
    rows: list[dict],
    source: str,
) -> dict:
    mapper = {
        "control": row_from_control_terminos,
        "colombia": row_from_analizador_colombia,
    }.get(source, row_from_control_terminos)

    created = 0
    duplicates = 0
    skipped = 0
    for row in rows:
        payload = mapper(row if isinstance(row, dict) else row.to_dict())
        result = sync_term_to_case(store, case_id, payload)
        if result["status"] == "created":
            created += 1
        elif result["status"] == "duplicate":
            duplicates += 1
        else:
            skipped += 1
    return {"created": created, "duplicates": duplicates, "skipped": skipped}
