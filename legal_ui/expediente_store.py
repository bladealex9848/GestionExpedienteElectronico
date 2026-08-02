from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from legal_ui.auth import get_current_user_id, use_database_storage
from legal_ui.despacho_store import DATA_DIR, new_id

EXPEDIENTES_DIR = DATA_DIR / "expedientes"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB por archivo
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".md", ".json", ".zip",
}


def _validate_upload(filename: str, content: bytes) -> None:
    if not filename or not filename.strip():
        raise ValueError("El nombre del archivo está vacío.")
    if not content:
        raise ValueError("El archivo está vacío.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"El archivo supera el límite de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )
    suffix = Path(filename).suffix.lower()
    if suffix and suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extensión no permitida: {suffix}")


def _sanitize_filename(name: str) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_") or "documento"
    return f"{safe}{suffix}"


def case_root(case_id: str) -> Path:
    root = EXPEDIENTES_DIR / case_id
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "resultados").mkdir(parents=True, exist_ok=True)
    return root


def _persist_bytes(case_id: str, file_id: str, kind: str, filename: str, content: bytes) -> None:
    user_id = get_current_user_id()
    if use_database_storage() and user_id:
        from legal_ui.database import save_file_blob

        save_file_blob(user_id, case_id, file_id, kind, filename, content)
        return
    folder = "docs" if kind == "doc" else "resultados"
    dest = case_root(case_id) / folder / filename
    dest.write_bytes(content)


def _load_bytes(case_id: str, file_id: str, kind: str, filename: str) -> bytes:
    user_id = get_current_user_id()
    if use_database_storage() and user_id:
        from legal_ui.database import read_file_blob

        content = read_file_blob(user_id, case_id, file_id, kind)
        if content is not None:
            return content
    folder = "docs" if kind == "doc" else "resultados"
    return (case_root(case_id) / folder / filename).read_bytes()


def _delete_bytes(case_id: str, file_id: str, kind: str, filename: str) -> None:
    user_id = get_current_user_id()
    if use_database_storage() and user_id:
        from legal_ui.database import delete_file_blob

        delete_file_blob(user_id, case_id, file_id, kind)
    folder = "docs" if kind == "doc" else "resultados"
    path = case_root(case_id) / folder / filename
    if path.exists():
        path.unlink()


def save_document(case: dict, filename: str, content: bytes, categoria: str = "") -> dict:
    _validate_upload(filename, content)
    case_id = case["id"]
    safe_name = _sanitize_filename(filename)
    counter = 1
    while any(doc.get("archivo") == safe_name for doc in case.get("documentos", [])):
        safe_name = _sanitize_filename(f"{Path(filename).stem}_{counter}{Path(filename).suffix}")
        counter += 1

    meta = {
        "id": new_id("doc"),
        "nombre": filename,
        "archivo": safe_name,
        "tipo": Path(filename).suffix.lower().lstrip("."),
        "categoria": categoria.strip(),
        "subido": datetime.now().isoformat(timespec="seconds"),
        "tamano": len(content),
    }
    _persist_bytes(case_id, meta["id"], "doc", safe_name, content)
    case.setdefault("documentos", []).append(meta)
    return meta


def read_document_bytes(case_id: str, doc_meta: dict) -> bytes:
    return _load_bytes(case_id, doc_meta["id"], "doc", doc_meta["archivo"])


def delete_document(case: dict, doc_id: str) -> None:
    case_id = case["id"]
    docs = case.get("documentos", [])
    target = next((doc for doc in docs if doc.get("id") == doc_id), None)
    if not target:
        return
    _delete_bytes(case_id, target["id"], "doc", target["archivo"])
    case["documentos"] = [doc for doc in docs if doc.get("id") != doc_id]


def save_result(
    case: dict,
    herramienta: str,
    titulo: str,
    filename: str,
    content: bytes,
    notas: str = "",
) -> dict:
    _validate_upload(filename, content)
    case_id = case["id"]
    safe_name = _sanitize_filename(filename)
    counter = 1
    while any(row.get("archivo") == safe_name for row in case.get("resultados", [])):
        safe_name = _sanitize_filename(f"{Path(filename).stem}_{counter}{Path(filename).suffix}")
        counter += 1

    meta = {
        "id": new_id("res"),
        "herramienta": herramienta,
        "titulo": titulo.strip() or filename,
        "archivo": safe_name,
        "tipo": Path(filename).suffix.lower().lstrip("."),
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "tamano": len(content),
        "notas": notas.strip(),
    }
    _persist_bytes(case_id, meta["id"], "result", safe_name, content)
    case.setdefault("resultados", []).append(meta)
    return meta


def read_result_bytes(case_id: str, result_meta: dict) -> bytes:
    return _load_bytes(case_id, result_meta["id"], "result", result_meta["archivo"])


def delete_result(case: dict, result_id: str) -> None:
    case_id = case["id"]
    results = case.get("resultados", [])
    target = next((row for row in results if row.get("id") == result_id), None)
    if not target:
        return
    _delete_bytes(case_id, target["id"], "result", target["archivo"])
    case["resultados"] = [row for row in results if row.get("id") != result_id]
