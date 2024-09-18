import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Informe Consolidado SIUGJ", layout="wide")

# Título principal
st.title("Informe Consolidado sobre la Implementación del Sistema de Gestión Documental Electrónica y su Alineación con SIUGJ")

# Resumen Ejecutivo
st.header("1. Resumen Ejecutivo")
st.write("""
Este informe consolida las evaluaciones realizadas por diversos funcionarios judiciales del Distrito Judicial de Sincelejo 
sobre el ABC - Protocolo para la Gestión de Documentos Electrónicos y la herramienta de software asociada, en el contexto 
de su alineación con los requerimientos del Sistema Integrado Único de Gestión Judicial (SIUGJ). Se analizan aspectos técnicos, 
usabilidad, conformidad con protocolos, impacto en procesos judiciales y se proponen recomendaciones para mejorar tanto el ABC 
como el software.
""")

# Análisis General
st.header("2. Análisis General")

tab1, tab2, tab3, tab4 = st.tabs(["Viabilidad Técnica", "Usabilidad", "Conformidad", "Impacto"])

with tab1:
    st.subheader("2.1 Viabilidad Técnica")
    st.markdown("""
    - Compatibilidad: El sistema es compatible con OneDrive, SharePoint y potencialmente con BESTDoc, alineándose con los requerimientos de SIUGJ.
    - Rendimiento: Se reporta un buen desempeño con grandes volúmenes de documentos.
    - Seguridad: No se proporcionaron detalles específicos sobre medidas de seguridad.
    """)

with tab2:
    st.subheader("2.2 Usabilidad y Experiencia de Usuario")
    st.markdown("""
    - El ABC y el software son generalmente considerados fáciles de usar.
    - La estructura de carpetas y la numeración de archivos (000-999) son apreciadas por su claridad.
    - Se identifican desafíos en la descarga de expedientes grandes y en la transición inicial.
    """)

with tab3:
    st.subheader("2.3 Conformidad con el Protocolo")
    st.markdown("""
    - El sistema se alinea con el protocolo versión 2 para la gestión de documentos electrónicos.
    - La estructura de carpetas y la generación del índice electrónico cumplen con los lineamientos.
    - Se identificaron algunas discrepancias menores en la nomenclatura de archivos.
    """)

with tab4:
    st.subheader("2.4 Impacto en Procesos Judiciales")
    st.markdown("""
    - Mejora significativa en la eficiencia y organización de expedientes.
    - Facilita el acceso remoto y simultáneo a los expedientes.
    - Reduce el uso de papel y optimiza el espacio físico en los despachos.
    """)

# Análisis Individual de Informes
st.header("3. Análisis Individual de Informes")

informes = {
    "Daniel Arbeláez Álvarez (CSP de Bello, Antioquia)": [
        "Destaca la necesidad de alinear el sistema con el nuevo Sistema de Expediente Judicial Electrónico.",
        "Sugiere mantener el uso del protocolo actual como herramienta complementaria."
    ],
    "Jaider Contreras Puentes (Centro de Servicios Penales de Sincelejo)": [
        "Enfatiza la viabilidad técnica del sistema en términos de compatibilidad y rendimiento.",
        "Recomienda priorizar la seguridad de la información y la capacitación del personal."
    ],
    "Mauricio Bedoya (Juzgado 05 Penal Municipal de Sincelejo)": [
        "Identifica desafíos en la digitalización y corrección de expedientes existentes.",
        "Sugiere sesiones de capacitación para resolver dudas sobre el proceso."
    ],
    "Zuleyma Arrieta (Juzgado 06 Civil Circuito Sincelejo)": [
        "Destaca los beneficios en términos de eficiencia y acceso a la información.",
        "Recomienda mantener la numeración de tres dígitos para los archivos."
    ],
    "Rafael Sampayo Tovio (Comisión Seccional de Disciplina Judicial de Sucre)": [
        "Resalta la eficacia del sistema de numeración de tres dígitos.",
        "Confirma la alineación con el Protocolo de Gestión de Expediente Electrónico."
    ]
}

