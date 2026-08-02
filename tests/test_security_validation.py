"""Pruebas básicas de seguridad y validación de expedientes."""

from __future__ import annotations

import unittest

from legal_ui.database import hash_password, verify_password
from legal_ui.expediente_store import _validate_upload


class TestAuthSecurity(unittest.TestCase):
    def test_password_hash_roundtrip(self) -> None:
        stored = hash_password("contraseña-segura-123")
        self.assertTrue(verify_password("contraseña-segura-123", stored))
        self.assertFalse(verify_password("otra", stored))


class TestExpedienteValidation(unittest.TestCase):
    def test_reject_empty_file(self) -> None:
        with self.assertRaises(ValueError):
            _validate_upload("doc.pdf", b"")

    def test_reject_oversized_file(self) -> None:
        with self.assertRaises(ValueError):
            _validate_upload("doc.pdf", b"x" * (51 * 1024 * 1024))

    def test_reject_bad_extension(self) -> None:
        with self.assertRaises(ValueError):
            _validate_upload("malware.exe", b"data")


if __name__ == "__main__":
    unittest.main()
