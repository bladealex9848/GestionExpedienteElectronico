import os
import re
from datetime import datetime
import string

def rename_files(folder_path):
    """
    Renombra los archivos en la carpeta según el protocolo, respetando los que ya tienen la estructura correcta.
    """
    files = [f for f in os.listdir(folder_path) 
             if os.path.isfile(os.path.join(folder_path, f)) 
             and not f.startswith('.') 
             and os.path.splitext(f)[1] != ''
             and f != '000IndiceElectronicoC0.xlsx']
    
    # Ordenar los archivos por fecha de modificación
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)))
    
    # Encontrar el número más alto de los archivos ya nombrados
    max_num = 0
    for filename in files:
        if re.match(r'^(\d{3})', filename):
            num = int(filename[:3])
            if num > max_num:
                max_num = num
    
    # Renombrar solo los archivos que no tienen el formato correcto
    for filename in files:
        if not re.match(r'^(\d{3})', filename):
            file_path = os.path.join(folder_path, filename)
            name, extension = os.path.splitext(filename)
            
            # Eliminar caracteres no alfanuméricos y espacios
            name = re.sub(r'[^a-zA-Z0-9 ]+', '', name)
            
            # Aplicar mayúscula a la primera letra de cada palabra
            name = string.capwords(name)
            
            # Eliminar espacios
            name = name.replace(" ", "")
            
            # Limitar a 36 caracteres
            name = name[:36]
            
            # Si está vacío, asignar "DocumentoElectronico"
            if not name:
                name = "DocumentoElectronico"
            
            # Incrementar el número y agregar al inicio
            max_num += 1
            new_name = f"{max_num:03d}{name}{extension}"
            
            new_path = os.path.join(folder_path, new_name)
            os.rename(file_path, new_path)

def get_file_metadata(file_path):
    """
    Obtiene los metadatos básicos de un archivo.
    """
    stat = os.stat(file_path)
    return {
        'creation_date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
        'modification_date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
        'size': format_file_size(stat.st_size),
        'extension': os.path.splitext(file_path)[1].lower()
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