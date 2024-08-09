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

    folder_path = st.text_input("Ingrese la ruta de la carpeta que contiene los documentos del expediente:")

    if folder_path and os.path.isdir(folder_path):
        st.success("Carpeta seleccionada correctamente.")
        
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
        st.error("Por favor, ingrese una ruta de carpeta válida.")

    st.markdown("---")
    st.write("Desarrollado por el Consejo Superior de la Judicatura")

if __name__ == "__main__":
    main()