"""Pruebas de comprobación de dependencias del sistema."""

from __future__ import annotations

import unittest

from legal_ui.system_deps import DependencyStatus, check_ocr_dependencies, check_poppler


class TestSystemDeps(unittest.TestCase):
    def test_check_poppler_returns_status(self) -> None:
        status = check_poppler()
        self.assertIsInstance(status, DependencyStatus)
        self.assertEqual(status.name, "Poppler")

    def test_check_ocr_dependencies_list(self) -> None:
        items = check_ocr_dependencies()
        self.assertEqual(len(items), 2)
        self.assertEqual({item.name for item in items}, {"Tesseract OCR", "Poppler"})


if __name__ == "__main__":
    unittest.main()
