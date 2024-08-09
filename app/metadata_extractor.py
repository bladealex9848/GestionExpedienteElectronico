import os
import PyPDF2
import docx
import openpyxl
from PIL import Image
import magic

def get_pdf_pages(file_path):
    """
    Obtiene el número de páginas de un archivo PDF.
    """
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages)
    except:
        return 1  # Si no es un PDF o hay un error, asumimos 1 página

def get_word_pages(file_path):
    """
    Obtiene el número de páginas de un archivo Word.
    """
    try:
        doc = docx.Document(file_path)
        return len(doc.sections)
    except:
        return 1  # Si hay un error, asumimos 1 página

def get_excel_sheets(file_path):
    """
    Obtiene el número de hojas de un archivo Excel.
    """
    try:
        workbook = openpyxl.load_workbook(file_path, read_only=True)
        return len(workbook.sheetnames)
    except:
        return 1  # Si hay un error, asumimos 1 hoja

def get_image_info(file_path):
    """
    Obtiene información de una imagen.
    """
    try:
        with Image.open(file_path) as img:
            return {
                'format': img.format,
                'size': img.size,
                'mode': img.mode
            }
    except:
        return None

def get_file_type(file_path):
    """
    Obtiene el tipo MIME del archivo.
    """
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)

def extract_metadata(file_path):
    """
    Extrae metadatos de un archivo basado en su tipo.
    """
    file_type = get_file_type(file_path)
    metadata = {
        'file_type': file_type,
        'size': os.path.getsize(file_path),
        'creation_date': os.path.getctime(file_path),
        'modification_date': os.path.getmtime(file_path)
    }

    if file_type.startswith('application/pdf'):
        metadata['pages'] = get_pdf_pages(file_path)
    elif file_type.startswith('application/vnd.openxmlformats-officedocument.wordprocessingml'):
        metadata['pages'] = get_word_pages(file_path)
    elif file_type.startswith('application/vnd.openxmlformats-officedocument.spreadsheetml'):
        metadata['sheets'] = get_excel_sheets(file_path)
    elif file_type.startswith('image'):
        metadata['image_info'] = get_image_info(file_path)

    return metadata

def is_document_digitalized(file_path):
    """
    Determina si un documento es digitalizado o nativo electrónico.
    """
    file_type = get_file_type(file_path)
    if file_type.startswith('application/pdf'):
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if '/Producer' in pdf_reader.metadata:
                    return 'scan' in pdf_reader.metadata['/Producer'].lower()
        except:
            pass
    return False  # Si no es un PDF o no se puede determinar, asumimos que es nativo electrónico

def get_document_origin(file_path):
    """
    Determina el origen del documento (Electrónico o Digitalizado).
    """
    return 'Digitalizado' if is_document_digitalized(file_path) else 'Electrónico'