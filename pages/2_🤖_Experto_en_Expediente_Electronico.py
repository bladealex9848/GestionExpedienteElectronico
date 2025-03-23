# Importación de bibliotecas necesarias
import os
import openai
import streamlit as st
import time
from io import BytesIO
import base64

# Configuración de la página
st.set_page_config(
    page_title="Experto en Gestión Documental Judicial",
    page_icon="🏛️📄",
    layout="wide",
    menu_items={
        "Get Help": "https://www.ramajudicial.gov.co/web/centro-de-documentacion-judicial/protocolo-para-la-gestion-de-documentos-electronicos",
        "Report a bug": None,
        "About": "Experto en Gestión Documental Judicial: Tu asistente para la gestión de documentos electrónicos en la Rama Judicial de Colombia. Obtén información precisa y actualizada sobre los requisitos, procedimientos y herramientas tecnológicas.",
    },
)


# Función para verificar si el archivo secrets.toml existe
def secrets_file_exists():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    return os.path.isfile(secrets_path)


# Intentar obtener el ID del asistente de OpenAI desde st.secrets si el archivo secrets.toml existe
if secrets_file_exists():
    try:
        ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
    except KeyError:
        ASSISTANT_ID = None
else:
    ASSISTANT_ID = None

# Si no está disponible, pedir al usuario que lo introduzca
if not ASSISTANT_ID:
    ASSISTANT_ID = st.sidebar.text_input(
        "Introduce el ID del asistente de OpenAI", type="password"
    )

# Si aún no se proporciona el ID, mostrar un error y detener la ejecución
if not ASSISTANT_ID:
    st.sidebar.error("Por favor, proporciona el ID del asistente de OpenAI.")
    st.stop()

assistant_id = ASSISTANT_ID

# Inicialización del cliente de OpenAI
client = openai


def get_binary_file_downloader_html(url, file_label="File"):
    href = f'<a href="{url}" target="_blank">Descargar {file_label}</a>'
    return href


# Sidebar
st.sidebar.title("Recursos Adicionales")
with st.sidebar.expander("Ver Recursos Adicionales", expanded=False):
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/IndiceElectronicoC0", "Plantilla Excel"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/GestionExpedienteElectronicoGuiaUso", "Guía de Uso"
        ),
        unsafe_allow_html=True,
    )

st.sidebar.title("Marco Normativo")
with st.sidebar.expander("Ver Marco Normativo", expanded=False):
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/PCSJA20-11567", "ACUERDO PCSJA20-11567"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/PCSJA23-12094", "ACUERDO PCSJA23-12094"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/PCSJC24-23", "CIRCULAR PCSJC24-23"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/PlanSectorialDesarrolloRamaJudicial2023-2026",
            "Plan Sectorial de Desarrollo Rama Judicial 2023-2026",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/seccion-de-gestion-documental",
            "División de Gestión Documental",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/gestion-de-documentos-electronicos",
            "Gestión de documentos electrónicos",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/ProtocoloGestionDocumentosElectronicos",
            "Protocolo para la gestión de documentos electrónicos",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        get_binary_file_downloader_html(
            "https://enki.care/ABCExpedienteJudicialElectronicoV6",
            "ABC Expediente Judicial Electrónico",
        ),
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")
st.sidebar.image("assets/logo_CSJ_Sucre.png", width=200)
st.sidebar.write(
    "<div style='text-align: center;'>Desarrollado por Equipo Marduk</div>",
    unsafe_allow_html=True,
)
st.sidebar.write(
    "<div style='text-align: center;'>v.1.3.4 Lite | v.1.4.4 AgilEx</div>",
    unsafe_allow_html=True,
)
st.sidebar.write(
    "<div style='text-align: center;'><a href='https://github.com/bladealex9848'>GitHub Lite</a> | <a href='https://github.com/HammerDev99'>GitHub AgilEx</a> | <a href='https://marduk.pro/'>Website</a></div>",
    unsafe_allow_html=True,
)

# Presentación del agente
st.title("Bienvenido al Experto en Gestión Documental Judicial 🏛️📄")

st.write(
    """
    [![ver código fuente](https://img.shields.io/badge/Repositorio%20GitHub-gris?logo=github)](https://github.com/bladealex9848/GestionExpedienteElectronico)
    ![Visitantes](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgestionexpedienteelectronico.streamlit.app&label=Visitantes&labelColor=%235d5d5d&countColor=%231e7ebf&style=flat)
    """
)

st.markdown(
    """
### ¡Hola! Soy tu Experto en Gestión Documental Judicial

Estoy aquí para ayudarte a entender y aplicar el Protocolo para la Gestión de Documentos Electrónicos en la Rama Judicial de Colombia. 

#### ¿En qué puedo ayudarte hoy? 🤔

* Explicarte los requisitos y procedimientos para la producción, gestión y tratamiento de documentos electrónicos.
* Guiarte en la creación y organización de expedientes electrónicos.
* Brindar información sobre la digitalización de documentos físicos.
* Aclarar tus dudas sobre el almacenamiento, acceso, consulta, cierre, retención y disposición final de los expedientes electrónicos.
* Ofrecerte información actualizada sobre las herramientas tecnológicas disponibles.

**¡No dudes en consultarme! Estoy aquí para facilitar tu transición a la gestión documental electrónica y ayudarte a cumplir con los estándares de la Rama Judicial.**
"""
)

# Inicialización de variables de estado de sesión
st.session_state.start_chat = True
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Cargar la clave API de OpenAI
API_KEY = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    API_KEY = st.sidebar.text_input("Introduce tu clave API de OpenAI", type="password")

if not API_KEY:
    st.sidebar.error("Por favor, proporciona una clave API para continuar.")
    st.stop()

openai.api_key = API_KEY


def process_message_with_citations(message):
    """Extraiga y devuelva solo el texto del mensaje del asistente."""
    if hasattr(message, "content") and len(message.content) > 0:
        message_content = message.content[0]
        if hasattr(message_content, "text"):
            nested_text = message_content.text
            if hasattr(nested_text, "value"):
                return nested_text.value
    return "No se pudo procesar el mensaje"


# Crear un hilo de chat inmediatamente después de cargar la clave API
if not st.session_state.thread_id:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.write("ID del hilo: ", thread.id)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("¿Cómo puedo ayudarte hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("usuario"):
        st.markdown(prompt)

    # Enviar mensaje del usuario
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id, role="user", content=prompt
    )

    # Crear una ejecución para el hilo de chat
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id, assistant_id=assistant_id
    )

    while run.status != "completed":
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id, run_id=run.id
        )

    # Recuperar mensajes agregados por el asistente
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)

    # Procesar y mostrar mensajes del asistente
    for message in messages:
        if message.run_id == run.id and message.role == "assistant":
            full_response = process_message_with_citations(message)
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
            with st.chat_message("assistant"):
                st.markdown(full_response)
