import streamlit as st
import os
import pandas as pd
from index_generator import generate_index_from_scratch, generate_index_from_template
from file_utils import rename_files
from excel_handler import save_excel_file
import base64

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Descargar {file_label}</a>'
    return href

def main():
    st.set_page_config(page_title="Sistema de Gestión de Expedientes Electrónicos Judiciales", layout="wide")
    
    st.title("Sistema de Gestión de Expedientes Electrónicos Judiciales")
    
    st.write("Esta aplicación permite generar el índice electrónico de expedientes judiciales.")

    uploaded_files = st.file_uploader("Seleccione los archivos que contienen los documentos del expediente:", type=None, accept_multiple_files=True)

    if uploaded_files:
        # Crear una carpeta temporal para almacenar los archivos subidos
        temp_folder = "temp_expediente"
        os.makedirs(temp_folder, exist_ok=True)
        
        for uploaded_file in uploaded_files:
            with open(os.path.join(temp_folder, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        folder_path = temp_folder
        st.success("Archivos seleccionados correctamente.")
        
        index_method = st.radio(
            "Seleccione el método para generar el índice:",
            ("Generar desde cero", "Usar plantilla")
        )
        
        if st.button("Generar Índice Electrónico"):
            with st.spinner("Generando índice electrónico..."):
                try:
                    # Renombrar archivos
                    rename_files(folder_path)
                    
                    # Generar índice
                    if index_method == "Generar desde cero":
                        df = generate_index_from_scratch(folder_path)
                    else:
                        template_path = os.path.join(os.path.dirname(__file__), 'assets', '000IndiceElectronicoC0.xlsm')
                        df = generate_index_from_template(folder_path, template_path)
                    
                    # Guardar el archivo Excel
                    index_file_path = os.path.join(folder_path, "000IndiceElectronicoC0.xlsx")
                    save_excel_file(df, index_file_path, index_method == "Usar plantilla")
                    
                    st.success("Índice electrónico generado con éxito.")
                    
                    # Proporcionar enlace de descarga
                    st.markdown(get_binary_file_downloader_html(index_file_path, 'Índice Electrónico'), unsafe_allow_html=True)
                
                except Exception as e:
                    st.error(f"Ocurrió un error: {str(e)}")
    else:
        st.info("Por favor, seleccione los archivos que contienen los documentos del expediente.")

    st.markdown("---")
    st.write("Desarrollado por Alexander Oviedo Fadul")
    st.write("Consejo Seccional de la Judicatura de Sucre")
    st.write("[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [LinkedIn](https://www.linkedin.com/in/alexanderoviedo/)")

if __name__ == "__main__":
    main()