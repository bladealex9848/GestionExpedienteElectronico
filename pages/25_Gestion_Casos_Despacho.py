from __future__ import annotations

import importlib
from datetime import date

import streamlit as st

from legal_ui.auth import init_auth
from legal_ui import despacho_store

importlib.reload(despacho_store)
from legal_ui.despacho_store import load_store
from legal_ui.lexivox_sidebar import render_lexivox_sidebar
from legal_ui.brand import BRAND_NAME
from legal_ui.lexivox_theme import LEXIVOX_CSS
from legal_ui.dashboard_views import render_vista_dashboard, render_vista_facturacion
from legal_ui.lexivox_views import (
    persist,
    render_busqueda_global,
    render_metricas,
    render_vista_calendario,
    render_vista_casos,
    render_vista_clientes,
    render_vista_configuracion,
    render_vista_tareas,
)


st.set_page_config(
    page_title=f"{BRAND_NAME} | Gestión del Despacho",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(LEXIVOX_CSS, unsafe_allow_html=True)

init_auth()

if "lexivox_vista" not in st.session_state:
    st.session_state.lexivox_vista = "casos"
if "despacho_store" not in st.session_state:
    st.session_state.despacho_store = load_store()
if "caso_seleccionado_id" not in st.session_state:
    casos = st.session_state.despacho_store.get("casos", [])
    st.session_state.caso_seleccionado_id = casos[0]["id"] if casos else ""
if "filtro_casos" not in st.session_state:
    st.session_state.filtro_casos = "todos"
if "calendario_fecha" not in st.session_state:
    st.session_state.calendario_fecha = date.today()

with st.sidebar:
    query = render_lexivox_sidebar(st.session_state.lexivox_vista)

vista = st.session_state.lexivox_vista
if vista not in ("dashboard", "facturacion"):
    render_metricas()
render_busqueda_global(query)

if vista == "dashboard":
    render_vista_dashboard(persist)
elif vista == "casos":
    render_vista_casos(query)
elif vista == "clientes":
    render_vista_clientes(query)
elif vista == "tareas":
    render_vista_tareas(query)
elif vista == "calendario":
    render_vista_calendario(query)
elif vista == "facturacion":
    render_vista_facturacion(persist)
else:
    render_vista_configuracion()
