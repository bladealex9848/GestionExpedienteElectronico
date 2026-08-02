from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from legal_ui.despacho_store import DATA_DIR
from legal_ui.app_logging import get_logger

DB_PATH = DATA_DIR / "lexivox.db"
logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return secrets.compare_digest(actual, expected)


@contextmanager
def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'abogado',
                activo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS despacho_data (
                user_id TEXT PRIMARY KEY,
                store_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS expediente_files (
                user_id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                file_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                filename TEXT NOT NULL,
                content BLOB NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, case_id, file_id, kind)
            );
            """
        )
        _migrate_users(conn)


def _migrate_users(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "email" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "google_id" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id "
        "ON users(google_id) WHERE google_id IS NOT NULL"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email "
        "ON users(email) WHERE email IS NOT NULL"
    )


def user_count() -> int:
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(row["total"]) if row else 0


def create_user(username: str, password: str, nombre: str, rol: str = "abogado") -> dict:
    user_id = f"u{uuid4().hex[:10]}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO users (id, username, password_hash, nombre, rol, activo, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (user_id, username.strip().lower(), hash_password(password), nombre.strip(), rol, _now_iso()),
        )
    return get_user_by_id(user_id) or {}


def get_user_by_email(email: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? AND activo = 1",
            (email.strip().lower(),),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_google_id(google_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE google_id = ? AND activo = 1",
            (google_id.strip(),),
        ).fetchone()
    return dict(row) if row else None


def link_google_account(user_id: str, google_id: str, email: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE users SET google_id = ?, email = COALESCE(email, ?) WHERE id = ?",
            (google_id.strip(), email.strip().lower(), user_id),
        )


def _unique_username(base: str) -> str:
    candidate = base.strip().lower()
    if not candidate:
        candidate = f"user{uuid4().hex[:6]}"
    if not get_user_by_username(candidate):
        return candidate
    suffix = 2
    while get_user_by_username(f"{candidate}{suffix}"):
        suffix += 1
    return f"{candidate}{suffix}"


def create_or_get_google_user(google_id: str, email: str, nombre: str) -> dict:
    init_db()
    existing = get_user_by_google_id(google_id)
    if existing:
        return existing

    by_email = get_user_by_email(email)
    if by_email:
        link_google_account(by_email["id"], google_id, email)
        linked = get_user_by_id(by_email["id"])
        if linked:
            return linked
        return by_email

    username = _unique_username(email.split("@", 1)[0])
    user_id = f"u{uuid4().hex[:10]}"
    random_password = secrets.token_urlsafe(32)
    try:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO users
                (id, username, password_hash, nombre, rol, activo, created_at, email, google_id)
                VALUES (?, ?, ?, ?, 'abogado', 1, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    hash_password(random_password),
                    nombre.strip(),
                    _now_iso(),
                    email.strip().lower(),
                    google_id.strip(),
                ),
            )
    except sqlite3.IntegrityError as exc:
        existing = get_user_by_google_id(google_id) or get_user_by_email(email)
        if existing:
            return existing
        raise ValueError(f"No se pudo crear el usuario de Google: {exc}") from exc

    created = get_user_by_id(user_id)
    if not created:
        raise ValueError("El usuario de Google se insertó pero no pudo recuperarse de la base de datos.")
    return created


def get_user_by_username(username: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND activo = 1",
            (username.strip().lower(),),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, username, nombre, rol, activo, email, google_id, created_at "
            "FROM users ORDER BY username"
        ).fetchall()
    return [dict(row) for row in rows]


def authenticate(username: str, password: str) -> dict | None:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def update_password(user_id: str, new_password: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id),
        )


def load_store_json(user_id: str) -> str | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT store_json FROM despacho_data WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return row["store_json"] if row else None


def save_store_json(user_id: str, store_json: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO despacho_data (user_id, store_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                store_json = excluded.store_json,
                updated_at = excluded.updated_at
            """,
            (user_id, store_json, _now_iso()),
        )


def save_file_blob(
    user_id: str,
    case_id: str,
    file_id: str,
    kind: str,
    filename: str,
    content: bytes,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO expediente_files
            (user_id, case_id, file_id, kind, filename, content, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, case_id, file_id, kind) DO UPDATE SET
                filename = excluded.filename,
                content = excluded.content,
                updated_at = excluded.updated_at
            """,
            (user_id, case_id, file_id, kind, filename, content, _now_iso()),
        )


def read_file_blob(user_id: str, case_id: str, file_id: str, kind: str) -> bytes | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT content FROM expediente_files
            WHERE user_id = ? AND case_id = ? AND file_id = ? AND kind = ?
            """,
            (user_id, case_id, file_id, kind),
        ).fetchone()
    return row["content"] if row else None


def delete_file_blob(user_id: str, case_id: str, file_id: str, kind: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            DELETE FROM expediente_files
            WHERE user_id = ? AND case_id = ? AND file_id = ? AND kind = ?
            """,
            (user_id, case_id, file_id, kind),
        )


def export_database_bytes() -> bytes:
    if not DB_PATH.exists():
        init_db()
    return DB_PATH.read_bytes()


def auth_disabled() -> bool:
    if os.getenv("LEXIVOX_AUTH_DISABLED", "").strip().lower() in {"1", "true", "yes"}:
        return True
    try:
        import streamlit as st

        return bool(st.secrets.get("lexivox_auth", {}).get("disabled", False))
    except Exception:
        return False


def bootstrap_admin_from_secrets() -> None:
    if user_count() > 0:
        return
    username = os.getenv("LEXIVOX_ADMIN_USERNAME", "admin").strip() or "admin"
    password = os.getenv("LEXIVOX_ADMIN_PASSWORD", "").strip()
    nombre = os.getenv("LEXIVOX_ADMIN_NOMBRE", "Administrador").strip() or "Administrador"
    try:
        import streamlit as st

        cfg = st.secrets.get("lexivox_auth", {})
        username = str(cfg.get("admin_username", username))
        password = str(cfg.get("admin_password", password))
        nombre = str(cfg.get("admin_nombre", nombre))
    except Exception as exc:
        logger.debug("Secrets de admin no disponibles: %s", exc)

    if not password:
        password = "Lexivox2026!"
        logger.warning(
            "Contraseña admin por defecto en uso. Configure lexivox_auth.admin_password "
            "o LEXIVOX_ADMIN_PASSWORD antes de exponer la app a red."
        )
    create_user(username, password, nombre, rol="admin")
