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
        st.markdown(get_binary_file_downloader_html("https://enki.care/ProtocoloGestionDocumentosElectronicos", 'Protocolo para la gestión de documentos electrónicos'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/ABCExpedienteJudicialElectronicoV6", 'ABC Expediente Judicial Electrónico'), unsafe_allow_html=True)

    st.sidebar.title("Descargar Versiones Portables")
    with st.sidebar.expander("Ver Versiones Portables", expanded=False):
        st.markdown(get_binary_file_downloader_html("https://enki.care/GestionExpedienteElectronicoWindows", 'Versión Portable para Windows'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/GestionExpedienteElectronicoMac", 'Versión Portable para Mac'), unsafe_allow_html=True)
        st.markdown(get_binary_file_downloader_html("https://enki.care/GestionExpedienteElectronicoLinux", 'Versión Portable para Linux'), unsafe_allow_html=True)

    st.sidebar.markdown("---")
    # Centrar el contenido de la barra lateral
    st.sidebar.image("assets/logo_CSJ_Sucre.png", width=200)
    st.sidebar.write("<div style='text-align: center;'>Desarrollado por Alexander Oviedo Fadul</div>", unsafe_allow_html=True)
    st.sidebar.write("<div style='text-align: center;'>v.1.3.2</div>", unsafe_allow_html=True)
    st.sidebar.write("<div style='text-align: center;'><a href='https://github.com/bladealex9848'>GitHub</a> | <a href='https://www.alexanderoviedofadul.dev/'>Website</a> | <a href='https://www.linkedin.com/in/alexander-oviedo-fadul/'>LinkedIn</a></div>", unsafe_allow_html=True)

    # Main content
    
    # Titulo    
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
                    if df is None:
                        raise ValueError("La generación del índice falló.")
                    
                    progress_bar.progress(66)
                    
                    index_file_path = os.path.join(temp_folder, "00IndiceElectronicoC0.xlsx")
                    save_excel_file(df, index_file_path, use_template=False)
                    
                    progress_bar.progress(100)
                    st.success("Índice electrónico generado con éxito.")
                    
                    with open(index_file_path, "rb") as f:
                        st.download_button(label='Descargar Índice Electrónico', data=f, file_name=os.path.basename(index_file_path), mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                
                except Exception as e:
                    st.error(f"Ocurrió un error: {str(e)}")

if __name__ == "__main__":
    main()
