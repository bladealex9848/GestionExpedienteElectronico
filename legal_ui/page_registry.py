from __future__ import annotations

from pathlib import Path

from legal_ui.brand import BRAND_NAME

PAGES_DIR = Path(__file__).resolve().parent.parent / "pages"
HOME_PAGE = "🏠_Inicio.py"

# (etiqueta, ruta relativa al entrypoint 🏠_Inicio.py)
APP_PAGES: list[tuple[str, str]] = [
    ("🏠 Inicio", HOME_PAGE),
    ("📊 Hoja de Ruta", "pages/1_📊_Hoja_de_Ruta.py"),
    ("🤖 Asistente Legal", "pages/2_🤖_Experto_en_Expediente_Electronico.py"),
    ("📊 Informe SIUGJ", "pages/3_📊_Informe_Consolidado_SIUGJ.py"),
    (f"⚖️ {BRAND_NAME} — Gestión Despacho", "pages/25_Gestion_Casos_Despacho.py"),
]

TOOL_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Consulta normativa",
        [
            ("📚 Consulta iLey CO", "pages/26_Consulta_Normativa_iLey_CO.py"),
        ],
    ),
    (
        "Análisis y auditoría",
        [
            ("🔍 Analizador Jurídico", "pages/4_Analizador_Juridico.py"),
            ("📋 OCR Matriz Cumplimiento", "pages/5_OCR_Matriz_Cumplimiento.py"),
            ("⚖️ Auditor Jurídico V2", "pages/6_Auditor_Juridico_V2.py"),
            ("🧠 Expediente Inteligente V3", "pages/7_Expediente_Inteligente_V3.py"),
            ("🎯 Centro de Mando Jurídico", "pages/8_Centro_Mando_Juridico.py"),
        ],
    ),
    (
        "Estrategia y producción",
        [
            ("♟️ Sala Estrategia Jurídica", "pages/9_Sala_Estrategia_Juridica.py"),
            ("📡 Radar Probatorio 360", "pages/10_Radar_Probatorio_360.py"),
            ("✍️ Fábrica Escritos Jurídicos", "pages/11_Fabrica_Escritos_Juridicos.py"),
            ("🚦 Semáforo del Expediente", "pages/12_Semaforo_Expediente.py"),
        ],
    ),
    (
        "Panel y términos",
        [
            ("🧠 Panel Integral Expediente", "pages/13_Panel_Integral_Expediente.py"),
            ("📅 Control de Términos", "pages/14_Control_Terminos.py"),
            ("⚖️ Analizador Términos Colombia", "pages/15_Analizador_Legal_Terminos_Colombia.py"),
        ],
    ),
    (
        "Vigilancia judicial",
        [
            ("📋 Preparador Vigilancia", "pages/16_Preparador_Vigilancia_Judicial.py"),
            ("🔎 Auditor Errores Despachos", "pages/17_Auditor_Errores_Despachos.py"),
            ("❓ Preguntas Revisión Vigilancia", "pages/18_Preguntas_Revision_Vigilancia.py"),
            ("📚 Revisor Integral Vigilancia", "pages/19_Revisor_Integral_Vigilancia.py"),
            ("📂 Organizador Automático", "pages/24_Organizador_Automatico_Vigilancia.py"),
        ],
    ),
    (
        "Motores avanzados",
        [
            ("⚙️ Motor Jurídico Avanzado", "pages/20_Motor_Juridico_Avanzado.py"),
            ("🔬 Auditor Forense Judicial", "pages/21_Auditor_Forense_Judicial_Litigantes.py"),
            ("🔗 Detector Concordancia Fallos", "pages/22_Detector_Concordancia_Fallo_Providencias.py"),
            ("🏛️ Centro Integral Auditoría", "pages/23_Centro_Integral_Auditoria_Judicial.py"),
        ],
    ),
]


def all_tool_pages() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for _, pages in TOOL_SECTIONS:
        rows.extend(pages)
    return rows


def page_exists(page_path: str) -> bool:
    root = Path(__file__).resolve().parent.parent
    return (root / page_path).is_file()
