import streamlit as st
import os
import pandas as pd
from datetime import datetime
import PyPDF2
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Border, Side
import io
import base64
from file_utils import rename_files, get_file_metadata
from metadata_extractor import get_pdf_pages
from index_generator import generate_index, generate_excel, generate_pdf
from gui import create_info_table, show_instructions

def main():
    st.set_page_config(page_title="Sistema de Gestión de Expedientes Electrónicos Judiciales", layout="wide")
    
    create_info_table()
    
    st.title("Sistema de Gestión de Expedientes Electrónicos Judiciales")
    
    show_instructions()

    if 'folder_path' not in st.session_state:
        st.session_state.folder_path = ""

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
        
        st.subheader("Metadatos del Expediente")
        ciudad = st.text_input("Ciudad:")
        despacho_judicial = st.text_input("Despacho Judicial:")
        serie_subserie = st.text_input("Serie/Subserie documental:")
        num_radicacion = st.text_input("Número de radicación del proceso:")
        partes_procesales = st.text_area("Partes procesales:")
        
        if st.button("Generar Índice Electrónico"):
            if ciudad and despacho_judicial and serie_subserie and num_radicacion and partes_procesales:
                with st.spinner("Generando índice electrónico..."):
                    # Renombrar archivos
                    rename_files(folder_path)
                    
                    # Generar índice
                    metadata = {
                        'Ciudad': ciudad,
                        'Despacho Judicial': despacho_judicial,
                        'Serie/Subserie documental': serie_subserie,
                        'Número de radicación del proceso': num_radicacion,
                        'Partes procesales': partes_procesales
                    }
                    df = generate_index(folder_path, metadata)
                    
                    # Generar Excel
                    excel_file = generate_excel(df)
                    st.download_button(
                        label="Descargar Índice en Excel",
                        data=excel_file,
                        file_name="indice_electronico.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # Generar PDF
                    pdf_file = generate_pdf(df)
                    st.download_button(
                        label="Descargar Índice en PDF",
                        data=pdf_file,
                        file_name="indice_electronico.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success("Índice electrónico generado con éxito.")
            else:
                st.error("Por favor, complete todos los campos de metadatos.")
    else:
        st.info("Por favor, seleccione los archivos que contienen los documentos del expediente.")

    st.markdown("---")
    st.write("Desarrollado por Alexander Oviedo Fadul")
    st.write("Profesional Universitario Grado 11 - Consejo Seccional de la Judicatura de Sucre")
    st.write("[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [LinkedIn](https://www.linkedin.com/in/alexanderoviedo/)")
    st.write("Este proyecto es una evolución del trabajo inicial realizado por [HammerDev99 Daniel](https://github.com/HammerDev99/GestionExpedienteElectronico_Version1)")

if __name__ == "__main__":
    main()