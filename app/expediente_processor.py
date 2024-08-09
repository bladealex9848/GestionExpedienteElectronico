import os
from datetime import datetime
import pandas as pd
from file_utils import rename_files, get_file_metadata
from metadata_extractor import get_pdf_pages

class ExpedienteProcessor:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.files = []
        self.metadata = {}

    def process(self):
        self.rename_files()
        self.extract_metadata()
        return self.generate_dataframe()

    def rename_files(self):
        rename_files(self.folder_path)
        self.files = sorted(os.listdir(self.folder_path))

    def extract_metadata(self):
        for i, filename in enumerate(self.files, start=1):
            file_path = os.path.join(self.folder_path, filename)
            metadata = get_file_metadata(file_path)
            
            self.metadata[filename] = {
                'Nombre Documento': filename,
                'Fecha creación del documento': metadata['creation_date'],
                'Fecha Incorporación Expediente': datetime.now().strftime('%Y-%m-%d'),
                'Orden Documento': i,
                'Número de Páginas': get_pdf_pages(file_path) if metadata['extension'].lower() == '.pdf' else 1,
                'Formato': metadata['extension'][1:],
                'Tamaño': metadata['size'],
                'Origen': 'Digitalizado' if metadata['extension'].lower() == '.pdf' else 'Electrónico',
                'Observaciones': ''
            }

    def generate_dataframe(self):
        df = pd.DataFrame.from_dict(self.metadata, orient='index')
        df['Página Inicio'] = df['Número de Páginas'].cumsum() - df['Número de Páginas'] + 1
        df['Página Fin'] = df['Número de Páginas'].cumsum()
        return df

    def add_expediente_metadata(self, metadata):
        metadata_df = pd.DataFrame([metadata])
        return pd.concat([metadata_df, self.generate_dataframe()], ignore_index=True)

    def validate_metadata(self, metadata):
        required_fields = ['Ciudad', 'Despacho Judicial', 'Serie/Subserie documental', 
                           'Número de radicación del proceso', 'Partes procesales']
        for field in required_fields:
            if not metadata.get(field):
                raise ValueError(f"El campo '{field}' es obligatorio.")

    def process_with_metadata(self, metadata):
        self.validate_metadata(metadata)
        self.process()
        return self.add_expediente_metadata(metadata)