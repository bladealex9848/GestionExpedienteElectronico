from __future__ import annotations

import urllib.parse

import streamlit as st

from legal_ui.brand import BRAND_NAME
from legal_ui.iley_service import (
    ILEY_URL,
    export_articles_markdown,
    format_article_text,
    get_article,
    list_normas,
    list_sections,
    load_norma,
    search_articles,
)
from legal_ui.tool_bridge import render_active_case_banner


def render_iley_consulta() -> None:
    st.markdown(
        f"""
        <div class="lx-header">
            <div class="lx-title">Consulta normativa iLey CO</div>
            <div class="lx-subtitle">
                Constitución y normas clave de Colombia: búsqueda por artículo o palabras clave,
                inspirado en <a href="{ILEY_URL}" target="_blank">iLey CO</a>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_active_case_banner(show_load_button=False)

    st.info(
        "Información de dominio público con fines consultivos. Verifique siempre contra la norma "
        "oficial antes de usarla en actuaciones judiciales. Referencia: "
        f"[iLey CO — Fusense]({ILEY_URL})."
    )

    normas = list_normas()
    norma_labels = {row["id"]: f"{row['nombre']} ({row['anio']})" for row in normas}
    norma_id = st.selectbox(
        "Norma",
        options=list(norma_labels.keys()),
        format_func=lambda key: norma_labels[key],
        key="iley_norma",
    )

    tab_buscar, tab_articulo, tab_indice = st.tabs(
        ["Búsqueda por palabras", "Ir a artículo", "Índice por secciones"]
    )

    with tab_buscar:
        query = st.text_input(
            "Buscar",
            placeholder="Ej.: debido proceso, tutela, artículo 29, petición...",
            key="iley_query",
        )
        if query.strip():
            results = search_articles(norma_id, query)
            if not results:
                st.warning("No se encontraron artículos para esa búsqueda.")
            else:
                st.caption(f"{len(results)} resultado(s)")
                _render_results(results, prefix="search")

    with tab_articulo:
        numero = st.number_input("Número de artículo", min_value=1, step=1, value=29, key="iley_num")
        if st.button("Consultar artículo", type="primary", key="iley_go_article"):
            article = get_article(norma_id, int(numero))
            if article:
                _render_results([article], prefix="direct")
            else:
                st.warning("Artículo no encontrado en esta norma.")

    with tab_indice:
        if norma_id != "cp1991":
            st.caption("El índice detallado está disponible para la Constitución Política.")
            articles = load_norma(norma_id).get("articulos", [])
            for article in articles:
                st.markdown(f"**Artículo {article['numero']}** — {article.get('seccion', '')}")
                with st.expander("Ver texto"):
                    st.write(article.get("texto", ""))
        else:
            sections = list_sections(norma_id)
            section_names = [row["nombre"] for row in sections]
            selected = st.selectbox("Sección", section_names, key="iley_section")
            section = next(row for row in sections if row["nombre"] == selected)
            cols = st.columns(6)
            for idx, number in enumerate(section.get("articulos", [])):
                if cols[idx % 6].button(str(number), key=f"iley_idx_{selected}_{number}"):
                    article = get_article(norma_id, number)
                    if article:
                        st.session_state["iley_selected_article"] = article
            selected_article = st.session_state.get("iley_selected_article")
            if selected_article and selected_article.get("norma_id") == norma_id:
                _render_results([selected_article], prefix="index")


def _render_results(articles: list[dict], *, prefix: str) -> None:
    for idx, article in enumerate(articles):
        st.markdown(f"### Artículo {article.get('numero', '')}")
        if article.get("seccion"):
            st.caption(article["seccion"])
        st.markdown(
            f"<div class='lx-panel'>{article.get('texto', '')}</div>",
            unsafe_allow_html=True,
        )

        text = format_article_text(article)
        col_copy, col_mail, col_case = st.columns(3)
        col_copy.download_button(
            "Descargar .txt",
            data=text.encode("utf-8"),
            file_name=f"articulo_{article.get('numero', idx)}.txt",
            mime="text/plain",
            key=f"{prefix}_dl_{article.get('numero', idx)}_{idx}",
            use_container_width=True,
        )
        try:
            email = st.secrets.get("iley", {}).get("support_email", "iley@fusense.com")
        except Exception:
            email = "iley@fusense.com"
        subject = f"Artículo {article.get('numero', '')} — {article.get('norma', BRAND_NAME)}"
        mailto = (
            f"mailto:{email}?subject={urllib.parse.quote(subject)}"
            f"&body={urllib.parse.quote(text[:1800])}"
        )
        col_mail.link_button(
            "Enviar por correo",
            mailto,
            use_container_width=True,
        )
        if col_case.button(
            "Copiar al portapapeles",
            key=f"{prefix}_copy_{article.get('numero', idx)}_{idx}",
            use_container_width=True,
        ):
            st.session_state[f"{prefix}_clipboard"] = text
            st.toast("Texto listo. Use Ctrl+C en el cuadro inferior.")
        if st.session_state.get(f"{prefix}_clipboard") == text:
            st.text_area("Texto para copiar", value=text, height=160, key=f"{prefix}_ta_{idx}")

    bundle = export_articles_markdown(articles)
    st.download_button(
        "Descargar selección (.md)",
        data=bundle.encode("utf-8"),
        file_name="consulta_normativa.md",
        mime="text/markdown",
        key=f"{prefix}_bundle",
        use_container_width=True,
    )
