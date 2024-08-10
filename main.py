import streamlit as st
import os
import pandas as pd
from index_generator import generate_index_from_scratch
from file_utils import rename_files
from excel_handler import save_excel_file
import base64
import zipfile
import tempfile

# Configuración de Streamlit
st.set_page_config(
    page_title="Sistema de Gestión de Expedientes Electrónicos Judiciales",
    page_icon="📄",
    initial_sidebar_state='expanded',
    menu_items={
        'Get Help': 'https://alexander.oviedo.isabellaea.com/',
        'Report a bug': 'https://github.com/bladealex9848/GestionExpedienteElectronico/issues',
        'About': "El Sistema de Gestión de Expedientes Electrónicos Judiciales es una herramienta para generar índices electrónicos de expedientes judiciales, cumpliendo con los estándares establecidos por el Consejo Superior de la Judicatura."
    }
)

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Descargar {file_label}</a>'
    return href

def create_zip_file(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), 
                           os.path.relpath(os.path.join(root, file), folder_path))

def main():
    # Sidebar
    st.sidebar.image("assets/logo.png", width=200)
    st.sidebar.title("Recursos Adicionales")
    st.sidebar.markdown(get_binary_file_downloader_html("assets/000IndiceElectronicoC0.xlsm", 'Plantilla Excel'), unsafe_allow_html=True)
    st.sidebar.markdown(get_binary_file_downloader_html("assets/guia_uso.pdf", 'Guía de Uso'), unsafe_allow_html=True)
    
    # Marco Normativo
    st.sidebar.title("Marco Normativo")
    marco_normativo_dir = "marco_normativo"
    for file in os.listdir(marco_normativo_dir):
        if file.endswith('.pdf'):
            st.sidebar.markdown(get_binary_file_downloader_html(os.path.join(marco_normativo_dir, file), file), unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.write("Desarrollado por Alexander Oviedo Fadul")
    st.sidebar.write("Consejo Seccional de la Judicatura de Sucre")
    st.sidebar.write("[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul-49434b9a/)")

    # Main content
    st.title("Sistema de Gestión de Expedientes Electrónicos Judiciales")
    
    st.write("""
    [![ver código fuente](https://img.shields.io/badge/Repositorio%20GitHub-gris?logo=github)](https://github.com/bladealex9848/GestionExpedienteElectronico)
    ![Visitantes](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgestionexpedienteelectronico.streamlit.app&label=Visitantes&labelColor=%235d5d5d&countColor=%231e7ebf&style=flat)
    """)

    st.write("Esta aplicación permite generar el índice electrónico de expedientes judiciales.")

    uploaded_files = st.file_uploader("Seleccione los archivos que contienen los documentos del expediente:", type=None, accept_multiple_files=True)

    if uploaded_files:
        with tempfile.TemporaryDirectory() as temp_folder:
            for uploaded_file in uploaded_files:
                with open(os.path.join(temp_folder, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            st.success("Archivos seleccionados correctamente.")
            
            if st.button("Generar Índice Electrónico"):
                progress_bar = st.progress(0)
                try:
                    rename_files(temp_folder)
                    progress_bar.progress(33)
                    
                    df = generate_index_from_scratch(temp_folder)
                    
                    progress_bar.progress(66)
                    
                    index_file_path = os.path.join(temp_folder, "000IndiceElectronicoC0.xlsx")
                    save_excel_file(df, index_file_path, use_template=False)
                    
                    zip_path = os.path.join(temp_folder, "expediente_con_indice.zip")
                    create_zip_file(temp_folder, zip_path)
                    
                    progress_bar.progress(100)
                    st.success("Índice electrónico generado con éxito.")
                    
                    st.markdown(get_binary_file_downloader_html(zip_path, 'Expediente con Índice (ZIP)'), unsafe_allow_html=True)
                
                except Exception as e:
                    st.error(f"Ocurrió un error: {str(e)}")

if __name__ == "__main__":
    main()