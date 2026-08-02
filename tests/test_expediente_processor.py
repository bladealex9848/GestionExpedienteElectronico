"""Pruebas del generador de índice SGDE (legacy)."""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from excel_handler import create_new_excel, fill_template_xlwings, save_excel_file
from file_utils import create_folder_structure, get_file_metadata, get_folder_structure, rename_files
from index_generator import generate_index_from_scratch, generate_index_from_template, update_metadata
from metadata_extractor import get_pdf_pages

try:
    import xlwings  # noqa: F401

    HAS_XLWINGS = True
except ImportError:
    HAS_XLWINGS = False

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
TEMPLATE_XLSM = os.path.join(ASSETS_DIR, "000IndiceElectronicoC0.xlsm")


class TestExpedienteProcessor(unittest.TestCase):
    test_dir: str

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.create_test_files()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_files(self) -> None:
        open(os.path.join(self.test_dir, "documento1.pdf"), "w", encoding="utf-8").close()
        open(os.path.join(self.test_dir, "documento2.docx"), "w", encoding="utf-8").close()
        open(os.path.join(self.test_dir, "imagen.jpg"), "w", encoding="utf-8").close()
        with open(os.path.join(self.test_dir, "documento_multipage.pdf"), "w", encoding="utf-8") as handle:
            handle.write("%PDF-1.5\n%%EOF\n")

    def test_rename_files(self) -> None:
        rename_files(self.test_dir)
        files = sorted(os.listdir(self.test_dir))
        self.assertEqual(len(files), 4)
        self.assertTrue(
            all(re.match(r"^\d{3}", name) for name in files),
            f"Se esperaba prefijo numérico de 3 dígitos: {files}",
        )

    def test_get_file_metadata(self) -> None:
        file_path = os.path.join(self.test_dir, "documento1.pdf")
        metadata = get_file_metadata(file_path)
        self.assertIn("creation_date", metadata)
        self.assertIn("size", metadata)
        self.assertEqual(metadata["extension"], ".pdf")

    def test_generate_index_from_scratch(self) -> None:
        df = generate_index_from_scratch(self.test_dir)
        self.assertEqual(len(df), 4)
        expected_columns = [
            "Nombre Documento",
            "Fecha Creación Documento",
            "Fecha Incorporación Expediente",
            "Orden Documento",
            "Número Páginas",
            "Página Inicio",
            "Página Fin",
            "Formato",
            "Tamaño",
            "Origen",
            "Observaciones",
        ]
        self.assertListEqual(list(df.columns), expected_columns)

    @unittest.skipUnless(os.path.isfile(TEMPLATE_XLSM), "Plantilla xlsm no encontrada en assets/")
    def test_generate_index_from_template(self) -> None:
        output_path = generate_index_from_template(self.test_dir, TEMPLATE_XLSM)
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(output_path.endswith(".xlsm"))

    def test_save_excel_file(self) -> None:
        df = generate_index_from_scratch(self.test_dir)
        output_path = os.path.join(self.test_dir, "test_index.xlsx")
        save_excel_file(df, output_path, use_template=False)
        self.assertTrue(os.path.exists(output_path))

    def test_create_folder_structure(self) -> None:
        create_folder_structure(self.test_dir)
        for folder in (
            "01PrimeraInstancia",
            "02SegundaInstancia",
            "03RecursosExtraordinarios",
            "04Ejecucion",
        ):
            self.assertTrue(os.path.isdir(os.path.join(self.test_dir, folder, "C01")))

    def test_get_folder_structure(self) -> None:
        create_folder_structure(self.test_dir)
        structure = get_folder_structure(self.test_dir)
        self.assertIn("01PrimeraInstancia", structure)
        self.assertIn("level", structure["01PrimeraInstancia"])

    def test_get_pdf_pages(self) -> None:
        file_path = os.path.join(self.test_dir, "documento_multipage.pdf")
        pages = get_pdf_pages(file_path)
        self.assertGreaterEqual(pages, 1)

    def test_update_metadata(self) -> None:
        df = generate_index_from_scratch(self.test_dir)
        metadata = {
            "Ciudad": "Bogotá",
            "Despacho Judicial": "Juzgado 1 Civil del Circuito",
            "Serie o Subserie documental": "Expedientes de Procesos Judiciales",
        }
        updated_df = update_metadata(df, metadata)
        self.assertEqual(updated_df.iloc[0]["Ciudad"], "Bogotá")

    def test_create_new_excel(self) -> None:
        df = generate_index_from_scratch(self.test_dir)
        wb = create_new_excel(df)
        self.assertIsNotNone(wb)
        self.assertIn("Índice Electrónico", wb.sheetnames)

    @unittest.skipUnless(HAS_XLWINGS, "xlwings no instalado (solo desktop)")
    @unittest.skipUnless(os.path.isfile(TEMPLATE_XLSM), "Plantilla xlsm no encontrada")
    def test_fill_template_xlwings(self) -> None:
        df = generate_index_from_scratch(self.test_dir)
        output_path = os.path.join(self.test_dir, "filled_template.xlsm")
        fill_template_xlwings(df, output_path)
        self.assertTrue(os.path.exists(output_path))


if __name__ == "__main__":
    unittest.main()
