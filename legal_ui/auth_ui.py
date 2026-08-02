from __future__ import annotations

import streamlit as st

from legal_ui.auth import auth_disabled, get_current_user, login, login_with_user, logout
from legal_ui.brand import BRAND_NAME
from legal_ui.database import create_user
from legal_ui.google_oauth import (
    build_authorization_url,
    is_google_oauth_configured,
    try_handle_google_callback,
)


def ensure_authenticated() -> bool:
    if auth_disabled():
        if not st.session_state.get("lexivox_authenticated"):
            login("", "")
        return True

    if st.session_state.get("lexivox_authenticated"):
        return True

    if is_google_oauth_configured():
        try:
            google_user = try_handle_google_callback()
        except Exception as exc:
            st.error(str(exc))
            google_user = None
        if google_user:
            login_with_user(google_user)
            st.success(f"Bienvenido, {google_user.get('nombre', '')}.")
            st.rerun()

    st.markdown(
        f"""
        <div style="max-width:420px;margin:3rem auto;padding:2rem;border-radius:16px;
        border:1px solid #dbeafe;background:#f8fbff;">
        <h2 style="margin-top:0;">{BRAND_NAME}</h2>
        <p style="opacity:0.85;">Inicia sesión o regístrate para acceder al despacho.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_box = st.container()
    with login_box:
        if is_google_oauth_configured():
            st.link_button(
                "Continuar con Google",
                build_authorization_url(),
                use_container_width=True,
                type="primary",
            )
            st.caption("Registro e inicio de sesión con tu cuenta de Google.")
            st.markdown(
                '<p style="text-align:center;color:#64748b;margin:1rem 0;">— o —</p>',
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "Para habilitar registro con Google, configure `google_oauth` en "
                "`.streamlit/secrets.toml` (client_id, client_secret, redirect_uri)."
            )

        with st.form("lexivox_login"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Entrar con usuario y contraseña", use_container_width=True)
            if submitted:
                if login(username, password):
                    st.rerun()
                st.error("Usuario o contraseña incorrectos.")

    st.caption(
        "Primera instalación: configure `lexivox_auth.admin_password` en "
        "`.streamlit/secrets.toml` o la variable `LEXIVOX_ADMIN_PASSWORD`."
    )
    return False


def render_user_badge() -> None:
    user = get_current_user()
    if not user:
        return
    st.caption(f"👤 {user.get('nombre', user.get('username', ''))} · {user.get('rol', '')}")
    if not auth_disabled() and st.button("Cerrar sesión", key="lexivox_logout", use_container_width=True):
        logout()
        st.rerun()


def render_admin_user_panel() -> None:
    from legal_ui.auth import is_admin
    from legal_ui.database import list_users

    if not is_admin():
        return

    st.markdown("#### Usuarios del despacho")
    users = list_users()
    if users:
        st.dataframe(
            [
                {
                    "Usuario": row["username"],
                    "Nombre": row["nombre"],
                    "Correo": row.get("email") or "—",
                    "Google": "Sí" if row.get("google_id") else "No",
                    "Rol": row["rol"],
                    "Activo": "Sí" if row["activo"] else "No",
                }
                for row in users
            ],
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Crear usuario"):
        with st.form("create_user_form"):
            username = st.text_input("Usuario")
            nombre = st.text_input("Nombre completo")
            password = st.text_input("Contraseña temporal", type="password")
            rol = st.selectbox("Rol", ["abogado", "admin"])
            if st.form_submit_button("Crear usuario"):
                if username.strip() and password.strip() and nombre.strip():
                    try:
                        create_user(username, password, nombre, rol=rol)
                        st.success(f"Usuario {username} creado.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"No se pudo crear el usuario: {exc}")
                else:
                    st.error("Completa todos los campos.")

    with st.expander("Cambiar mi contraseña"):
        with st.form("change_password_form"):
            new_password = st.text_input("Nueva contraseña", type="password")
            confirm = st.text_input("Confirmar contraseña", type="password")
            if st.form_submit_button("Actualizar contraseña"):
                user = get_current_user()
                if user and new_password == confirm and len(new_password) >= 8:
                    from legal_ui.database import update_password

                    update_password(user["id"], new_password)
                    st.success("Contraseña actualizada.")
                else:
                    st.error("Las contraseñas deben coincidir y tener al menos 8 caracteres.")
