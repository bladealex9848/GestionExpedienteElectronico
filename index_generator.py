import os
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from metadata_extractor import get_file_metadata, get_pdf_pages
import xlwings as xw
import re

def generate_index_from_scratch(folder_path):
    """
    Genera el índice electrónico desde cero.
    """
    files = [f for f in os.listdir(folder_path) 
             if os.path.isfile(os.path.join(folder_path, f))
             and not f.startswith('.') # Ignorar archivos ocultos
             and os.path.splitext(f)[1] != '' # Ignorar archivos sin extensión
             and not ('IndiceElectronico' in f and f.endswith(('.xlsx', '.xlsm')))] # Ignorar archivos de índice
    
    # Ordenar los archivos por fecha de modificación (más antiguo primero)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)))

    data = []
    current_page = 1

    for i, filename in enumerate(files, start=1):
        file_path = os.path.join(folder_path, filename)
        metadata = get_file_metadata(file_path)
        
        num_pages = get_pdf_pages(file_path) if metadata['extension'].lower() == '.pdf' else 1
        
        # Eliminar los tres dígitos iniciales y la extensión para el nombre del documento
        doc_name = re.sub(r'^\d+', '', os.path.splitext(filename)[0])
        
        data.append({
            'Nombre Documento': doc_name,
            'Fecha Creación Documento': metadata['modification_date'],
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
    Genera el índice electrónico usando la plantilla proporcionada con macros.
    """
    # Generar el índice
    df = generate_index_from_scratch(folder_path)

    try:
        # Usar xlwings para manejar el archivo con macros
        with xw.App(visible=False) as app:
            wb = app.books.open(template_path)
            ws = wb.sheets[0]
            
            # Llenar la plantilla con los datos del DataFrame
            for _ in range(len(df)):
                # Ejecutar la macro para insertar una nueva fila
                wb.macro("Macro1InsertarFila")
            
            # Llenar los datos
            start_row = 12  # Asumiendo que los datos comienzan en la fila 12
            for i, row in df.iterrows():
                for j, value in enumerate(row, start=1):
                    ws.cells(start_row + i, j).value = value
            
            # Guardar y cerrar
            output_path = os.path.join(folder_path, "000IndiceElectronicoC0.xlsm")
            wb.save(output_path)
            wb.close()
        
        return output_path

    except Exception as e:
        print(f"Error al usar xlwings: {str(e)}")
        print("Intentando con openpyxl (sin macros)...")

        # Si xlwings falla, usar openpyxl como alternativa (sin macros)
        wb = load_workbook(template_path, keep_vba=True)
        ws = wb.active

        # Insertar filas necesarias
        ws.insert_rows(12, amount=len(df))

        # Llenar la plantilla con los datos del DataFrame
        for r, row in enumerate(df.itertuples(index=False), start=12):
            for c, value in enumerate(row, start=1):
                ws.cell(row=r, column=c, value=value)

        # Guardar el archivo
        output_path = os.path.join(folder_path, "000IndiceElectronicoC0.xlsm")
        wb.save(output_path)

        return output_path

def update_metadata(df, metadata):
    """
    Actualiza los metadatos del expediente en el DataFrame.
    """
    metadata_row = pd.DataFrame([metadata])
    return pd.concat([metadata_row, df]).reset_index(drop=True)