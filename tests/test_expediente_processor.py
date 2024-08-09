import unittest
import os
import shutil
import tempfile
from expediente_processor import ExpedienteProcessor
from file_utils import rename_files, get_file_metadata
from metadata_extractor import get_pdf_pages

class TestExpedienteProcessor(unittest.TestCase):

    def setUp(self):
        # Crear un directorio temporal para las pruebas
        self.test_dir = tempfile.mkdtemp()
        
        # Crear algunos archivos de prueba
        self.create_test_files()
        
        # Inicializar el procesador
        self.processor = ExpedienteProcessor(self.test_dir)

    def tearDown(self):
        # Eliminar el directorio temporal después de las pruebas
        shutil.rmtree(self.test_dir)

    def create_test_files(self):
        # Crear archivos de prueba con diferentes extensiones
        open(os.path.join(self.test_dir, "documento1.pdf"), "w").close()
        open(os.path.join(self.test_dir, "documento2.docx"), "w").close()
        open(os.path.join(self.test_dir, "imagen.jpg"), "w").close()

    def test_rename_files(self):
        self.processor.rename_files()
        files = os.listdir(self.test_dir)
        self.assertEqual(len(files), 3)
        self.assertTrue(any(file.startswith("001") for file in files))
        self.assertTrue(any(file.startswith("002") for file in files))
        self.assertTrue(any(file.startswith("003") for file in files))

    def test_extract_metadata(self):
        self.processor.rename_files()
        self.processor.extract_metadata()
        self.assertEqual(len(self.processor.metadata), 3)
        for metadata in self.processor.metadata.values():
            self.assertIn('Nombre Documento', metadata)
            self.assertIn('Fecha creación del documento', metadata)
            self.assertIn('Fecha Incorporación Expediente', metadata)
            self.assertIn('Orden Documento', metadata)
            self.assertIn('Número de Páginas', metadata)
            self.assertIn('Formato', metadata)
            self.assertIn('Tamaño', metadata)
            self.assertIn('Origen', metadata)

    def test_generate_dataframe(self):
        self.processor.rename_files()
        self.processor.extract_metadata()
        df = self.processor.generate_dataframe()
        self.assertEqual(len(df), 3)
        self.assertListEqual(list(df.columns), [
            'Nombre Documento', 'Fecha creación del documento', 
            'Fecha Incorporación Expediente', 'Orden Documento',
            'Número de Páginas', 'Página Inicio', 'Página Fin',
            'Formato', 'Tamaño', 'Origen', 'Observaciones'
        ])

    def test_add_expediente_metadata(self):
        metadata = {
            'Ciudad': 'Bogotá',
            'Despacho Judicial': 'Juzgado 1 Civil del Circuito',
            'Serie/Subserie documental': 'Procesos Declarativos',
            'Número de radicación del proceso': '2021-00123',
            'Partes procesales': 'Demandante: Juan Pérez, Demandado: Empresa XYZ'
        }
        self.processor.rename_files()
        self.processor.extract_metadata()
        df = self.processor.add_expediente_metadata(metadata)
        self.assertEqual(len(df), 4)  # 3 archivos + 1 fila de metadatos
        self.assertEqual(df.iloc[0]['Ciudad'], 'Bogotá')

    def test_validate_metadata(self):
        valid_metadata = {
            'Ciudad': 'Bogotá',
            'Despacho Judicial': 'Juzgado 1 Civil del Circuito',
            'Serie/Subserie documental': 'Procesos Declarativos',
            'Número de radicación del proceso': '2021-00123',
            'Partes procesales': 'Demandante: Juan Pérez, Demandado: Empresa XYZ'
        }
        self.processor.validate_metadata(valid_metadata)  # No debería lanzar excepción

        invalid_metadata = {
            'Ciudad': 'Bogotá',
            'Despacho Judicial': 'Juzgado 1 Civil del Circuito'
            # Faltan campos obligatorios
        }
        with self.assertRaises(ValueError):
            self.processor.validate_metadata(invalid_metadata)

    def test_process_with_metadata(self):
        metadata = {
            'Ciudad': 'Bogotá',
            'Despacho Judicial': 'Juzgado 1 Civil del Circuito',
            'Serie/Subserie documental': 'Procesos Declarativos',
            'Número de radicación del proceso': '2021-00123',
            'Partes procesales': 'Demandante: Juan Pérez, Demandado: Empresa XYZ'
        }
        df = self.processor.process_with_metadata(metadata)
        self.assertEqual(len(df), 4)  # 3 archivos + 1 fila de metadatos
        self.assertEqual(df.iloc[0]['Ciudad'], 'Bogotá')
        self.assertEqual(len(df.iloc[1:]), 3)  # Verificar que se procesaron los 3 archivos

if __name__ == '__main__':
    unittest.main()