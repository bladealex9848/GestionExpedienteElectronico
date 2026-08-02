from __future__ import annotations

import streamlit as st

from legal_ui.iley_views import render_iley_consulta
from legal_ui.lexivox_theme import LEXIVOX_CSS

st.set_page_config(
    page_title="Consulta normativa iLey CO | garciabermeo.net",
    page_icon="📚",
    layout="wide",
)

st.markdown(LEXIVOX_CSS, unsafe_allow_html=True)
render_iley_consulta()
