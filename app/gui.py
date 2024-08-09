import streamlit as st
from datetime import datetime

def create_info_table():
    """
    Crea y muestra una tabla con información general del programa.
    """
    st.markdown("""
    | Versión | Descripción | Desarrollado por |
    |---------|-------------|-------------------|
    | 1.0     | Sistema de Gestión de Expedientes Electrónicos Judiciales | Consejo Superior de la Judicatura |
    """)

def show_instructions():
    """
    Muestra las instrucciones de uso del sistema.
    """
    st.markdown("""
    ## Instrucciones de Uso

    1. Ingrese la ruta de la carpeta que contiene los documentos del expediente.
    2. Complete los metadatos del expediente en los campos proporcionados.
    3. Haga clic en "Generar Índice Electrónico" para procesar los documentos.
    4. Descargue el índice en formato Excel y PDF utilizando los botones correspondientes.

    **Nota:** Asegúrese de que todos los documentos estén en formatos compatibles (PDF, DOC, DOCX, XLS, XLSX, JPG, PNG).
    """)

def show_metadata_form():
    """
    Muestra el formulario para ingresar los metadatos del expediente.
    """
    st.subheader("Metadatos del Expediente")
    
    ciudad = st.text_input("Ciudad:")
    despacho_judicial = st.text_input("Despacho Judicial:")
    serie_subserie = st.selectbox("Serie/Subserie documental:", 
                                  ["Acciones Constitucionales", "Expedientes de Procesos Judiciales"])
    num_radicacion = st.text_input("Número de radicación del proceso:")
    parte_a = st.text_input("Parte A (Demandado, Procesado, Accionado):")
    parte_b = st.text_input("Parte B (Demandante, Denunciante, Accionante):")
    terceros = st.text_input("Terceros intervinientes (opcional):")
    
    partes_procesales = f"Parte A: {parte_a}\nParte B: {parte_b}"
    if terceros:
        partes_procesales += f"\nTerceros: {terceros}"

    return {
        'Ciudad': ciudad,
        'Despacho Judicial': despacho_judicial,
        'Serie/Subserie documental': serie_subserie,
        'Número de radicación del proceso': num_radicacion,
        'Partes procesales': partes_procesales
    }

def show_processing_status(status):
    """
    Muestra el estado del procesamiento de los documentos.
    """
    if status == "success":
        st.success("Índice electrónico generado con éxito.")
    elif status == "error":
        st.error("Se produjo un error al generar el índice electrónico.")
    else:
        st.warning("Procesando documentos...")

def show_download_buttons(excel_file, pdf_file):
    """
    Muestra los botones para descargar los archivos generados.
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="Descargar Índice en Excel",
            data=excel_file,
            file_name=f"indice_electronico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        st.download_button(
            label="Descargar Índice en PDF",
            data=pdf_file,
            file_name=f"indice_electronico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )

def show_footer():
    """
    Muestra el pie de página de la aplicación.
    """
    st.markdown("---")
    st.write("Desarrollado por el Consejo Superior de la Judicatura")
    st.write(f"Fecha y hora de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")