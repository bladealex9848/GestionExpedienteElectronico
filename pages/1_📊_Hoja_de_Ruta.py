import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.figure_factory as ff
from io import BytesIO
import base64

# Configuración de la página
st.set_page_config(layout="wide", page_title="Hoja de Ruta - SGDE", page_icon="📊")

# Estilos CSS personalizados (se mantienen igual)
st.markdown(
    """
<style>
    .big-font {
        font-size:24px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size:18px !important;
        font-weight: bold;
    }
    .small-font {
        font-size:14px !important;
    }
    .info-card {
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .info-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    .progress-card {
        background-color: #e3f2fd;
    }
    .current-card {
        background-color: #e8f5e9;
    }
    .next-card {
        background-color: #fce4ec;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .centered-percentage {
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 60px !important;
        font-weight: bold;
        color: #4CAF50;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Configurar la zona horaria de Bogotá
bogota_tz = pytz.timezone("America/Bogota")
fecha_actual = datetime.now(bogota_tz).replace(
    hour=0, minute=0, second=0, microsecond=0
)  # (No visualiza las actividades completadas ni en proceso)
# fecha_actual = datetime(2024, 10, 1, tzinfo=bogota_tz) (Visualiza las actividades completadas y en proceso)
# Que la fecha actual sea con datetime.now() para que se actualice automáticamente pero que visualice las actividades completadas y en proceso


# Función para cargar los datos
def cargar_datos():
    data = {
        "Aprobación de la estrategia": {"Start": "2024-08-14", "Finish": "2024-08-14"},
        "Comunicación oficial": {"Start": "2024-08-15", "Finish": "2024-08-15"},
        "Formación del equipo de revisión interdisciplinaria": {
            "Start": "2024-08-16",
            "Finish": "2024-08-16",
        },
        "Distribución de materiales": {"Start": "2024-08-17", "Finish": "2024-08-17"},
        "Proceso de revisión": {"Start": "2024-08-18", "Finish": "2024-08-29"},
        "Recopilación y análisis del informe ejecutivo": {
            "Start": "2024-08-30",
            "Finish": "2024-09-01",
        },
        "Ajustes y mejoras": {"Start": "2024-09-02", "Finish": "2024-09-08"},
        "Validación de ajustes": {"Start": "2024-09-09", "Finish": "2024-09-10"},
        "Planificación de la implementación piloto": {
            "Start": "2024-09-11",
            "Finish": "2024-09-15",
        },
        "Preparación de materiales de capacitación": {
            "Start": "2024-09-16",
            "Finish": "2024-09-22",
        },
        "Lanzamiento del proyecto piloto": {
            "Start": "2024-09-23",
            "Finish": "2024-10-06",
        },
        "Monitoreo y evaluación del piloto": {
            "Start": "2024-10-07",
            "Finish": "2024-10-20",
        },
        "Ajustes finales": {"Start": "2024-10-21", "Finish": "2024-10-27"},
        "Planificación del despliegue general": {
            "Start": "2024-10-28",
            "Finish": "2024-11-03",
        },
        "Inicio del despliegue general": {
            "Start": "2024-11-04",
            "Finish": "2024-11-17",
        },
        "Seguimiento y soporte continuo": {
            "Start": "2024-11-18",
            "Finish": "2024-12-01",
        },
        "Preparación para la integración con Alfresco": {
            "Start": "2024-12-02",
            "Finish": "2024-12-15",
        },
    }
    df = pd.DataFrame(data).T.reset_index()
    df.columns = ["Task", "Start", "Finish"]
    df["Start"] = pd.to_datetime(df["Start"]).dt.tz_localize(bogota_tz)
    df["Finish"] = pd.to_datetime(df["Finish"]).dt.tz_localize(bogota_tz)
    return df


def determinar_estado_actual(row):
    if fecha_actual > row["Finish"]:
        return "Completado"
    elif fecha_actual >= row["Start"] and fecha_actual <= row["Finish"]:
        return "En proceso"
    else:
        return "Pendiente"


def crear_gantt(df):
    fig = ff.create_gantt(
        df,
        colors={
            "Completado": "#4CAF50",
            "En proceso": "#2196F3",
            "Pendiente": "#9E9E9E",
        },
        index_col="Estado",
        show_colorbar=True,
        group_tasks=True,
    )

    fig.update_layout(
        title=dict(text="Timeline del Proyecto", font=dict(size=24)),
        xaxis_title="Fecha",
        yaxis_title="Actividad",
        height=500,
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        ),
    )
    return fig


def get_binary_file_downloader_html(url, file_label="File"):
    href = f'<a href="{url}" target="_blank">Descargar {file_label}</a>'
    return href


def main():
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

    st.title("🚀 Hoja de Ruta - Implementación")

    st.write(
        """
    [![ver código fuente](https://img.shields.io/badge/Repositorio%20GitHub-gris?logo=github)](https://github.com/bladealex9848/GestionExpedienteElectronico)
    ![Visitantes](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgestionexpedienteelectronico.streamlit.app&label=Visitantes&labelColor=%235d5d5d&countColor=%231e7ebf&style=flat)
    """
    )

    df = cargar_datos()
    df["Estado"] = df.apply(determinar_estado_actual, axis=1)

    # Crear y mostrar el timeline
    fig_gantt = crear_gantt(df)
    st.plotly_chart(fig_gantt, use_container_width=True)

    # Información de progreso y actividades
    col1, col2, col3 = st.columns(3)

    with col1:
        actividades_completadas = sum(df["Estado"] == "Completado")
        total_actividades = len(df)
        progreso = actividades_completadas / total_actividades
        st.markdown(
            f"""
        <div class="info-card progress-card">
            <p class="medium-font">🏆 Progreso General</p>
            <div class="centered-percentage">{progreso:.0%}</div>
            <p class="small-font">📌 {actividades_completadas} de {total_actividades} actividades completadas</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.progress(progreso)

    with col2:
        actividad_actual = df[df["Estado"] == "En proceso"]
        if not actividad_actual.empty:
            st.markdown(
                f"""
            <div class="info-card current-card">
                <p class="medium-font">🔄 Actividad Actual</p>
                <p class="big-font" style="color: #2196F3;">{actividad_actual['Task'].values[0]}</p>
                <p class="small-font">📅 Inicio: {actividad_actual['Start'].dt.strftime('%Y-%m-%d').values[0]}</p>
                <p class="small-font">📅 Fin: {actividad_actual['Finish'].dt.strftime('%Y-%m-%d').values[0]}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div class="info-card current-card">
                <p class="medium-font">🔄 Actividad Actual</p>
                <p class="small-font">No hay actividades en proceso</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col3:
        proximas_actividades = df[df["Start"] > fecha_actual].sort_values("Start")
        if not proximas_actividades.empty:
            proxima_actividad = proximas_actividades.iloc[0]
            st.markdown(
                f"""
            <div class="info-card next-card">
                <p class="medium-font">⏭️ Próxima Actividad</p>
                <p class="big-font" style="color: #F44336;">{proxima_actividad['Task']}</p>
                <p class="small-font">📅 Inicio: {proxima_actividad['Start'].strftime('%Y-%m-%d')}</p>
                <p class="small-font">📅 Fin: {proxima_actividad['Finish'].strftime('%Y-%m-%d')}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div class="info-card next-card">
                <p class="medium-font">⏭️ Próxima Actividad</p>
                <p class="small-font">No hay actividades futuras programadas</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Fecha actual en la parte inferior
    st.markdown(
        f'<p class="small-font" style="text-align:right;">📅 Fecha actual: {fecha_actual.strftime("%Y-%m-%d")}</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
