import os
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from metadata_extractor import get_file_metadata, get_pdf_pages

def generate_index_from_scratch(folder_path):
    """
    Genera el índice electrónico desde cero.
    """
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)))

    data = []
    current_page = 1

    for i, filename in enumerate(files, start=1):
        file_path = os.path.join(folder_path, filename)
        metadata = get_file_metadata(file_path)
        
        num_pages = get_pdf_pages(file_path) if metadata['extension'].lower() == '.pdf' else 1
        
        data.append({
            'Nombre Documento': filename,
            'Fecha Creación Documento': metadata['creation_date'],
            'Fecha Incorporación Expediente': datetime.now().strftime('%Y-%m-%d'),
            'Orden Documento': i,
            'Número Páginas': num_pages,
            'Página Inicio': current_page,
            'Página Fin': current_page + num_pages - 1,
            'Formato': metadata['extension'][1:],
            'Tamaño': metadata['size'],
            'Origen': 'Digitalizado' if metadata['extension'].lower() == '.pdf' else 'Electrónico',
            'Observaciones': ''
        })
        current_page += num_pages

    df = pd.DataFrame(data)
    return df

def generate_index_from_template(folder_path, template_path):
    """
    Genera el índice electrónico usando la plantilla proporcionada.
    """
    # Cargar la plantilla
    wb = load_workbook(template_path)
    ws = wb.active

    # Generar el índice
    df = generate_index_from_scratch(folder_path)

    # Llenar la plantilla con los datos del DataFrame
    for r in range(12, 12 + len(df)):
        ws.cell(row=r, column=1, value=df.iloc[r-12]['Nombre Documento'])
        ws.cell(row=r, column=2, value=df.iloc[r-12]['Fecha Creación Documento'])
        ws.cell(row=r, column=3, value=df.iloc[r-12]['Fecha Incorporación Expediente'])
        ws.cell(row=r, column=4, value=df.iloc[r-12]['Orden Documento'])
        ws.cell(row=r, column=5, value=df.iloc[r-12]['Número Páginas'])
        ws.cell(row=r, column=6, value=df.iloc[r-12]['Página Inicio'])
        ws.cell(row=r, column=7, value=df.iloc[r-12]['Página Fin'])
        ws.cell(row=r, column=8, value=df.iloc[r-12]['Formato'])
        ws.cell(row=r, column=9, value=df.iloc[r-12]['Tamaño'])
        ws.cell(row=r, column=10, value=df.iloc[r-12]['Origen'])
        ws.cell(row=r, column=11, value=df.iloc[r-12]['Observaciones'])

    # Convertir el workbook de vuelta a un DataFrame
    data = ws.values
    cols = next(data)[1:]
    data = list(data)
    df = pd.DataFrame(data, columns=cols)

    return df

def update_metadata(df, metadata):
    """
    Actualiza los metadatos del expediente en el DataFrame.
    """
    metadata_row = pd.DataFrame([metadata])
    return pd.concat([metadata_row, df]).reset_index(drop=True)