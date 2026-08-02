"""Pruebas básicas de corrección de encoding en iLey CO."""

from __future__ import annotations

import unittest

from legal_ui.iley_service import _fix_encoding, _fix_mojibake_pairs


class TestIleyEncoding(unittest.TestCase):
    def test_fix_latin_mojibake(self) -> None:
        raw = "ConstituciÃ³n PolÃ­tica de la RepÃºblica"
        fixed = _fix_encoding(raw)
        self.assertIn("Constitución", fixed)
        self.assertIn("República", fixed)
        self.assertNotIn("Ã", fixed)

    def test_fix_pairs_in_mixed_line(self) -> None:
        line = "Las lenguas son tambiÃ©n oficiales y tradiciones lingÃ¼isticas"
        fixed = _fix_mojibake_pairs(line)
        self.assertIn("también", fixed)


if __name__ == "__main__":
    unittest.main()
