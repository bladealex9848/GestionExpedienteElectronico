import unittest
import os
import shutil
import tempfile
from index_generator import generate_index_from_scratch, generate_index_from_template
from file_utils import rename_files
from metadata_extractor import get_file_metadata

class TestExpedienteProcessor(unittest.TestCase):

    def setUp(self):
        # Crear un directorio temporal para las pruebas
        self.test_dir = tempfile.mkdtemp()
        
        # Crear algunos archivos de prueba
        self.create_test_files()

    def tearDown(self):
        # Eliminar el directorio temporal después de las pruebas
        shutil.rmtree(self.test_dir)

    def create_test_files(self):
        # Crear archivos de prueba con diferentes extensiones
        open(os.path.join(self.test_dir, "documento1.pdf"), "w").close()
        open(os.path.join(self.test_dir, "documento2.docx"), "w").close()
        open(os.path.join(self.test_dir, "imagen.jpg"), "w").close()

    def test_rename_files(self):
        rename_files(self.test_dir)
        files = os.listdir(self.test_dir)
        self.assertEqual(len(files), 3)
        self.assertTrue(any(file.startswith("001") for file in files))
        self.assertTrue(any(file.startswith("002") for file in files))
        self.assertTrue(any(file.startswith("003") for file in files))

    def test_get_file_metadata(self):
        file_path = os.path.join(self.test_dir, "documento1.pdf")
        metadata = get_file_metadata(file_path)
        self.assertIn('creation_date', metadata)
        self.assertIn('size', metadata)
        self.assertIn('extension', metadata)
        self.assertEqual(metadata['extension'], '.pdf')

    def test_generate_index_from_scratch(self):
        df = generate_index_from_scratch(self.test_dir)
        self.assertEqual(len(df), 3)
        self.assertListEqual(list(df.columns), [
            'Nombre Documento', 'Fecha Creación Documento', 
            'Fecha Incorporación Expediente', 'Orden Documento',
            'Número Páginas', 'Página Inicio', 'Página Fin',
            'Formato', 'Tamaño', 'Origen', 'Observaciones'
        ])

    def test_generate_index_from_template(self):
        template_path = os.path.join(os.path.dirname(__file__), '..', 'assets', '000IndiceElectronicoC0.xlsm')
        df = generate_index_from_template(self.test_dir, template_path)
        self.assertGreater(len(df), 0)
        self.assertIn('Nombre Documento', df.columns)
        self.assertIn('Fecha Creación Documento', df.columns)

if __name__ == '__main__':
    unittest.main()