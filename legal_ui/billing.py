from __future__ import annotations

import io
from datetime import date, timedelta

import pandas as pd

from legal_ui.despacho_store import client_name, parse_date

BILLING_STATES = ("pendiente", "facturado", "cobrado")

BILLING_LABELS = {
    "pendiente": "Pendiente de facturar",
    "facturado": "Facturado",
    "cobrado": "Cobrado",
}


def normalize_time_entry(entry: dict) -> None:
    estado = entry.get("estado_facturacion")
    if estado not in BILLING_STATES:
        estado = "facturado" if entry.get("facturado") else "pendiente"
        entry["estado_facturacion"] = estado
    entry["facturado"] = entry["estado_facturacion"] in ("facturado", "cobrado")


def normalize_store_billing(store: dict) -> None:
    config = store.setdefault("config", {})
    config.setdefault("tarifa_default_hora", 150_000)
    config.setdefault("moneda", "COP")
    for client in store.get("clientes", []):
        client.setdefault("tarifa_hora", 0)
    for case in store.get("casos", []):
        case.setdefault("tarifa_hora", 0)
        for entry in case.get("tiempo", []):
            normalize_time_entry(entry)


def hourly_rate(store: dict, case: dict) -> float:
    if case.get("tarifa_hora"):
        return float(case["tarifa_hora"])
    client = next(
        (row for row in store.get("clientes", []) if row.get("id") == case.get("cliente_id")),
        None,
    )
    if client and client.get("tarifa_hora"):
        return float(client["tarifa_hora"])
    return float(store.get("config", {}).get("tarifa_default_hora", 0))


def entry_value(minutos: int, tarifa_hora: float) -> float:
    if tarifa_hora <= 0:
        return 0.0
    return round((minutos / 60) * tarifa_hora, 2)


def all_time_entries(store: dict) -> list[dict]:
    rows: list[dict] = []
    for case in store.get("casos", []):
        rate = hourly_rate(store, case)
        for entry in case.get("tiempo", []):
            normalize_time_entry(entry)
            minutos = int(entry.get("minutos", 0))
            rows.append(
                {
                    **entry,
                    "caso_id": case["id"],
                    "caso": case.get("nombre", ""),
                    "cliente": client_name(store, case.get("cliente_id", "")),
                    "radicado": case.get("radicado", ""),
                    "tarifa_hora": rate,
                    "valor": entry_value(minutos, rate),
                    "estado_facturacion": entry.get("estado_facturacion", "pendiente"),
                }
            )
    rows.sort(key=lambda row: row.get("fecha", ""), reverse=True)
    return rows


def billing_totals(store: dict) -> dict[str, float | int]:
    totals = {"pendiente": 0.0, "facturado": 0.0, "cobrado": 0.0, "minutos_pendientes": 0}
    for row in all_time_entries(store):
        estado = row.get("estado_facturacion", "pendiente")
        valor = float(row.get("valor", 0))
        if estado == "pendiente":
            totals["pendiente"] += valor
            totals["minutos_pendientes"] += int(row.get("minutos", 0))
        elif estado == "facturado":
            totals["facturado"] += valor
        elif estado == "cobrado":
            totals["cobrado"] += valor
    return totals


def billing_by_client(store: dict) -> pd.DataFrame:
    buckets: dict[str, dict[str, float]] = {}
    for row in all_time_entries(store):
        client = row.get("cliente", "Sin cliente")
        bucket = buckets.setdefault(
            client,
            {"Pendiente": 0.0, "Facturado": 0.0, "Cobrado": 0.0, "Minutos pendientes": 0},
        )
        estado = row.get("estado_facturacion", "pendiente")
        valor = float(row.get("valor", 0))
        minutos = int(row.get("minutos", 0))
        if estado == "pendiente":
            bucket["Pendiente"] += valor
            bucket["Minutos pendientes"] += minutos
        elif estado == "facturado":
            bucket["Facturado"] += valor
        else:
            bucket["Cobrado"] += valor
    if not buckets:
        return pd.DataFrame()
    df = pd.DataFrame.from_dict(buckets, orient="index").reset_index()
    df.rename(columns={"index": "Cliente"}, inplace=True)
    df["Total"] = df["Pendiente"] + df["Facturado"] + df["Cobrado"]
    return df.sort_values("Pendiente", ascending=False)


def executive_dashboard(store: dict, today: date | None = None) -> dict:
    today = today or date.today()
    week_end = today + timedelta(days=7)
    casos = store.get("casos", [])

    casos_por_estado: dict[str, int] = {estado: 0 for estado in ("activo", "pausado", "cerrado", "archivado")}
    casos_riesgo: list[dict] = []
    plazos_criticos: list[dict] = []

    for case in casos:
        estado = case.get("estado", "activo")
        casos_por_estado[estado] = casos_por_estado.get(estado, 0) + 1
        vencidas = 0
        proximas = 0
        for task in case.get("tareas", []):
            if task.get("estado") == "completada":
                continue
            due = parse_date(task.get("vence", ""))
            if not due:
                continue
            if due < today:
                vencidas += 1
                plazos_criticos.append(
                    {
                        "Tipo": "Tarea vencida",
                        "Fecha": due.isoformat(),
                        "Detalle": task.get("titulo", ""),
                        "Caso": case.get("nombre", ""),
                        "Cliente": client_name(store, case.get("cliente_id", "")),
                    }
                )
            elif due <= week_end:
                proximas += 1
                plazos_criticos.append(
                    {
                        "Tipo": "Vence esta semana",
                        "Fecha": due.isoformat(),
                        "Detalle": task.get("titulo", ""),
                        "Caso": case.get("nombre", ""),
                        "Cliente": client_name(store, case.get("cliente_id", "")),
                    }
                )
        for event in case.get("eventos", []):
            event_date = parse_date(event.get("fecha", ""))
            if event_date and today <= event_date <= week_end:
                plazos_criticos.append(
                    {
                        "Tipo": "Evento",
                        "Fecha": event_date.isoformat(),
                        "Detalle": event.get("titulo", ""),
                        "Caso": case.get("nombre", ""),
                        "Cliente": client_name(store, case.get("cliente_id", "")),
                    }
                )
        score = vencidas * 3 + proximas
        if score > 0 and estado == "activo":
            casos_riesgo.append(
                {
                    "Caso": case.get("nombre", ""),
                    "Cliente": client_name(store, case.get("cliente_id", "")),
                    "Vencidas": vencidas,
                    "Próximas 7d": proximas,
                    "Score": score,
                }
            )

    casos_riesgo.sort(key=lambda row: row["Score"], reverse=True)
    plazos_criticos.sort(key=lambda row: row["Fecha"])

    billing = billing_totals(store)
    return {
        "casos_por_estado": casos_por_estado,
        "casos_riesgo": casos_riesgo[:8],
        "plazos_criticos": plazos_criticos[:12],
        "billing": billing,
        "total_casos": len(casos),
        "clientes": len(store.get("clientes", [])),
    }


def export_billing_excel(store: dict) -> bytes:
    rows = all_time_entries(store)
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "fecha",
                "descripcion",
                "minutos",
                "valor",
                "estado_facturacion",
                "caso",
                "cliente",
                "radicado",
            ]
        )
    else:
        df = df[
            [
                "fecha",
                "descripcion",
                "minutos",
                "tarifa_hora",
                "valor",
                "estado_facturacion",
                "caso",
                "cliente",
                "radicado",
            ]
        ]
    summary = billing_by_client(store)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Detalle horas", index=False)
        summary.to_excel(writer, sheet_name="Resumen por cliente", index=False)
    return buffer.getvalue()
