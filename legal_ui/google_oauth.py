from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import streamlit as st

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPES = "openid email profile"


def _oauth_config() -> dict[str, str]:
    cfg: dict[str, str] = {}
    try:
        raw = st.secrets.get("google_oauth", {})
        if isinstance(raw, dict):
            cfg = {str(k): str(v) for k, v in raw.items() if v}
    except Exception:
        pass
    cfg.setdefault("client_id", os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip())
    cfg.setdefault("client_secret", os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip())
    redirect = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
    cfg.setdefault("redirect_uri", redirect)
    if cfg.get("redirect_uri"):
        cfg["redirect_uri"] = cfg["redirect_uri"].rstrip("/")
    return cfg


def is_google_oauth_configured() -> bool:
    cfg = _oauth_config()
    return bool(cfg.get("client_id") and cfg.get("client_secret") and cfg.get("redirect_uri"))


def _state_secret() -> str:
    cfg = _oauth_config()
    secret = cfg.get("client_secret") or os.getenv("GOOGLE_OAUTH_STATE_SECRET", "").strip()
    if not secret:
        raise ValueError(
            "OAuth no configurado de forma segura: falta client_secret o GOOGLE_OAUTH_STATE_SECRET."
        )
    return secret


def create_oauth_state() -> str:
    payload = secrets.token_urlsafe(24)
    sig = hmac.new(
        _state_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:20]
    return f"{payload}.{sig}"


def verify_oauth_state(state: str) -> bool:
    try:
        payload, sig = state.rsplit(".", 1)
    except ValueError:
        return False
    expected = hmac.new(
        _state_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:20]
    return secrets.compare_digest(sig, expected)


def _query_param(key: str) -> str:
    value = st.query_params.get(key)
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value or "").strip()


def build_authorization_url() -> str:
    cfg = _oauth_config()
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": create_oauth_state(),
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Google rechazó el intercambio del código OAuth: {detail}") from exc


def _get_json(url: str, *, access_token: str) -> dict[str, Any]:
    request = urllib.request.Request(url, method="GET")
    request.add_header("Authorization", f"Bearer {access_token}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"No se pudo leer el perfil de Google: {detail}") from exc


def exchange_code_for_profile(code: str) -> dict[str, str]:
    cfg = _oauth_config()
    token_payload = _post_form(
        GOOGLE_TOKEN_URL,
        {
            "code": code,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "redirect_uri": cfg["redirect_uri"],
            "grant_type": "authorization_code",
        },
    )
    access_token = token_payload.get("access_token")
    if not access_token:
        raise ValueError("Google no devolvió un token de acceso válido.")

    profile = _get_json(GOOGLE_USERINFO_URL, access_token=access_token)
    google_id = str(profile.get("sub", "")).strip()
    email = str(profile.get("email", "")).strip().lower()
    nombre = str(profile.get("name") or profile.get("given_name") or email).strip()
    if not google_id or not email:
        raise ValueError("No se pudo obtener el perfil de Google.")
    if profile.get("email_verified") is False:
        raise ValueError("La cuenta de Google no tiene el correo verificado.")
    return {"google_id": google_id, "email": email, "nombre": nombre}


def clear_oauth_query_params() -> None:
    for key in ("code", "state", "scope", "authuser", "prompt", "error", "error_description"):
        if key in st.query_params:
            del st.query_params[key]


def try_handle_google_callback() -> dict | None:
    error = _query_param("error")
    if error:
        clear_oauth_query_params()
        raise ValueError(f"Google rechazó el acceso: {error}")

    code = _query_param("code")
    if not code:
        return None

    state = _query_param("state")
    if not verify_oauth_state(state):
        clear_oauth_query_params()
        raise ValueError(
            "La validación OAuth falló. Verifique que redirect_uri en secrets coincida "
            "exactamente con la URI autorizada en Google Cloud."
        )

    clear_oauth_query_params()

    profile = exchange_code_for_profile(code)
    from legal_ui.database import create_or_get_google_user, init_db

    init_db()
    user = create_or_get_google_user(
        profile["google_id"],
        profile["email"],
        profile["nombre"],
    )
    if not user.get("id"):
        raise ValueError("No se pudo registrar el usuario en la base de datos.")
    return user
