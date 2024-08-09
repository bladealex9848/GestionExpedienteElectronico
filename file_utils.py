import os
import re
from datetime import datetime
import string
import random

def rename_files(folder_path):
    """
    Renombra los archivos en la carpeta según el protocolo.
    """
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and not f.startswith('.') and os.path.splitext(f)[1] != '']
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)))
    
    for i, filename in enumerate(files, start=1):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            # Obtener nombre y extensión
            name, extension = os.path.splitext(filename)
            
            # Aplicar mayúscula a la primera letra de cada palabra
            name = string.capwords(name)
            
            # Eliminar caracteres no alfanuméricos
            name = re.sub(r'[^a-zA-Z0-9]+', '', name)
            
            # Eliminar números al inicio del nombre
            name = re.sub(r'^[0-9]+', '', name)
            
            # Limitar a 36 caracteres
            name = name[:36]
            
            # Si está vacío, asignar "DocumentoElectronico"
            if not name:
                name = "DocumentoElectronico"
            
            # Agregar número consecutivo al inicio
            new_name = f"{i:03d}{name}{extension}"
            
            new_path = os.path.join(folder_path, new_name)
            os.rename(file_path, new_path)

def get_file_metadata(file_path):
    """
    Obtiene los metadatos básicos de un archivo.
    """
    stat = os.stat(file_path)
    return {
        'creation_date': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d'),
        'modification_date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
        'size': format_file_size(stat.st_size),
        'extension': os.path.splitext(file_path)[1]
    }

def format_file_size(size):
    """
    Formatea el tamaño del archivo en una unidad legible.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0

def create_folder_structure(base_path):
    """
    Crea la estructura de carpetas para el expediente electrónico.
    """
    folders = [
        '01PrimeraInstancia',
        '02SegundaInstancia',
        '03RecursosExtraordinarios',
        '04Ejecucion'
    ]
    for folder in folders:
        os.makedirs(os.path.join(base_path, folder, 'C01'), exist_ok=True)

def get_folder_structure(base_path):
    """
    Obtiene la estructura de carpetas del expediente electrónico.
    """
    structure = {}
    for root, dirs, files in os.walk(base_path):
        level = root.replace(base_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        structure[os.path.basename(root)] = {
            'level': level,
            'indent': indent,
            'files': files
        }
    return structure

def generate_random_filename(length=10):
    """
    Genera un nombre de archivo aleatorio.
    """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))