from __future__ import annotations

import io
import json
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STORE_PATH = DATA_DIR / "despacho.json"

TASK_STATES = ("pendiente", "en_curso", "completada")
CASE_STATES = ("activo", "pausado", "cerrado", "archivado")

__all__ = [
    "CASE_STATES",
    "TASK_STATES",
    "all_open_tasks",
    "case_metrics",
    "cases_for_client",
    "client_map",
    "client_name",
    "complete_task",
    "default_store",
    "delete_case",
    "delete_client",
    "delete_event",
    "delete_task",
    "events_in_range",
    "export_excel",
    "export_json",
    "find_case",
    "find_client",
    "global_metrics",
    "import_excel",
    "import_json",
    "load_store",
    "new_id",
    "open_tasks",
    "overdue_tasks",
    "parse_date",
    "reset_store",
    "save_store",
    "search_store",
    "set_time_billing_state",
    "toggle_time_billed",
]


def _today() -> date:
    return date.today()


def _normalize_case(case: dict) -> None:
    case.setdefault("despacho", "")
    case.setdefault("tipo_proceso", "")
    case.setdefault("partes", "")
    case.setdefault("documentos", [])
    case.setdefault("resultados", [])
    case.setdefault("tarifa_hora", 0)


def _normalize_store(store: dict) -> None:
    from legal_ui.billing import normalize_store_billing

    normalize_store_billing(store)
    for case in store.get("casos", []):
        _normalize_case(case)


def default_store() -> dict:
    today = _today()
    clientes = [
        {
            "id": "cl1",
            "nombre": "María López",
            "documento": "52.123.456",
            "email": "maria.lopez@correo.com",
            "telefono": "3001234567",
            "tarifa_hora": 0,
        },
        {
            "id": "cl2",
            "nombre": "Carlos Ruiz",
            "documento": "80.987.654",
            "email": "carlos.ruiz@correo.com",
            "telefono": "3109876543",
        },
        {
            "id": "cl3",
            "nombre": "Empresa ABC S.A.S.",
            "documento": "900.111.222-3",
            "email": "juridico@abc.com",
            "telefono": "6015550101",
        },
        {
            "id": "cl4",
            "nombre": "Ana Torres",
            "documento": "41.555.888",
            "email": "ana.torres@correo.com",
            "telefono": "3201112233",
        },
    ]
    casos = [
        {
            "id": "c1",
            "nombre": "Vigilancia judicial — Juzgado 1 Civil",
            "cliente_id": "cl1",
            "radicado": "2024-00123",
            "despacho": "Juzgado Primero Civil Municipal",
            "tipo_proceso": "Vigilancia Judicial Administrativa",
            "partes": "María López — solicitante",
            "estado": "activo",
            "notas": "Falta memorial de impulso y constancia de radicación.",
            "documentos": [],
            "resultados": [],
            "tareas": [
                {
                    "id": "t1",
                    "titulo": "Revisar memorial de impulso",
                    "estado": "pendiente",
                    "vence": (today + timedelta(days=1)).isoformat(),
                },
                {
                    "id": "t2",
                    "titulo": "Actualizar cronología documental",
                    "estado": "en_curso",
                    "vence": (today + timedelta(days=3)).isoformat(),
                },
                {
                    "id": "t3",
                    "titulo": "Validar anexos PDF",
                    "estado": "pendiente",
                    "vence": (today - timedelta(days=1)).isoformat(),
                },
            ],
            "eventos": [
                {
                    "id": "e1",
                    "titulo": "Audiencia de seguimiento",
                    "fecha": (today + timedelta(days=2)).isoformat(),
                    "hora": "09:00",
                },
                {
                    "id": "e2",
                    "titulo": "Revisión interna del expediente",
                    "fecha": (today + timedelta(days=6)).isoformat(),
                    "hora": "15:30",
                },
            ],
            "tiempo": [
                {
                    "id": "tm1",
                    "fecha": today.isoformat(),
                    "minutos": 90,
                    "descripcion": "Análisis de providencias",
                    "facturado": False,
                },
                {
                    "id": "tm2",
                    "fecha": (today - timedelta(days=1)).isoformat(),
                    "minutos": 30,
                    "descripcion": "Organización de anexos",
                    "facturado": False,
                },
            ],
        },
        {
            "id": "c2",
            "nombre": "Tutela derecho de petición — EPS",
            "cliente_id": "cl2",
            "radicado": "2025-00456",
            "despacho": "Juzgado de Ejecución de Penas y Medidas de Seguridad",
            "tipo_proceso": "Tutela",
            "partes": "Carlos Ruiz vs. EPS accionada",
            "estado": "activo",
            "notas": "Esperando respuesta de la accionada.",
            "documentos": [],
            "resultados": [],
            "tareas": [
                {
                    "id": "t4",
                    "titulo": "Verificar respuesta EPS",
                    "estado": "pendiente",
                    "vence": (today + timedelta(days=4)).isoformat(),
                },
            ],
            "eventos": [
                {
                    "id": "e3",
                    "titulo": "Vencimiento término tutela",
                    "fecha": (today + timedelta(days=5)).isoformat(),
                    "hora": "17:00",
                },
            ],
            "tiempo": [
                {
                    "id": "tm3",
                    "fecha": today.isoformat(),
                    "minutos": 45,
                    "descripcion": "Redacción de memorial",
                    "facturado": False,
                },
            ],
        },
        {
            "id": "c3",
            "nombre": "Conciliación extrajudicial laboral",
            "cliente_id": "cl3",
            "radicado": "2023-00987",
            "despacho": "Centro de Conciliación",
            "tipo_proceso": "Conciliación extrajudicial",
            "partes": "Empresa ABC S.A.S.",
            "estado": "pausado",
            "notas": "Pausado a solicitud del cliente.",
            "documentos": [],
            "resultados": [],
            "tareas": [],
            "eventos": [],
            "tiempo": [],
        },
        {
            "id": "c4",
            "nombre": "Incidente de desacato tutela",
            "cliente_id": "cl4",
            "radicado": "2022-00321",
            "despacho": "Juzgado de Familia",
            "tipo_proceso": "Incidente de desacato",
            "partes": "Ana Torres",
            "estado": "cerrado",
            "notas": "Fallo favorable. Archivo listo.",
            "documentos": [],
            "resultados": [],
            "tareas": [],
            "eventos": [],
            "tiempo": [],
        },
    ]
    store = {
        "config": {"tarifa_default_hora": 150_000, "moneda": "COP"},
        "clientes": clientes,
        "casos": casos,
    }
    _normalize_store(store)
    return store


