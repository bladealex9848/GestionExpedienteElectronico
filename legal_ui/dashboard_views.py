from __future__ import annotations

import pandas as pd
import streamlit as st

from legal_ui.billing import (
    BILLING_LABELS,
    BILLING_STATES,
    billing_by_client,
    billing_totals,
    executive_dashboard,
    export_billing_excel,
    normalize_store_billing,
)
from legal_ui.despacho_store import set_time_billing_state


def render_vista_dashboard(persist) -> None:
    store = st.session_state.despacho_store
    normalize_store_billing(store)
    data = executive_dashboard(store)

    st.markdown(
        """
        <div class="lx-header">
            <div class="lx-title">Dashboard ejecutivo</div>
            <div class="lx-subtitle">Visión general del despacho: casos, riesgo, plazos y facturación.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    billing = data["billing"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Casos totales", data["total_casos"])
    c2.metric("Clientes", data["clientes"])
    c3.metric("Por facturar", f"${billing['pendiente']:,.0f}")
    c4.metric("Facturado", f"${billing['facturado']:,.0f}")
    c5.metric("Cobrado", f"${billing['cobrado']:,.0f}")

    col_estado, col_riesgo = st.columns([1, 1.2])
    with col_estado:
        st.markdown("#### Casos por estado")
        estado_df = pd.DataFrame(
            [{"Estado": k, "Cantidad": v} for k, v in data["casos_por_estado"].items() if v > 0]
        )
        if estado_df.empty:
            st.info("Sin casos registrados.")
        else:
            try:
                import plotly.express as px

                fig = px.bar(estado_df, x="Estado", y="Cantidad", color="Estado")
                fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=280)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.dataframe(estado_df, use_container_width=True, hide_index=True)

    with col_riesgo:
        st.markdown("#### Casos con mayor riesgo")
        if data["casos_riesgo"]:
            st.dataframe(pd.DataFrame(data["casos_riesgo"]), use_container_width=True, hide_index=True)
        else:
            st.success("No hay casos activos con tareas vencidas o próximas.")

    st.markdown("#### Plazos críticos (7 días)")
    if data["plazos_criticos"]:
        st.dataframe(pd.DataFrame(data["plazos_criticos"]), use_container_width=True, hide_index=True)
    else:
        st.info("Sin plazos críticos en la próxima semana.")

    st.markdown("#### Facturación por cliente")
    summary = billing_by_client(store)
    if summary.empty:
        st.info("Aún no hay horas registradas.")
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)


def render_vista_facturacion(persist) -> None:
    store = st.session_state.despacho_store
    normalize_store_billing(store)

    st.markdown(
        """
        <div class="lx-header">
            <div class="lx-title">Facturación</div>
            <div class="lx-subtitle">Control de horas, tarifas y estados de cobro del despacho.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    config = store.setdefault("config", {})
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        tarifa = st.number_input(
            "Tarifa default por hora (COP)",
            min_value=0,
            step=10_000,
            value=int(config.get("tarifa_default_hora", 150_000)),
            key="billing_default_rate",
        )
    with cfg_col2:
        moneda = st.text_input("Moneda", value=config.get("moneda", "COP"), key="billing_currency")
    if st.button("Guardar tarifas generales", key="save_billing_config"):
        config["tarifa_default_hora"] = int(tarifa)
        config["moneda"] = moneda.strip() or "COP"
        persist()
        st.success("Tarifas actualizadas.")

    totals = billing_totals(store)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pendiente", f"${totals['pendiente']:,.0f}")
    m2.metric("Facturado", f"${totals['facturado']:,.0f}")
    m3.metric("Cobrado", f"${totals['cobrado']:,.0f}")
    m4.metric("Minutos pendientes", int(totals["minutos_pendientes"]))

    from legal_ui.billing import all_time_entries

    entries = all_time_entries(store)
    filtro = st.selectbox(
        "Filtrar estado",
        options=["todos", *BILLING_STATES],
        format_func=lambda k: "Todos" if k == "todos" else BILLING_LABELS[k],
    )
    if filtro != "todos":
        entries = [row for row in entries if row.get("estado_facturacion") == filtro]

    st.markdown('<div class="lx-panel">', unsafe_allow_html=True)
    if not entries:
        st.info("No hay registros de tiempo.")
    else:
        for row in entries:
            cols = st.columns([2.2, 1.2, 1, 1, 1.2, 1.2, 0.8, 0.8, 0.8])
            cols[0].write(f"**{row.get('descripcion') or 'Sin descripción'}**")
            cols[1].write(row.get("caso", ""))
            cols[2].write(f"{row.get('minutos', 0)} min")
            cols[3].write(f"${row.get('valor', 0):,.0f}")
            cols[4].write(BILLING_LABELS.get(row.get("estado_facturacion", ""), ""))
            cols[5].write(row.get("fecha", ""))
            if cols[6].button("Fac.", key=f"bill_f_{row['caso_id']}_{row['id']}"):
                set_time_billing_state(store, row["caso_id"], row["id"], "facturado")
                persist()
                st.rerun()
            if cols[7].button("Cob.", key=f"bill_c_{row['caso_id']}_{row['id']}"):
                set_time_billing_state(store, row["caso_id"], row["id"], "cobrado")
                persist()
                st.rerun()
            if cols[8].button("Pen.", key=f"bill_p_{row['caso_id']}_{row['id']}"):
                set_time_billing_state(store, row["caso_id"], row["id"], "pendiente")
                persist()
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        "Descargar reporte Excel",
        data=export_billing_excel(store),
        file_name="facturacion_despacho.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    with st.expander("Tarifas por cliente"):
        for client in store.get("clientes", []):
            new_rate = st.number_input(
                f"{client.get('nombre', '')} (COP/hora, 0 = usar default)",
                min_value=0,
                step=10_000,
                value=int(client.get("tarifa_hora", 0)),
                key=f"client_rate_{client['id']}",
            )
            if st.button(f"Guardar tarifa — {client.get('nombre', '')}", key=f"save_rate_{client['id']}"):
                client["tarifa_hora"] = int(new_rate)
                persist()
                st.success("Tarifa de cliente actualizada.")
                st.rerun()
