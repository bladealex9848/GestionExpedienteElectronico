from __future__ import annotations

import importlib
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from legal_ui import despacho_store

importlib.reload(despacho_store)

from legal_ui.billing import BILLING_LABELS, BILLING_STATES, entry_value, hourly_rate, normalize_time_entry
from legal_ui.despacho_store import (
    CASE_STATES,
    TASK_STATES,
    all_open_tasks,
    case_metrics,
    cases_for_client,
    client_name,
    complete_task,
    delete_case,
    delete_client,
    delete_event,
    delete_task,
    events_in_range,
    export_excel,
    export_json,
    find_case,
    find_client,
    global_metrics,
    import_excel,
    import_json,
    new_id,
    parse_date,
    reset_store,
    save_store,
    search_store,
    set_time_billing_state,
)
from legal_ui.expediente_views import render_expediente_tab
from legal_ui.lexivox_theme import FILTER_OPTIONS, STATUS_LABELS, TASK_LABELS


def persist() -> None:
    save_store(st.session_state.despacho_store)

def filtrar_casos(casos: list[dict], query: str) -> list[dict]:
    filtro = st.session_state.filtro_casos
    rows = casos
    if filtro != "todos":
        rows = [case for case in rows if case.get("estado") == filtro]
    if query:
        rows = [
            case
            for case in rows
            if query in case.get("nombre", "").lower()
            or query in case.get("radicado", "").lower()
            or query in client_name(st.session_state.despacho_store, case.get("cliente_id", "")).lower()
        ]
    return rows