def load_store() -> dict:
    from legal_ui.auth import get_current_user_id, use_database_storage

    user_id = get_current_user_id()
    if use_database_storage() and user_id:
        from legal_ui.database import load_store_json

        raw = load_store_json(user_id)
        if raw:
            store = json.loads(raw)
            _normalize_store(store)
            return store

        if STORE_PATH.exists():
            with STORE_PATH.open(encoding="utf-8") as handle:
                store = json.load(handle)
            _normalize_store(store)
            save_store(store)
            return store

        store = default_store()
        save_store(store)
        return store

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        store = default_store()
        save_store(store)
        return store
    with STORE_PATH.open(encoding="utf-8") as handle:
        store = json.load(handle)
    _normalize_store(store)
    return store


def save_store(store: dict) -> None:
    from legal_ui.auth import get_current_user_id, use_database_storage

    user_id = get_current_user_id()
    if use_database_storage() and user_id:
        from legal_ui.database import save_store_json

        for case in store.get("casos", []):
            _normalize_case(case)
        save_store_json(user_id, json.dumps(store, ensure_ascii=False))
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with STORE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=False, indent=2)


def client_map(store: dict) -> dict[str, dict]:
    return {cliente["id"]: cliente for cliente in store.get("clientes", [])}


def client_name(store: dict, client_id: str) -> str:
    return client_map(store).get(client_id, {}).get("nombre", "Sin cliente")


def new_id(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:8]}"


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def open_tasks(case: dict) -> list[dict]:
    return [task for task in case.get("tareas", []) if task.get("estado") != "completada"]


def overdue_tasks(case: dict, today: date | None = None) -> list[dict]:
    today = today or _today()
    overdue = []
    for task in open_tasks(case):
        due = parse_date(task.get("vence", ""))
        if due and due < today:
            overdue.append(task)
    return overdue


def events_in_range(store: dict, start: date, end: date) -> list[dict]:
    rows = []
    for case in store.get("casos", []):
        for event in case.get("eventos", []):
            event_date = parse_date(event.get("fecha", ""))
            if event_date and start <= event_date <= end:
                rows.append(
                    {
                        **event,
                        "caso_id": case["id"],
                        "caso": case["nombre"],
                        "cliente": client_name(store, case.get("cliente_id", "")),
                    }
                )
    rows.sort(key=lambda row: (row.get("fecha", ""), row.get("hora", "")))
    return rows


