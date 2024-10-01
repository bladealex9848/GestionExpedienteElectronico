import unittest
import os
import shutil
import tempfile
import sys
import pandas as pd
from datetime import datetime

# Añadir el directorio raíz del proyecto al path para poder importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from index_generator import generate_index_from_scratch, generate_index_from_template, update_metadata
from file_utils import rename_files, get_file_metadata, create_folder_structure, get_folder_structure
from metadata_extractor import get_pdf_pages
from excel_handler import save_excel_file, create_new_excel, fill_template_xlwings

class TestExpedienteProcessor(unittest.TestCase):

    def setUp(self):
        try:
            # Crear un directorio temporal para las pruebas
            self.test_dir = tempfile.mkdtemp()
            
            # Crear algunos archivos de prueba
            self.create_test_files()
        except Exception as e:
            self.fail(f"Error en setUp: {str(e)}")

    def tearDown(self):
        try:
            # Eliminar el directorio temporal después de las pruebas
            shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Error en tearDown: {str(e)}")

    def create_test_files(self):
        try:
            # Crear archivos de prueba con diferentes extensiones
            open(os.path.join(self.test_dir, "documento1.pdf"), "w").close()
            open(os.path.join(self.test_dir, "documento2.docx"), "w").close()
            open(os.path.join(self.test_dir, "imagen.jpg"), "w").close()
            # Crear un archivo PDF más realista
            with open(os.path.join(self.test_dir, "documento_multipage.pdf"), "w") as f:
                f.write("%PDF-1.5\n%EOF\n")  # Contenido mínimo para simular un PDF
        except Exception as e:
            self.fail(f"Error al crear archivos de prueba: {str(e)}")

    def test_rename_files(self):
        try:
            rename_files(self.test_dir)
            files = os.listdir(self.test_dir)
            self.assertEqual(len(files), 4, "El número de archivos renombrados no coincide")
            self.assertTrue(any(file.startswith("01") for file in files), "No se encontró archivo con prefijo 01")
            self.assertTrue(any(file.startswith("02") for file in files), "No se encontró archivo con prefijo 02")
            self.assertTrue(any(file.startswith("03") for file in files), "No se encontró archivo con prefijo 03")
            self.assertTrue(any(file.startswith("04") for file in files), "No se encontró archivo con prefijo 04")
        except Exception as e:
            self.fail(f"Error en test_rename_files: {str(e)}")

    def test_get_file_metadata(self):
        try:
            file_path = os.path.join(self.test_dir, "documento1.pdf")
            metadata = get_file_metadata(file_path)
            self.assertIn('creation_date', metadata, "No se encontró la fecha de creación en los metadatos")
            self.assertIn('size', metadata, "No se encontró el tamaño en los metadatos")
            self.assertIn('extension', metadata, "No se encontró la extensión en los metadatos")
            self.assertEqual(metadata['extension'], '.pdf', "La extensión del archivo no coincide")
        except Exception as e:
            self.fail(f"Error en test_get_file_metadata: {str(e)}")

    def test_generate_index_from_scratch(self):
        try:
            df = generate_index_from_scratch(self.test_dir)
            self.assertEqual(len(df), 4, "El número de filas en el índice no coincide con el número de archivos")
            expected_columns = [
                'Nombre Documento', 'Fecha Creación Documento', 
                'Fecha Incorporación Expediente', 'Orden Documento',
                'Número Páginas', 'Página Inicio', 'Página Fin',
                'Formato', 'Tamaño', 'Origen', 'Observaciones'
            ]
            self.assertListEqual(list(df.columns), expected_columns, "Las columnas del índice no coinciden con las esperadas")
        except Exception as e:
            self.fail(f"Error en test_generate_index_from_scratch: {str(e)}")

    def test_generate_index_from_template(self):
        try:
            template_path = os.path.join(os.path.dirname(__file__), '..', 'assets', '000IndiceElectronicoC0.xlsm')
            output_path = generate_index_from_template(self.test_dir, template_path)
            self.assertTrue(os.path.exists(output_path), "No se generó el archivo de índice")
            self.assertTrue(output_path.endswith('.xlsm'), "El archivo generado no tiene la extensión .xlsm")
        except Exception as e:
            self.fail(f"Error en test_generate_index_from_template: {str(e)}")

    def test_save_excel_file(self):
        try:
            df = generate_index_from_scratch(self.test_dir)
            output_path = os.path.join(self.test_dir, "test_index.xlsx")
            save_excel_file(df, output_path, use_template=False)
            self.assertTrue(os.path.exists(output_path), "No se guardó el archivo Excel")
        except Exception as e:
            self.fail(f"Error en test_save_excel_file: {str(e)}")

    def test_create_folder_structure(self):
        try:
            create_folder_structure(self.test_dir)
            expected_folders = ['01PrimeraInstancia', '02SegundaInstancia', '03RecursosExtraordinarios', '04Ejecucion']
            for folder in expected_folders:
                self.assertTrue(os.path.exists(os.path.join(self.test_dir, folder)), f"No se creó la carpeta {folder}")
                self.assertTrue(os.path.exists(os.path.join(self.test_dir, folder, 'C01')), f"No se creó la subcarpeta C01 en {folder}")
        except Exception as e:
            self.fail(f"Error en test_create_folder_structure: {str(e)}")

    def test_get_folder_structure(self):
        try:
            create_folder_structure(self.test_dir)
            structure = get_folder_structure(self.test_dir)
            self.assertIn('01PrimeraInstancia', structure, "No se encontró la carpeta 01PrimeraInstancia en la estructura")
            self.assertIn('level', structure['01PrimeraInstancia'], "La estructura no contiene el nivel de la carpeta")
            self.assertIn('indent', structure['01PrimeraInstancia'], "La estructura no contiene la indentación de la carpeta")
            self.assertIn('files', structure['01PrimeraInstancia'], "La estructura no contiene la lista de archivos de la carpeta")
        except Exception as e:
            self.fail(f"Error en test_get_folder_structure: {str(e)}")

    def test_get_pdf_pages(self):
        try:
            file_path = os.path.join(self.test_dir, "documento_multipage.pdf")
            pages = get_pdf_pages(file_path)
            self.assertEqual(pages, 1, "El número de páginas del PDF no es el esperado")
        except Exception as e:
            self.fail(f"Error en test_get_pdf_pages: {str(e)}")

    def test_update_metadata(self):
        try:
            df = generate_index_from_scratch(self.test_dir)
            metadata = {
                'Ciudad': 'Bogotá',
                'Despacho Judicial': 'Juzgado 1 Civil del Circuito',
                'Serie o Subserie documental': 'Expedientes de Procesos Judiciales'
            }
            updated_df = update_metadata(df, metadata)
            self.assertEqual(updated_df.iloc[0]['Ciudad'], 'Bogotá', "No se actualizó correctamente el metadato de Ciudad")
            self.assertEqual(updated_df.iloc[0]['Despacho Judicial'], 'Juzgado 1 Civil del Circuito', "No se actualizó correctamente el metadato de Despacho Judicial")
        except Exception as e:
            self.fail(f"Error en test_update_metadata: {str(e)}")

    def test_create_new_excel(self):
        try:
            df = generate_index_from_scratch(self.test_dir)
            wb = create_new_excel(df)
            self.assertIsNotNone(wb, "No se creó el libro de Excel")
            self.assertIn('Índice Electrónico', wb.sheetnames, "No se creó la hoja 'Índice Electrónico' en el libro de Excel")
        except Exception as e:
            self.fail(f"Error en test_create_new_excel: {str(e)}")

    def test_fill_template_xlwings(self):
        try:
            df = generate_index_from_scratch(self.test_dir)
            template_path = os.path.join(os.path.dirname(__file__), '..', 'assets', '00IndiceElectronicoC0.xlsm')
            output_path = os.path.join(self.test_dir, "filled_template.xlsm")
            fill_template_xlwings(df, output_path)
            self.assertTrue(os.path.exists(output_path), "No se generó el archivo de plantilla llenado")
        except Exception as e:
            self.fail(f"Error en test_fill_template_xlwings: {str(e)}")

if __name__ == '__main__':
    unittest.main()