for nombre, puntos in informes.items():
    with st.expander(nombre):
        for punto in puntos:
            st.markdown(f"- {punto}")

# Cambios Propuestos
st.header("4. Cambios Propuestos")

tab5, tab6 = st.tabs(["Cambios al ABC", "Cambios al Código"])

with tab5:
    st.subheader("4.1 Cambios Propuestos al ABC")
    st.markdown("""
    Actualizar el documento "ABC Protocolo para la Gestión de Documentos Electrónicos en la Rama Judicial.pdf":
    - Incluir una sección sobre la integración con SIUGJ y sus requerimientos específicos.
    - Clarificar la nomenclatura de archivos, especialmente respecto al uso de tres dígitos vs. dos dígitos.
    - Añadir información sobre la interacción con sistemas como Justicia XXICS y Tyba.
    - Incorporar guías para la migración de expedientes existentes al nuevo sistema.

    Modificar el archivo "README.md":
    - Actualizar la sección de "Características Principales" para reflejar la alineación con SIUGJ.
    - Añadir una sección sobre "Compatibilidad con Sistemas Existentes".
    - Incluir información sobre el proceso de migración de expedientes.
    """)

with tab6:
    st.subheader("4.2 Cambios Propuestos al Código")
    st.markdown("""
    Modificar "🏠_Inicio.py":
    - Implementar una función para verificar la compatibilidad con Justicia XXICS y Tyba.
    - Añadir una opción en la interfaz para iniciar el proceso de migración a SIUGJ.

    Actualizar "index_generator.py":
    - Modificar la función de generación de índices para asegurar total compatibilidad con SIUGJ.
    - Implementar validaciones adicionales según los criterios de SIUGJ.

    Modificar "file_utils.py":
    - Actualizar la función de renombrado de archivos para ofrecer flexibilidad entre 2 y 3 dígitos.
    - Implementar una función para verificar la validez de las extensiones de archivo según SIUGJ.

    Actualizar "metadata_extractor.py":
    - Añadir funciones para extraer y validar metadatos específicos requeridos por SIUGJ.
    """)

# Justificación de los Cambios
st.header("5. Justificación de los Cambios")
st.write("""
Los cambios propuestos son necesarios para:
1. Asegurar la plena compatibilidad con los requerimientos de SIUGJ.
2. Facilitar el proceso de migración de expedientes existentes.
3. Mejorar la flexibilidad del sistema para adaptarse a diferentes necesidades de los despachos.
4. Incrementar la eficiencia en la gestión de expedientes electrónicos.
5. Garantizar la conformidad con los protocolos y estándares establecidos.
""")

# Conclusiones y Recomendaciones
st.header("6. Conclusiones y Recomendaciones Finales")
st.write("""
El ABC y la herramienta de software desarrollada han demostrado ser efectivos y bien recibidos por los usuarios. 
Sin embargo, para asegurar una transición exitosa a SIUGJ y mantener la eficiencia en la gestión documental, se recomienda:

1. Implementar los cambios propuestos en el ABC y el código.
2. Desarrollar un plan de capacitación integral para todos los usuarios del sistema.
3. Establecer un proceso de retroalimentación continua para seguir mejorando el sistema.
4. Realizar pruebas piloto de migración a SIUGJ en despachos seleccionados antes de una implementación general.
5. Mantener una comunicación constante con el equipo de SIUGJ para asegurar la alineación continua con sus requerimientos.

La implementación de estas recomendaciones permitirá una transición más suave hacia SIUGJ, manteniendo la eficiencia y 
efectividad ya logradas con el sistema actual.
""")

# Nota al pie
st.markdown("---")
st.markdown("Informe generado basado en las evaluaciones de los funcionarios judiciales del Distrito Judicial de Sincelejo y el análisis del equipo de desarrollo.")