import streamlit as st
import os
import pandas as pd
from index_generator import generate_index_from_scratch
from file_utils import rename_files
from excel_handler import save_excel_file
import base64
import tempfile

# Configuración de Streamlit
st.set_page_config(
    page_title="Sistema de Gestión de Expedientes Electrónicos Judiciales",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state='expanded',    
    menu_items={
        'Get Help': 'https://alexander.oviedo.isabellaea.com/',
        'Report a bug': 'https://github.com/bladealex9848/GestionExpedienteElectronico/issues',
        'About': "El Sistema de Gestión de Expedientes Electrónicos Judiciales es una herramienta para generar índices electrónicos de expedientes judiciales, cumpliendo con los estándares establecidos por el Consejo Superior de la Judicatura."
    }
)

def get_binary_file_downloader_html(url, file_label='File'):
    href = f'<a href="{url}" target="_blank">Descargar {file_label}</a>'
    return href

def main():
    # Sidebar
    st.sidebar.title("Recursos Adicionales")
    with st.sidebar.expander("Ver Recursos Adicionales", expanded=False):
        st.markdown(get_binary_file_downloader_html("https://enki.care/IndiceElectronicoC0", 'Plantilla Excel'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/GestionExpedienteElectronicoGuiaUso", 'Guía de Uso'), unsafe_allow_html=True)

    st.sidebar.title("Marco Normativo")
    with st.sidebar.expander("Ver Marco Normativo", expanded=False):
        st.markdown(get_binary_file_downloader_html("https://enki.care/PCSJA20-11567", 'ACUERDO PCSJA20-11567'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/PCSJA23-12094", 'ACUERDO PCSJA23-12094'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/PCSJC24-23", 'CIRCULAR PCSJC24-23'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/PlanSectorialDesarrolloRamaJudicial2023-2026", 'Plan Sectorial de Desarrollo Rama Judicial 2023-2026'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/seccion-de-gestion-documental", 'División de Gestión Documental'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/gestion-de-documentos-electronicos", 'Gestión de documentos electrónicos'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/ProtocoloGestionDocumentosElectronicos", 'Protocolo para la gestión de documentos electrónicos'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/ABCExpedienteJudicialElectronicoV6", 'ABC Expediente Judicial Electrónico'), unsafe_allow_html=True)        

    st.sidebar.markdown("---")
    st.sidebar.image("assets/logo_CSJ_Sucre.png", width=200)
    st.sidebar.write("<div style='text-align: center;'>Desarrollado por Equipo Marduk</div>", unsafe_allow_html=True)
    st.sidebar.write("<div style='text-align: center;'>v.1.3.3 Lite | v.1.3.0 Ultimate</div>", unsafe_allow_html=True)
    st.sidebar.write("<div style='text-align: center;'><a href='https://github.com/bladealex9848'>GitHub Lite</a> | <a href='https://github.com/HammerDev99'>GitHub Ultimate</a> | <a href='https://marduk.pro/'>Website</a></div>", unsafe_allow_html=True)

    # Main content
    st.title("Sistema de Gestión de Expedientes Electrónicos Judiciales")
    
    st.write("""
    [![ver código fuente](https://img.shields.io/badge/Repositorio%20GitHub-gris?logo=github)](https://github.com/bladealex9848/GestionExpedienteElectronico)
    ![Visitantes](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgestionexpedienteelectronico.streamlit.app&label=Visitantes&labelColor=%235d5d5d&countColor=%231e7ebf&style=flat)
    """)

    # Tabs para las diferentes versiones
    tab1, tab2 = st.tabs(["Versiones de Escritorio", "Versión Web"])

    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("Versión Lite")
            st.write("Ideal para procesar una carpeta a la vez. Perfecta para usuarios que manejan volúmenes moderados de expedientes.")
            st.markdown(get_binary_file_downloader_html("https://enki.care/GestionExpedienteElectronicoWindows", 'Versión Lite'), unsafe_allow_html=True)
        
        with col2:
            st.header("Versión Ultimate")
            st.write("Capacidad de procesamiento masivo. Diseñada para usuarios que necesitan manejar grandes volúmenes de expedientes simultáneamente.")
            st.markdown(get_binary_file_downloader_html("https://enki.care/GestionExpedienteElectronicoUltimate", 'Versión Ultimate'), unsafe_allow_html=True)

    with tab2:
        st.header("Versión Web de Entrenamiento")
        st.write("Esta versión en línea permite generar el índice electrónico de expedientes judiciales.")

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
                        if df is None:
                            raise ValueError("La generación del índice falló.")
                        
                        progress_bar.progress(66)
                        
                        index_file_path = os.path.join(temp_folder, "000IndiceElectronicoC0.xlsx")
                        save_excel_file(df, index_file_path, use_template=False)
                        
                        progress_bar.progress(100)
                        st.success("Índice electrónico generado con éxito.")
                        
                        with open(index_file_path, "rb") as f:
                            st.download_button(label='Descargar Índice Electrónico', data=f, file_name=os.path.basename(index_file_path), mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    
                    except Exception as e:
                        st.error(f"Ocurrió un error: {str(e)}")

    # Instrucciones de uso
    with st.expander("Instrucciones de Uso"):
        st.write("""
        1. Descargue la carpeta del expediente sin incluir ningún índice.
        2. Nombre la carpeta con el radicado de 23 dígitos.
        3. Verifique que los metadatos de los archivos sean consistentes con los documentos originales.
        4. Cierre cualquier archivo de Excel abierto antes de ejecutar el programa.
        5. Asegúrese de que la estructura de la carpeta sea: carpeta_seleccionada/subcarpeta/archivos_para_indice.
        6. El procesamiento comenzará automáticamente una vez seleccionada la carpeta.
        """)

if __name__ == "__main__":
    main()