def case_metrics(case: dict, today: date | None = None) -> dict[str, int]:
    today = today or _today()
    open_list = open_tasks(case)
    week_end = today + timedelta(days=7)
    events_week = 0
    for event in case.get("eventos", []):
        event_date = parse_date(event.get("fecha", ""))
        if event_date and today <= event_date <= week_end:
            events_week += 1
    unbilled = sum(
        entry.get("minutos", 0)
        for entry in case.get("tiempo", [])
        if entry.get("estado_facturacion", "pendiente" if not entry.get("facturado") else "facturado")
        == "pendiente"
    )
    return {
        "tareas_abiertas": len(open_list),
        "vencidas": len(overdue_tasks(case, today)),
        "eventos_7d": events_week,
        "minutos_sin_facturar": unbilled,
    }


def global_metrics(store: dict, today: date | None = None) -> dict[str, int | float]:
    today = today or _today()
    casos = store.get("casos", [])
    activos = [case for case in casos if case.get("estado") == "activo"]
    from legal_ui.billing import billing_totals

    billing = billing_totals(store)
    return {
        "activos": len(activos),
        "clientes": len(store.get("clientes", [])),
        "tareas": sum(case_metrics(case, today)["tareas_abiertas"] for case in casos),
        "vencidas": sum(case_metrics(case, today)["vencidas"] for case in casos),
        "eventos": len(events_in_range(store, today, today + timedelta(days=7))),
        "sin_facturar": sum(case_metrics(case, today)["minutos_sin_facturar"] for case in casos),
        "valor_pendiente": billing["pendiente"],
    }


def all_open_tasks(store: dict) -> list[dict]:
    rows = []
    for case in store.get("casos", []):
        for task in open_tasks(case):
            rows.append(
                {
                    **task,
                    "caso_id": case["id"],
                    "caso": case["nombre"],
                    "cliente": client_name(store, case.get("cliente_id", "")),
                    "radicado": case.get("radicado", ""),
                }
            )
    rows.sort(key=lambda row: row.get("vence", "9999"))
    return rows


def find_case(store: dict, case_id: str) -> dict | None:
    for case in store.get("casos", []):
        if case["id"] == case_id:
            return case
    return None


def find_client(store: dict, client_id: str) -> dict | None:
    for client in store.get("clientes", []):
        if client["id"] == client_id:
            return client
    return None


def cases_for_client(store: dict, client_id: str) -> list[dict]:
    return [case for case in store.get("casos", []) if case.get("cliente_id") == client_id]


def delete_case(store: dict, case_id: str) -> None:
    store["casos"] = [case for case in store.get("casos", []) if case["id"] != case_id]


def delete_client(store: dict, client_id: str) -> None:
    store["clientes"] = [client for client in store.get("clientes", []) if client["id"] != client_id]
    for case in store.get("casos", []):
        if case.get("cliente_id") == client_id:
            case["cliente_id"] = ""


def complete_task(store: dict, case_id: str, task_id: str) -> None:
    case = find_case(store, case_id)
    if not case:
        return
    for task in case.get("tareas", []):
        if task.get("id") == task_id:
            task["estado"] = "completada"
            return


def delete_task(store: dict, case_id: str, task_id: str) -> None:
    case = find_case(store, case_id)
    if not case:
        return
    case["tareas"] = [task for task in case.get("tareas", []) if task.get("id") != task_id]


def delete_event(store: dict, case_id: str, event_id: str) -> None:
    case = find_case(store, case_id)
    if not case:
        return
    case["eventos"] = [event for event in case.get("eventos", []) if event.get("id") != event_id]


def set_time_billing_state(store: dict, case_id: str, entry_id: str, estado: str) -> None:
    from legal_ui.billing import BILLING_STATES, normalize_time_entry

    if estado not in BILLING_STATES:
        return
    case = find_case(store, case_id)
    if not case:
        return
    for entry in case.get("tiempo", []):
        if entry.get("id") == entry_id:
            entry["estado_facturacion"] = estado
            normalize_time_entry(entry)
            return


def toggle_time_billed(store: dict, case_id: str, entry_id: str, billed: bool) -> None:
    set_time_billing_state(store, case_id, entry_id, "facturado" if billed else "pendiente")


def search_store(store: dict, query: str) -> dict[str, list[dict]]:
    query = query.lower().strip()
    if not query:
        return {"casos": [], "clientes": [], "tareas": []}

    casos = [
        case
        for case in store.get("casos", [])
        if query in case.get("nombre", "").lower()
        or query in case.get("radicado", "").lower()
        or query in client_name(store, case.get("cliente_id", "")).lower()
    ]
    clientes = [
        client
        for client in store.get("clientes", [])
        if query in client.get("nombre", "").lower()
        or query in client.get("documento", "").lower()
        or query in client.get("email", "").lower()
    ]
    tareas = [
        task
        for task in all_open_tasks(store)
        if query in task.get("titulo", "").lower()
        or query in task.get("caso", "").lower()
        or query in task.get("cliente", "").lower()
    ]
    return {"casos": casos, "clientes": clientes, "tareas": tareas}


