from __future__ import annotations

import streamlit as st

from legal_ui.database import (
    authenticate,
    auth_disabled,
    bootstrap_admin_from_secrets,
    create_user,
    get_user_by_id,
    init_db,
    update_password,
)

LOCAL_USER_ID = "__local__"


def init_auth() -> None:
    init_db()
    bootstrap_admin_from_secrets()


def get_current_user_id() -> str | None:
    if auth_disabled():
        return LOCAL_USER_ID
    if st.session_state.get("lexivox_authenticated"):
        return st.session_state.get("lexivox_user_id")
    return None


def get_current_user() -> dict | None:
    user_id = get_current_user_id()
    if not user_id:
        return None
    if user_id == LOCAL_USER_ID:
        return {
            "id": LOCAL_USER_ID,
            "username": "local",
            "nombre": "Modo local",
            "rol": "admin",
        }
    return get_user_by_id(user_id)


def is_admin() -> bool:
    user = get_current_user()
    return bool(user and user.get("rol") == "admin")


def login(username: str, password: str) -> bool:
    if auth_disabled():
        st.session_state.lexivox_authenticated = True
        st.session_state.lexivox_user_id = LOCAL_USER_ID
        st.session_state.lexivox_username = "local"
        return True
    user = authenticate(username, password)
    if not user:
        return False
    _set_session_user(user)
    return True


def login_with_user(user: dict) -> None:
    _set_session_user(user)


def _set_session_user(user: dict) -> None:
    st.session_state.lexivox_authenticated = True
    st.session_state.lexivox_user_id = user["id"]
    st.session_state.lexivox_username = user["username"]
    st.session_state.lexivox_user_nombre = user["nombre"]
    st.session_state.lexivox_user_rol = user["rol"]


def logout() -> None:
    for key in (
        "lexivox_authenticated",
        "lexivox_user_id",
        "lexivox_username",
        "lexivox_user_nombre",
        "lexivox_user_rol",
        "despacho_store",
    ):
        st.session_state.pop(key, None)


def use_database_storage() -> bool:
    return get_current_user_id() is not None