def render_metricas() -> None:
    store = st.session_state.despacho_store
    metricas = global_metrics(store)
    valor = metricas.get("valor_pendiente", 0)
    st.markdown(
        f"""
        <div class="lx-metric-grid">
            <div class="lx-metric">
                <div class="lx-metric-label">Casos activos</div>
                <div class="lx-metric-value ok">{metricas['activos']}</div>
            </div>
            <div class="lx-metric">
                <div class="lx-metric-label">Clientes</div>
                <div class="lx-metric-value">{metricas['clientes']}</div>
            </div>
            <div class="lx-metric">
                <div class="lx-metric-label">Tareas abiertas</div>
                <div class="lx-metric-value">{metricas['tareas']}</div>
            </div>
            <div class="lx-metric">
                <div class="lx-metric-label">Vencidas</div>
                <div class="lx-metric-value warn">{metricas['vencidas']}</div>
            </div>
            <div class="lx-metric">
                <div class="lx-metric-label">Por facturar</div>
                <div class="lx-metric-value">${valor:,.0f}</div>
            </div>
            <div class="lx-metric">
                <div class="lx-metric-label">Eventos 7 días</div>
                <div class="lx-metric-value">{metricas['eventos']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_busqueda_global(query: str) -> None:
    if not query:
        return
    results = search_store(st.session_state.despacho_store, query)
    total = sum(len(results[key]) for key in results)
    if total == 0:
        return

    with st.expander(f"🔍 Resultados de búsqueda ({total})", expanded=True):
        if results["casos"]:
            st.markdown("**Casos**")
            for case in results["casos"]:
                if st.button(
                    f"{case['nombre']} — {client_name(st.session_state.despacho_store, case.get('cliente_id', ''))}",
                    key=f"search_case_{case['id']}",
                ):
                    st.session_state.lexivox_vista = "casos"
                    st.session_state.caso_seleccionado_id = case["id"]
                    st.rerun()
        if results["clientes"]:
            st.markdown("**Clientes**")
            for client in results["clientes"]:
                if st.button(client.get("nombre", ""), key=f"search_client_{client['id']}"):
                    st.session_state.lexivox_vista = "clientes"
                    st.session_state.cliente_seleccionado_id = client["id"]
                    st.rerun()
        if results["tareas"]:
            st.markdown("**Tareas**")
            for task in results["tareas"]:
                if st.button(
                    f"{task.get('titulo', '')} ({task.get('caso', '')})",
                    key=f"search_task_{task['id']}",
                ):
                    st.session_state.lexivox_vista = "casos"
                    st.session_state.caso_seleccionado_id = task["caso_id"]
                    st.rerun()


def render_vista_casos(query: str) -> None:
    store = st.session_state.despacho_store
    header_col, action_col = st.columns([4, 1])
    with header_col:
        st.markdown(
            """
            <div class="lx-header">
                <div class="lx-title">Casos</div>
                <div class="lx-subtitle">
                    Gestiona asuntos, tareas, plazos, notas y tiempo del despacho.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with action_col:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        if st.button("➕ Nuevo caso", type="primary", use_container_width=True):
            st.session_state.mostrar_formulario_caso = True

    if st.session_state.get("mostrar_formulario_caso"):
        clientes = store.get("clientes", [])
        with st.expander("Registrar nuevo caso", expanded=True):
            with st.form("nuevo_caso"):
                nombre = st.text_input("Nombre del asunto")
                cliente_id = (
                    st.selectbox(
                        "Cliente",
                        options=[client["id"] for client in clientes],
                        format_func=lambda cid: client_name(store, cid),
                    )
                    if clientes
                    else None
                )
                radicado = st.text_input("Radicación")
                despacho = st.text_input("Despacho judicial (opcional)")
                estado = st.selectbox("Estado", CASE_STATES, format_func=lambda k: STATUS_LABELS[k])
                notas = st.text_area("Notas iniciales")
                submitted = st.form_submit_button("Guardar caso")
                if submitted:
                    if nombre.strip() and cliente_id:
                        nuevo = {
                            "id": new_id("c"),
                            "nombre": nombre.strip(),
                            "cliente_id": cliente_id,
                            "radicado": radicado.strip() or "Sin radicado",
                            "despacho": despacho.strip(),
                            "tipo_proceso": "Vigilancia Judicial Administrativa",
                            "partes": client_name(store, cliente_id),
                            "estado": estado,
                            "notas": notas.strip(),
                            "documentos": [],
                            "resultados": [],
                            "tareas": [],
                            "eventos": [],
                            "tiempo": [],
                        }
                        store["casos"].insert(0, nuevo)
                        st.session_state.caso_seleccionado_id = nuevo["id"]
                        st.session_state.mostrar_formulario_caso = False
                        persist()
                        st.rerun()
                    else:
                        st.error("Nombre y cliente son obligatorios.")
            if st.button("Cancelar registro", key="cancel_new_case"):
                st.session_state.mostrar_formulario_caso = False
                st.rerun()

    filter_cols = st.columns(len(FILTER_OPTIONS))
    for col, (key, label) in zip(filter_cols, FILTER_OPTIONS):
        with col:
            active = st.session_state.filtro_casos == key
            if st.button(
                label,
                key=f"filtro_{key}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.filtro_casos = key
                st.rerun()

    casos_filtrados = filtrar_casos(store.get("casos", []), query)
    if casos_filtrados and not any(
        case["id"] == st.session_state.caso_seleccionado_id for case in casos_filtrados
    ):
        st.session_state.caso_seleccionado_id = casos_filtrados[0]["id"]

    lista_col, detalle_col = st.columns([1.1, 1.4])
    with lista_col:
        st.markdown('<div class="lx-panel"><div class="lx-panel-title">Listado de casos</div>', unsafe_allow_html=True)
        if not casos_filtrados:
            st.markdown('<div class="lx-empty">No hay casos con este filtro.</div>', unsafe_allow_html=True)
        else:
            opciones = {
                case["id"]: f"{case['nombre']} — {client_name(store, case.get('cliente_id', ''))}"
                for case in casos_filtrados
            }
            keys = list(opciones.keys())
            seleccion = st.radio(
                "Casos",
                options=keys,
                format_func=lambda cid: opciones[cid],
                index=keys.index(st.session_state.caso_seleccionado_id)
                if st.session_state.caso_seleccionado_id in opciones
                else 0,
                label_visibility="collapsed",
            )
            if seleccion != st.session_state.caso_seleccionado_id:
                st.session_state.caso_seleccionado_id = seleccion
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with detalle_col:
        case = find_case(store, st.session_state.caso_seleccionado_id)
        st.markdown('<div class="lx-panel"><div class="lx-panel-title">Detalle del caso</div>', unsafe_allow_html=True)
        if not case:
            st.markdown(
                '<div class="lx-empty">Selecciona un caso para ver tareas, notas, eventos y tiempo.</div>',
                unsafe_allow_html=True,
            )
        else:
            metrics = case_metrics(case)
            st.markdown(f"### {case['nombre']}")
            st.caption(f"{client_name(store, case.get('cliente_id', ''))} · Rad. {case.get('radicado', '')}")

            edit_col, delete_col = st.columns([3, 1])
            with edit_col:
                with st.expander("✏️ Editar datos del caso"):
                    with st.form(f"edit_case_{case['id']}"):
                        new_name = st.text_input("Nombre", value=case.get("nombre", ""))
                        clientes = store.get("clientes", [])
                        new_client = st.selectbox(
                            "Cliente",
                            options=[client["id"] for client in clientes],
                            index=next(
                                (i for i, c in enumerate(clientes) if c["id"] == case.get("cliente_id")),
                                0,
                            )
                            if clientes
                            else 0,
                            format_func=lambda cid: client_name(store, cid),
                        ) if clientes else case.get("cliente_id", "")
                        new_radicado = st.text_input("Radicado", value=case.get("radicado", ""))
                        new_despacho = st.text_input("Despacho", value=case.get("despacho", ""))
                        new_tipo = st.text_input("Tipo de proceso", value=case.get("tipo_proceso", ""))
                        new_partes = st.text_input("Partes", value=case.get("partes", ""))
                        if st.form_submit_button("Guardar cambios"):
                            case["nombre"] = new_name.strip()
                            case["cliente_id"] = new_client
                            case["radicado"] = new_radicado.strip()
                            case["despacho"] = new_despacho.strip()
                            case["tipo_proceso"] = new_tipo.strip()
                            case["partes"] = new_partes.strip()
                            persist()
                            st.success("Caso actualizado.")
                            st.rerun()
            with delete_col:
                st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Eliminar caso", key=f"del_case_{case['id']}"):
                    delete_case(store, case["id"])
                    remaining = store.get("casos", [])
                    st.session_state.caso_seleccionado_id = remaining[0]["id"] if remaining else ""
                    persist()
                    st.rerun()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Tareas abiertas", metrics["tareas_abiertas"])
            m2.metric("Vencidas", metrics["vencidas"])
            m3.metric("Eventos 7d", metrics["eventos_7d"])
            m4.metric("Documentos", len(case.get("documentos", [])))
            m5.metric("Sin facturar", f"{metrics['minutos_sin_facturar']} min")

            tab_expediente, tab_tareas, tab_notas, tab_eventos, tab_tiempo = st.tabs(
                ["Expediente", "Tareas", "Notas", "Eventos", "Tiempo"]
            )
            with tab_expediente:
                render_expediente_tab(case, store, persist)
            with tab_tareas:
                for task in case.get("tareas", []):
                    tcol1, tcol2, tcol3, tcol4, tcol5 = st.columns([3, 1.2, 1.2, 0.5, 0.5])
                    origen = task.get("origen", "")
                    titulo = task.get("titulo", "")
                    if origen:
                        titulo = f"{titulo} · {origen}"
                    tcol1.write(f"**{titulo}**")
                    if task.get("notas"):
                        tcol1.caption(str(task.get("notas", ""))[:120])
                    tcol2.write(TASK_LABELS.get(task.get("estado", ""), task.get("estado", "")))
                    tcol3.write(task.get("vence", ""))
                    if task.get("estado") != "completada" and tcol4.button(
                        "✓", key=f"done_{case['id']}_{task['id']}"
                    ):
                        complete_task(store, case["id"], task["id"])
                        persist()
                        st.rerun()
                    if tcol5.button("🗑", key=f"rm_task_{case['id']}_{task['id']}"):
                        delete_task(store, case["id"], task["id"])
                        persist()
                        st.rerun()

                with st.form(f"nueva_tarea_{case['id']}"):
                    titulo = st.text_input("Nueva tarea")
                    vence = st.date_input("Vence", value=date.today() + timedelta(days=3))
                    estado = st.selectbox("Estado", TASK_STATES, format_func=lambda k: TASK_LABELS[k])
                    if st.form_submit_button("Agregar tarea"):
                        if titulo.strip():
                            case["tareas"].append(
                                {
                                    "id": new_id("t"),
                                    "titulo": titulo.strip(),
                                    "estado": estado,
                                    "vence": vence.isoformat(),
                                }
                            )
                            persist()
                            st.rerun()

            with tab_notas:
                notas = st.text_area("Notas del caso", value=case.get("notas", ""), height=140)
                if st.button("Guardar notas", key=f"save_notes_{case['id']}"):
                    case["notas"] = notas
                    persist()
                    st.success("Notas guardadas.")

            with tab_eventos:
                for event in case.get("eventos", []):
                    ecol1, ecol2, ecol3 = st.columns([2, 2, 1])
                    ecol1.write(f"**{event.get('titulo', '')}**")
                    ecol2.write(f"{event.get('fecha', '')} {event.get('hora', '')}")
                    if ecol3.button("🗑", key=f"rm_event_{case['id']}_{event['id']}"):
                        delete_event(store, case["id"], event["id"])
                        persist()
                        st.rerun()

                with st.form(f"nuevo_evento_{case['id']}"):
                    titulo = st.text_input("Evento")
                    fecha = st.date_input("Fecha", value=date.today())
                    hora = st.text_input("Hora", value="09:00")
                    if st.form_submit_button("Agregar evento"):
                        if titulo.strip():
                            case["eventos"].append(
                                {
                                    "id": new_id("e"),
                                    "titulo": titulo.strip(),
                                    "fecha": fecha.isoformat(),
                                    "hora": hora,
                                }
                            )
                            persist()
                            st.rerun()

            with tab_tiempo:
                rate = hourly_rate(store, case)
                if rate:
                    st.caption(f"Tarifa aplicada: ${rate:,.0f} COP/hora")
                for entry in case.get("tiempo", []):
                    normalize_time_entry(entry)
                    minutos = int(entry.get("minutos", 0))
                    valor = entry_value(minutos, rate)
                    tcol1, tcol2, tcol3, tcol4, tcol5 = st.columns([2, 1, 1, 1.5, 1.2])
                    tcol1.write(entry.get("descripcion", ""))
                    tcol2.write(f"{minutos} min")
                    tcol3.write(f"${valor:,.0f}" if valor else "—")
                    estado = entry.get("estado_facturacion", "pendiente")
                    tcol4.write(BILLING_LABELS.get(estado, estado))
                    nuevo_estado = tcol5.selectbox(
                        "Estado",
                        BILLING_STATES,
                        index=list(BILLING_STATES).index(estado),
                        format_func=lambda k: BILLING_LABELS[k],
                        key=f"time_state_{case['id']}_{entry['id']}",
                        label_visibility="collapsed",
                    )
                    if nuevo_estado != estado:
                        set_time_billing_state(store, case["id"], entry["id"], nuevo_estado)
                        persist()
                        st.rerun()

                with st.form(f"nuevo_tiempo_{case['id']}"):
                    minutos = st.number_input("Minutos", min_value=0, step=15, value=30)
                    descripcion = st.text_input("Descripción")
                    estado_nuevo = st.selectbox(
                        "Estado de facturación",
                        BILLING_STATES,
                        format_func=lambda k: BILLING_LABELS[k],
                    )
                    if st.form_submit_button("Registrar tiempo"):
                        entry = {
                            "id": new_id("tm"),
                            "fecha": date.today().isoformat(),
                            "minutos": int(minutos),
                            "descripcion": descripcion.strip(),
                            "estado_facturacion": estado_nuevo,
                        }
                        normalize_time_entry(entry)
                        case["tiempo"].append(entry)
                        persist()
                        st.rerun()

            nuevo_estado = st.selectbox(
                "Estado del caso",
                CASE_STATES,
                index=list(CASE_STATES).index(case.get("estado", "activo")),
                format_func=lambda k: STATUS_LABELS[k],
            )
            if st.button("Actualizar estado", key=f"estado_{case['id']}"):
                case["estado"] = nuevo_estado
                persist()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_vista_clientes(query: str) -> None:
    store = st.session_state.despacho_store
    st.markdown(
        """
        <div class="lx-header">
            <div class="lx-title">Clientes</div>
            <div class="lx-subtitle">Administra la base de clientes vinculada a tus casos.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "cliente_seleccionado_id" not in st.session_state:
        clientes_init = store.get("clientes", [])
        st.session_state.cliente_seleccionado_id = clientes_init[0]["id"] if clientes_init else ""

    clientes = store.get("clientes", [])
    if query:
        clientes = [
            client
            for client in clientes
            if query in client.get("nombre", "").lower()
            or query in client.get("documento", "").lower()
            or query in client.get("email", "").lower()
        ]

    col_list, col_detail = st.columns([1.2, 1.3])
    with col_list:
        st.markdown('<div class="lx-panel"><div class="lx-panel-title">Directorio</div>', unsafe_allow_html=True)
        if not clientes:
            st.markdown('<div class="lx-empty">No hay clientes registrados.</div>', unsafe_allow_html=True)
        else:
            options = {client["id"]: client.get("nombre", "") for client in clientes}
            keys = list(options.keys())
            selected = st.radio(
                "Clientes",
                options=keys,
                format_func=lambda cid: options[cid],
                index=keys.index(st.session_state.cliente_seleccionado_id)
                if st.session_state.cliente_seleccionado_id in options
                else 0,
                label_visibility="collapsed",
            )
            if selected != st.session_state.cliente_seleccionado_id:
                st.session_state.cliente_seleccionado_id = selected
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.get("mostrar_formulario_cliente"):
            with st.expander("Nuevo cliente", expanded=True):
                with st.form("nuevo_cliente"):
                    nombre = st.text_input("Nombre / Razón social")
                    documento = st.text_input("Documento / NIT")
                    email = st.text_input("Correo")
                    telefono = st.text_input("Teléfono")
                    if st.form_submit_button("Guardar cliente"):
                        if nombre.strip():
                            new_client = {
                                "id": new_id("cl"),
                                "nombre": nombre.strip(),
                                "documento": documento.strip(),
                                "email": email.strip(),
                                "telefono": telefono.strip(),
                            }
                            store["clientes"].append(new_client)
                            st.session_state.cliente_seleccionado_id = new_client["id"]
                            st.session_state.mostrar_formulario_cliente = False
                            persist()
                            st.rerun()
                        else:
                            st.error("El nombre es obligatorio.")
        elif st.button("➕ Nuevo cliente", use_container_width=True):
            st.session_state.mostrar_formulario_cliente = True
            st.rerun()

    with col_detail:
        client = find_client(store, st.session_state.cliente_seleccionado_id)
        st.markdown('<div class="lx-panel"><div class="lx-panel-title">Detalle del cliente</div>', unsafe_allow_html=True)
        if not client:
            st.markdown('<div class="lx-empty">Selecciona o crea un cliente.</div>', unsafe_allow_html=True)
        else:
            with st.form(f"edit_client_{client['id']}"):
                nombre = st.text_input("Nombre", value=client.get("nombre", ""))
                documento = st.text_input("Documento", value=client.get("documento", ""))
                email = st.text_input("Email", value=client.get("email", ""))
                telefono = st.text_input("Teléfono", value=client.get("telefono", ""))
                save, delete = st.columns(2)
                if save.form_submit_button("Guardar cambios", use_container_width=True):
                    client["nombre"] = nombre.strip()
                    client["documento"] = documento.strip()
                    client["email"] = email.strip()
                    client["telefono"] = telefono.strip()
                    persist()
                    st.success("Cliente actualizado.")
                    st.rerun()
                if delete.form_submit_button("Eliminar cliente", use_container_width=True):
                    delete_client(store, client["id"])
                    remaining = store.get("clientes", [])
                    st.session_state.cliente_seleccionado_id = remaining[0]["id"] if remaining else ""
                    persist()
                    st.rerun()

            related = cases_for_client(store, client["id"])
            st.markdown(f"**Casos vinculados ({len(related)})**")
            if related:
                for case in related:
                    if st.button(
                        f"{case.get('nombre', '')} — {case.get('radicado', '')}",
                        key=f"goto_case_{case['id']}",
                    ):
                        st.session_state.lexivox_vista = "casos"
                        st.session_state.caso_seleccionado_id = case["id"]
                        st.rerun()
            else:
                st.caption("Sin casos asociados.")
        st.markdown("</div>", unsafe_allow_html=True)


def render_vista_tareas(query: str) -> None:
    store = st.session_state.despacho_store
    st.markdown(
        """
        <div class="lx-header">
            <div class="lx-title">Tareas</div>
            <div class="lx-subtitle">Gestiona todas las tareas abiertas del despacho.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filtro = st.selectbox(
        "Filtrar por estado",
        options=["todas_abiertas", "pendiente", "en_curso", "vencidas"],
        format_func=lambda k: {
            "todas_abiertas": "Todas abiertas",
            "pendiente": "Pendientes",
            "en_curso": "En curso",
            "vencidas": "Vencidas",
        }[k],
    )

    tasks = all_open_tasks(store)
    today = date.today()
    if filtro == "pendiente":
        tasks = [task for task in tasks if task.get("estado") == "pendiente"]
    elif filtro == "en_curso":
        tasks = [task for task in tasks if task.get("estado") == "en_curso"]
    elif filtro == "vencidas":
        tasks = [
            task
            for task in tasks
            if (due := parse_date(task.get("vence", ""))) and due < today
        ]

    if query:
        tasks = [
            task
            for task in tasks
            if query in task.get("titulo", "").lower()
            or query in task.get("caso", "").lower()
            or query in task.get("cliente", "").lower()
        ]

    st.markdown('<div class="lx-panel">', unsafe_allow_html=True)
    if not tasks:
        st.markdown('<div class="lx-empty">No hay tareas con este filtro.</div>', unsafe_allow_html=True)
    else:
        for task in tasks:
            cols = st.columns([3, 1, 1, 2, 0.6, 0.6])
            cols[0].write(f"**{task.get('titulo', '')}**")
            cols[1].write(TASK_LABELS.get(task.get("estado", ""), ""))
            cols[2].write(task.get("vence", ""))
            cols[3].write(task.get("caso", ""))
            if cols[4].button("✓", key=f"global_done_{task['caso_id']}_{task['id']}"):
                complete_task(store, task["caso_id"], task["id"])
                persist()
                st.rerun()
            if cols[5].button("Ir", key=f"global_go_{task['caso_id']}_{task['id']}"):
                st.session_state.lexivox_vista = "casos"
                st.session_state.caso_seleccionado_id = task["caso_id"]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_vista_calendario(query: str) -> None:
    store = st.session_state.despacho_store
    st.markdown(
        """
        <div class="lx-header">
            <div class="lx-title">Calendario</div>
            <div class="lx-subtitle">Consulta audiencias, vencimientos y eventos del despacho.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_cal, col_list = st.columns([1, 1.5])
    with col_cal:
        selected = st.date_input("Fecha seleccionada", value=st.session_state.calendario_fecha)
        st.session_state.calendario_fecha = selected
        week_start = selected - timedelta(days=selected.weekday())
        week_end = week_start + timedelta(days=6)
        st.caption(f"Semana: {week_start.isoformat()} → {week_end.isoformat()}")

        month_start = selected.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        month_events = events_in_range(store, month_start, month_end)
        st.markdown("**Resumen del mes**")
        st.metric("Eventos del mes", len(month_events))

    events_day = events_in_range(store, selected, selected)
    events_week = events_in_range(store, week_start, week_end)
    if query:
        events_day = [
            event
            for event in events_day
            if query in event.get("titulo", "").lower() or query in event.get("caso", "").lower()
        ]
        events_week = [
            event
            for event in events_week
            if query in event.get("titulo", "").lower() or query in event.get("caso", "").lower()
        ]

    with col_list:
        st.markdown('<div class="lx-panel"><div class="lx-panel-title">Eventos del día</div>', unsafe_allow_html=True)
        if events_day:
            for event in events_day:
                if st.button(
                    f"{event.get('hora', '')} · {event.get('titulo', '')} ({event.get('caso', '')})",
                    key=f"cal_day_{event.get('id', '')}_{event.get('caso_id', '')}",
                ):
                    st.session_state.lexivox_vista = "casos"
                    st.session_state.caso_seleccionado_id = event["caso_id"]
                    st.rerun()
        else:
            st.markdown('<div class="lx-empty">Sin eventos para esta fecha.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="lx-panel"><div class="lx-panel-title">Agenda de la semana</div>', unsafe_allow_html=True)
    if events_week:
        df = pd.DataFrame(events_week)[["fecha", "hora", "titulo", "caso", "cliente"]]
        df.columns = ["Fecha", "Hora", "Evento", "Caso", "Cliente"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="lx-empty">No hay eventos programados esta semana.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    tasks_due = []
    for case in store.get("casos", []):
        for task in case.get("tareas", []):
            due = parse_date(task.get("vence", ""))
            if due and week_start <= due <= week_end and task.get("estado") != "completada":
                tasks_due.append(
                    {
                        "Vence": due.isoformat(),
                        "Tarea": task.get("titulo", ""),
                        "Caso": case.get("nombre", ""),
                        "Cliente": client_name(store, case.get("cliente_id", "")),
                    }
                )
    if tasks_due:
        st.markdown("#### Vencimientos de tareas en la semana")
        st.dataframe(pd.DataFrame(tasks_due), use_container_width=True, hide_index=True)


def render_vista_configuracion() -> None:
    store = st.session_state.despacho_store
    st.markdown(
        """
        <div class="lx-header">
            <div class="lx-title">Configuración</div>
            <div class="lx-subtitle">Respaldo, importación y preferencias del despacho.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lx-panel"><div class="lx-panel-title">Respaldo e importación</div>', unsafe_allow_html=True)
    col_json, col_xlsx, col_reset = st.columns(3)

    with col_json:
        st.download_button(
            "Descargar JSON",
            data=export_json(store),
            file_name="despacho.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded_json = st.file_uploader("Importar JSON", type=["json"], key="upload_json_cfg")
        if uploaded_json and st.button("Aplicar JSON", key="apply_json_cfg"):
            st.session_state.despacho_store = import_json(uploaded_json.getvalue())
            persist()
            st.success("Datos JSON importados.")
            st.rerun()

    with col_xlsx:
        st.download_button(
            "Descargar Excel",
            data=export_excel(store),
            file_name="despacho.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        uploaded_xlsx = st.file_uploader("Importar Excel", type=["xlsx"], key="upload_xlsx_cfg")
        if uploaded_xlsx and st.button("Aplicar Excel", key="apply_xlsx_cfg"):
            st.session_state.despacho_store = import_excel(uploaded_xlsx.getvalue())
            persist()
            st.success("Datos Excel importados.")
            st.rerun()

    with col_reset:
        if st.button("Restaurar demo", use_container_width=True, key="reset_cfg"):
            st.session_state.despacho_store = reset_store()
            casos = st.session_state.despacho_store.get("casos", [])
            st.session_state.caso_seleccionado_id = casos[0]["id"] if casos else ""
            st.success("Se restauraron los datos de ejemplo.")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="lx-panel"><div class="lx-panel-title">Resumen del despacho</div>', unsafe_allow_html=True)
    metricas = global_metrics(store)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Casos totales", len(store.get("casos", [])))
    c2.metric("Clientes", metricas["clientes"])
    c3.metric("Minutos sin facturar", metricas["sin_facturar"])
    c4.metric("Por facturar (COP)", f"${metricas.get('valor_pendiente', 0):,.0f}")
    c5.metric("Tareas vencidas", metricas["vencidas"])
    st.markdown("</div>", unsafe_allow_html=True)

    config = store.setdefault("config", {})
    st.markdown('<div class="lx-panel"><div class="lx-panel-title">Tarifas del despacho</div>', unsafe_allow_html=True)
    tarifa_col, moneda_col = st.columns(2)
    with tarifa_col:
        tarifa_default = st.number_input(
            "Tarifa default por hora (COP)",
            min_value=0,
            step=10_000,
            value=int(config.get("tarifa_default_hora", 150_000)),
            key="cfg_tarifa_default",
        )
    with moneda_col:
        moneda = st.text_input("Moneda", value=config.get("moneda", "COP"), key="cfg_moneda")
    if st.button("Guardar tarifas", key="save_cfg_tarifas"):
        config["tarifa_default_hora"] = int(tarifa_default)
        config["moneda"] = moneda.strip() or "COP"
        persist()
        st.success("Tarifas guardadas.")
    st.caption("También puede gestionar tarifas por cliente en la vista Facturación.")
    st.markdown("</div>", unsafe_allow_html=True)

    from legal_ui.auth import use_database_storage
    from legal_ui.auth_ui import render_admin_user_panel
    from legal_ui.database import DB_PATH, export_database_bytes

    st.markdown('<div class="lx-panel"><div class="lx-panel-title">Persistencia</div>', unsafe_allow_html=True)
    if use_database_storage():
        st.success(f"Datos guardados en base SQLite: `{DB_PATH.name}`")
        st.download_button(
            "Descargar respaldo SQLite",
            data=export_database_bytes(),
            file_name="lexivox_backup.db",
            mime="application/octet-stream",
            use_container_width=True,
        )
        st.caption(
            "En Streamlit Cloud descarga este respaldo periódicamente. "
            "Cada usuario del despacho tiene datos aislados."
        )
    else:
        st.info("Modo JSON local (`data/despacho.json`). Inicia sesión para usar SQLite.")
    st.markdown("</div>", unsafe_allow_html=True)

    render_admin_user_panel()