def export_excel(store: dict) -> bytes:
    clientes_df = pd.DataFrame(store.get("clientes", []))
    casos_rows = []
    tareas_rows = []
    eventos_rows = []
    tiempo_rows = []
    for case in store.get("casos", []):
        metrics = case_metrics(case)
        casos_rows.append(
            {
                "id": case["id"],
                "nombre": case["nombre"],
                "cliente_id": case.get("cliente_id", ""),
                "cliente": client_name(store, case.get("cliente_id", "")),
                "radicado": case.get("radicado", ""),
                "estado": case.get("estado", ""),
                "notas": case.get("notas", ""),
                "tareas_abiertas": metrics["tareas_abiertas"],
                "vencidas": metrics["vencidas"],
                "eventos_7d": metrics["eventos_7d"],
                "minutos_sin_facturar": metrics["minutos_sin_facturar"],
            }
        )
        for task in case.get("tareas", []):
            tareas_rows.append({**task, "caso_id": case["id"], "caso": case["nombre"]})
        for event in case.get("eventos", []):
            eventos_rows.append({**event, "caso_id": case["id"], "caso": case["nombre"]})
        for entry in case.get("tiempo", []):
            tiempo_rows.append({**entry, "caso_id": case["id"], "caso": case["nombre"]})

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(casos_rows).to_excel(writer, sheet_name="Casos", index=False)
        pd.DataFrame(clientes_df).to_excel(writer, sheet_name="Clientes", index=False)
        pd.DataFrame(tareas_rows).to_excel(writer, sheet_name="Tareas", index=False)
        pd.DataFrame(eventos_rows).to_excel(writer, sheet_name="Eventos", index=False)
        pd.DataFrame(tiempo_rows).to_excel(writer, sheet_name="Tiempo", index=False)
    return buffer.getvalue()


def import_excel(content: bytes) -> dict:
    book = pd.ExcelFile(io.BytesIO(content))
    store = {"clientes": [], "casos": []}

    if "Clientes" in book.sheet_names:
        store["clientes"] = book.parse("Clientes").fillna("").to_dict(orient="records")
        for client in store["clientes"]:
            client["id"] = str(client.get("id") or new_id("cl"))

    cases_df = book.parse("Casos").fillna("") if "Casos" in book.sheet_names else pd.DataFrame()
    tasks_df = book.parse("Tareas").fillna("") if "Tareas" in book.sheet_names else pd.DataFrame()
    events_df = book.parse("Eventos").fillna("") if "Eventos" in book.sheet_names else pd.DataFrame()
    time_df = book.parse("Tiempo").fillna("") if "Tiempo" in book.sheet_names else pd.DataFrame()

    for _, row in cases_df.iterrows():
        case_id = str(row.get("id") or new_id("c"))
        case = {
            "id": case_id,
            "nombre": str(row.get("nombre", "")),
            "cliente_id": str(row.get("cliente_id", "")),
            "radicado": str(row.get("radicado", "")),
            "estado": str(row.get("estado", "activo")) or "activo",
            "notas": str(row.get("notas", "")),
            "tareas": [],
            "eventos": [],
            "tiempo": [],
        }
        if not case["cliente_id"] and row.get("cliente"):
            match = next(
                (client["id"] for client in store["clientes"] if client.get("nombre") == row.get("cliente")),
                "",
            )
            case["cliente_id"] = match
        store["casos"].append(case)

    case_ids = {case["id"] for case in store["casos"]}

    def _attach(rows: pd.DataFrame, field: str) -> None:
        for _, row in rows.iterrows():
            case_id = str(row.get("caso_id", ""))
            if case_id not in case_ids:
                continue
            payload = row.drop(labels=["caso_id", "caso"], errors="ignore").to_dict()
            payload["id"] = str(payload.get("id") or new_id(field[0]))
            for case in store["casos"]:
                if case["id"] == case_id:
                    case[field].append(payload)
                    break

    _attach(tasks_df, "tareas")
    _attach(events_df, "eventos")
    _attach(time_df, "tiempo")
    _normalize_store(store)
    return store


def export_json(store: dict) -> bytes:
    return json.dumps(store, ensure_ascii=False, indent=2).encode("utf-8")


def import_json(content: bytes) -> dict:
    loaded = json.loads(content.decode("utf-8"))
    if not isinstance(loaded, dict) or "casos" not in loaded:
        raise ValueError("El JSON no tiene el formato esperado.")
    loaded.setdefault("clientes", [])
    _normalize_store(loaded)
    return loaded


def reset_store() -> dict:
    store = default_store()
    save_store(store)
    return deepcopy(store)
