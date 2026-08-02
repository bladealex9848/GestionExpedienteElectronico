import io
import re
import unicodedata
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from pdf_compat import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


st.set_page_config(
    page_title="Analizador Jurídico",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ Analizador jurídico de expedientes")
st.caption(
    "Analiza tutelas, desacatos y derechos de petición. "
    "Los resultados deben ser revisados por una persona."
)


TIPOS_DOCUMENTO = {
    "Derecho de petición": [
        "derecho de peticion",
        "ley 1755",
        "articulo 23 de la constitucion",
        "peticion respetuosa",
    ],
    "Acción de tutela": [
        "accion de tutela",
        "solicitud de amparo",
        "derechos fundamentales",
        "decreto 2591",
    ],
    "Auto admisorio": [
        "auto admisorio",
        "admite la accion de tutela",
        "admitir la presente accion",
        "correr traslado",
    ],
    "Contestación": [
        "contestacion",
        "respuesta a la accion de tutela",
        "informe rendido",
        "pronunciamiento de la entidad",
    ],
    "Fallo de tutela": [
        "fallo de tutela",
        "administrando justicia",
        "resuelve",
        "amparar los derechos",
        "negar el amparo",
    ],
    "Impugnación": [
        "impugnacion",
        "impugnar el fallo",
        "segunda instancia",
    ],
    "Incidente de desacato": [
        "incidente de desacato",
        "solicitud de desacato",
        "incumplimiento del fallo",
    ],
    "Auto de requerimiento": [
        "auto de requerimiento",
        "requierase",
        "requerir a",
        "previo a iniciar incidente",
    ],
    "Respuesta de cumplimiento": [
        "informe de cumplimiento",
        "cumplimiento del fallo",
        "se dio cumplimiento",
        "acreditamos cumplimiento",
    ],
    "Notificación": [
        "constancia de notificacion",
        "notificacion electronica",
        "constancia de envio",
        "correo electronico",
    ],
}


DERECHOS = {
    "Derecho de petición": [
        "derecho fundamental de peticion",
        "derecho de peticion",
    ],
    "Debido proceso": [
        "debido proceso",
    ],
    "Salud": [
        "derecho fundamental a la salud",
        "derecho a la salud",
    ],
    "Vida digna": [
        "vida digna",
        "dignidad humana",
    ],
    "Igualdad": [
        "derecho a la igualdad",
    ],
    "Mínimo vital": [
        "minimo vital",
    ],
    "Acceso a la justicia": [
        "acceso a la administracion de justicia",
        "acceso a la justicia",
    ],
    "Seguridad social": [
        "seguridad social",
    ],
}


def normalizar(texto: str) -> str:
    texto = texto or ""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    texto = texto.lower()
    return re.sub(r"\s+", " ", texto).strip()


def limpiar_texto(texto: str) -> str:
    texto = texto.replace("\x00", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def extraer_texto_pdf(contenido: bytes) -> tuple[str, list[str]]:
    lector = PdfReader(io.BytesIO(contenido))
    paginas = []

    for numero, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        paginas.append(limpiar_texto(texto))

    return "\n\n".join(paginas), paginas


def clasificar_documento(texto: str) -> tuple[str, int]:
    texto_normalizado = normalizar(texto)
    mejor_tipo = "Documento no clasificado"
    mejor_puntaje = 0

    for tipo, expresiones in TIPOS_DOCUMENTO.items():
        puntaje = sum(
            1 for expresion in expresiones
            if expresion in texto_normalizado
        )

        if puntaje > mejor_puntaje:
            mejor_tipo = tipo
            mejor_puntaje = puntaje

    return mejor_tipo, mejor_puntaje


def buscar_fecha(texto: str) -> Optional[str]:
    texto_normalizado = normalizar(texto)

    patron_numerico = (
        r"\b([0-3]?\d)[/-]([01]?\d)[/-]((?:19|20)\d{2})\b"
    )

    coincidencia = re.search(patron_numerico, texto_normalizado)

    if coincidencia:
        dia, mes, anio = coincidencia.groups()

        try:
            return datetime(
                int(anio),
                int(mes),
                int(dia),
            ).strftime("%Y-%m-%d")
        except ValueError:
            pass

    meses = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    patron_textual = (
        r"\b([0-3]?\d)\s+de\s+("
        + "|".join(meses.keys())
        + r")\s+de\s+((?:19|20)\d{2})\b"
    )

    coincidencia = re.search(patron_textual, texto_normalizado)

    if coincidencia:
        dia, mes_texto, anio = coincidencia.groups()

        try:
            return datetime(
                int(anio),
                meses[mes_texto],
                int(dia),
            ).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def buscar_radicado(texto: str) -> Optional[str]:
    patrones = [
        r"\b\d{2}[-\s]\d{3}[-\s]\d{2}[-\s]\d{2}[-\s]\d{3}[-\s]\d{4}[-\s]\d{5}[-\s]\d{2}\b",
        r"\b\d{23}\b",
        r"radicaci[oó]n\s*[:#]?\s*([0-9\-\s]{15,35})",
        r"radicado\s*[:#]?\s*([0-9\-\s]{10,35})",
    ]

    for patron in patrones:
        coincidencia = re.search(
            patron,
            texto,
            flags=re.IGNORECASE,
        )

        if coincidencia:
            valor = (
                coincidencia.group(1)
                if coincidencia.lastindex
                else coincidencia.group(0)
            )
            return re.sub(r"\s+", "", valor).strip(":- ")

    return None


def detectar_derechos(texto: str) -> list[str]:
    texto_normalizado = normalizar(texto)
    encontrados = []

    for derecho, expresiones in DERECHOS.items():
        if any(
            expresion in texto_normalizado
            for expresion in expresiones
        ):
            encontrados.append(derecho)

    return encontrados


def extraer_bloque(
    texto: str,
    encabezados_inicio: list[str],
    encabezados_fin: list[str],
    limite: int = 5000,
) -> str:
    texto_normalizado = normalizar(texto)
    inicio = -1

    for encabezado in encabezados_inicio:
        posicion = texto_normalizado.find(normalizar(encabezado))

        if posicion >= 0:
            inicio = posicion + len(normalizar(encabezado))
            break

    if inicio < 0:
        return ""

    fin = min(len(texto_normalizado), inicio + limite)

    for encabezado in encabezados_fin:
        posicion = texto_normalizado.find(
            normalizar(encabezado),
            inicio,
        )

        if posicion >= 0:
            fin = min(fin, posicion)

    return texto_normalizado[inicio:fin].strip(" :.-\n")


def extraer_pretensiones(texto: str) -> str:
    return extraer_bloque(
        texto,
        [
            "pretensiones",
            "peticiones",
            "solicitudes",
            "solicito al despacho",
        ],
        [
            "fundamentos de derecho",
            "pruebas",
            "anexos",
            "juramento",
            "competencia",
            "notificaciones",
        ],
    )


def extraer_ordenes(texto: str) -> str:
    bloque = extraer_bloque(
        texto,
        [
            "resuelve",
            "parte resolutiva",
            "en merito de lo expuesto",
        ],
        [
            "notifiquese",
            "comuniquese",
            "cumplase",
            "firma",
        ],
        limite=7000,
    )

    if bloque:
        return bloque

    texto_normalizado = normalizar(texto)
    frases = re.findall(
        r"(?:ordenar|ordenese|requerir|requierase|amparar|"
        r"negar|conceder)[^.]{20,500}\.",
        texto_normalizado,
    )

    return " ".join(frases[:10])


def extraer_plazos(texto: str) -> list[str]:
    texto_normalizado = normalizar(texto)

    patrones = [
        r"\b(?:dentro de|en el termino de|plazo de)\s+"
        r"(?:las\s+)?\d+\s+horas\b",
        r"\b(?:dentro de|en el termino de|plazo de)\s+"
        r"(?:los\s+)?\d+\s+dias(?:\s+habiles)?\b",
        r"\btermino improrrogable de\s+\d+\s+"
        r"(?:horas|dias(?:\s+habiles)?)\b",
        r"\ben un plazo no superior a\s+\d+\s+"
        r"(?:horas|dias(?:\s+habiles)?)\b",
    ]

    resultados = []

    for patron in patrones:
        resultados.extend(
            re.findall(patron, texto_normalizado)
        )

    return list(dict.fromkeys(resultados))


def localizar_paginas(
    paginas: list[str],
    expresiones: list[str],
) -> list[int]:
    encontradas = []

    for numero, pagina in enumerate(paginas, start=1):
        pagina_normalizada = normalizar(pagina)

        if any(
            normalizar(expresion) in pagina_normalizada
            for expresion in expresiones
        ):
            encontradas.append(numero)

    return encontradas


def crear_resumen(texto: str, limite: int = 900) -> str:
    texto_limpio = re.sub(r"\s+", " ", texto).strip()

    if not texto_limpio:
        return "No fue posible extraer texto digital."

    return texto_limpio[:limite] + (
        "..." if len(texto_limpio) > limite else ""
    )


def evaluar_documento(
    tipo: str,
    texto: str,
    pretensiones: str,
    ordenes: str,
    plazos: list[str],
) -> list[str]:
    hallazgos = []
    texto_normalizado = normalizar(texto)

    if tipo == "Derecho de petición":
        if "respuesta" not in texto_normalizado:
            hallazgos.append(
                "Debe comprobarse la fecha de radicación y la respuesta recibida."
            )

    if tipo == "Acción de tutela" and not pretensiones:
        hallazgos.append(
            "No se identificó claramente el capítulo de pretensiones."
        )

    if tipo == "Fallo de tutela":
        if not ordenes:
            hallazgos.append(
                "No se logró identificar la parte resolutiva del fallo."
            )

        if plazos:
            hallazgos.append(
                "El fallo contiene uno o más plazos que deben verificarse."
            )

    if tipo == "Contestación":
        expresiones_evasivas = [
            "falta de legitimacion",
            "hecho superado",
            "carencia actual de objeto",
            "no nos consta",
            "no es de nuestra competencia",
        ]

        detectadas = [
            expresion for expresion in expresiones_evasivas
            if expresion in texto_normalizado
        ]

        if detectadas:
            hallazgos.append(
                "La contestación utiliza argumentos que deben contrastarse: "
                + ", ".join(detectadas)
                + "."
            )

    if tipo in {
        "Incidente de desacato",
        "Respuesta de cumplimiento",
    }:
        hallazgos.append(
            "Debe compararse esta pieza con cada orden concreta del fallo."
        )

    if len(texto.strip()) < 100:
        hallazgos.append(
            "El PDF parece escaneado o contiene muy poco texto; podría requerir OCR."
        )

    return hallazgos


archivos = st.file_uploader(
    "Sube todas las piezas procesales del mismo expediente",
    type=["pdf"],
    accept_multiple_files=True,
)

if not archivos:
    st.info(
        "Carga los PDF del proceso: petición, tutela, auto admisorio, "
        "contestaciones, fallo, desacato, requerimientos y respuestas."
    )
    st.stop()


resultados = []
detalle_documentos = []
barra = st.progress(0)

for indice, archivo in enumerate(archivos):
    try:
        contenido = archivo.getvalue()
        texto, paginas = extraer_texto_pdf(contenido)

        tipo, confianza = clasificar_documento(texto)
        fecha = buscar_fecha(texto)
        radicado = buscar_radicado(texto)
        derechos = detectar_derechos(texto)
        pretensiones = extraer_pretensiones(texto)
        ordenes = extraer_ordenes(texto)
        plazos = extraer_plazos(texto)

        paginas_resuelve = localizar_paginas(
            paginas,
            ["resuelve", "ordenar", "ordenese"],
        )

        hallazgos = evaluar_documento(
            tipo,
            texto,
            pretensiones,
            ordenes,
            plazos,
        )

        resultados.append(
            {
                "Fecha": fecha,
                "Documento": archivo.name,
                "Tipo": tipo,
                "Radicado": radicado,
                "Derechos detectados": ", ".join(derechos),
                "Plazos": ", ".join(plazos),
                "Páginas": len(paginas),
                "Confianza": confianza,
                "Hallazgos": " | ".join(hallazgos),
            }
        )

        detalle_documentos.append(
            {
                "nombre": archivo.name,
                "tipo": tipo,
                "fecha": fecha,
                "radicado": radicado,
                "derechos": derechos,
                "paginas": len(paginas),
                "paginas_resuelve": paginas_resuelve,
                "pretensiones": pretensiones,
                "ordenes": ordenes,
                "plazos": plazos,
                "hallazgos": hallazgos,
                "resumen": crear_resumen(texto),
                "texto": texto,
            }
        )

    except Exception as error:
        resultados.append(
            {
                "Fecha": None,
                "Documento": archivo.name,
                "Tipo": "Error de lectura",
                "Radicado": None,
                "Derechos detectados": "",
                "Plazos": "",
                "Páginas": 0,
                "Confianza": 0,
                "Hallazgos": str(error),
            }
        )

    barra.progress((indice + 1) / len(archivos))


tabla = pd.DataFrame(resultados)
tabla["_orden"] = pd.to_datetime(tabla["Fecha"], errors="coerce")
tabla = tabla.sort_values(
    ["_orden", "Documento"],
    na_position="last",
).drop(columns="_orden")


st.success(f"Se analizaron {len(tabla)} piezas procesales.")

columna1, columna2, columna3, columna4 = st.columns(4)

columna1.metric("Documentos", len(tabla))
columna2.metric(
    "Páginas",
    int(tabla["Páginas"].sum()),
)
columna3.metric(
    "Con fecha detectada",
    int(tabla["Fecha"].notna().sum()),
)
columna4.metric(
    "Con alertas",
    int((tabla["Hallazgos"].str.len() > 0).sum()),
)


st.subheader("1. Línea de tiempo procesal")

st.dataframe(
    tabla[
        [
            "Fecha",
            "Documento",
            "Tipo",
            "Radicado",
            "Páginas",
            "Hallazgos",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)


st.subheader("2. Comparación preliminar")

documentos_tutela = [
    documento for documento in detalle_documentos
    if documento["tipo"] == "Acción de tutela"
]

documentos_fallo = [
    documento for documento in detalle_documentos
    if documento["tipo"] == "Fallo de tutela"
]

documentos_cumplimiento = [
    documento for documento in detalle_documentos
    if documento["tipo"] in {
        "Respuesta de cumplimiento",
        "Contestación",
        "Incidente de desacato",
    }
]

comparacion = pd.DataFrame(
    [
        {
            "Elemento": "Lo solicitado",
            "Resultado": (
                documentos_tutela[0]["pretensiones"]
                if documentos_tutela
                else "No se identificó una acción de tutela."
            ),
        },
        {
            "Elemento": "Lo ordenado",
            "Resultado": (
                documentos_fallo[0]["ordenes"]
                if documentos_fallo
                else "No se identificó un fallo de tutela."
            ),
        },
        {
            "Elemento": "Plazos judiciales",
            "Resultado": (
                ", ".join(documentos_fallo[0]["plazos"])
                if documentos_fallo
                and documentos_fallo[0]["plazos"]
                else "No se detectaron plazos automáticamente."
            ),
        },
        {
            "Elemento": "Piezas de cumplimiento",
            "Resultado": (
                ", ".join(
                    documento["nombre"]
                    for documento in documentos_cumplimiento
                )
                if documentos_cumplimiento
                else "No se identificaron respuestas o piezas de cumplimiento."
            ),
        },
    ]
)

st.dataframe(
    comparacion,
    use_container_width=True,
    hide_index=True,
)


st.subheader("3. Análisis individual")

for documento in detalle_documentos:
    titulo = (
        f"{documento['tipo']} — {documento['nombre']}"
    )

    with st.expander(titulo):
        st.write(
            f"**Fecha detectada:** "
            f"{documento['fecha'] or 'No detectada'}"
        )
        st.write(
            f"**Radicado:** "
            f"{documento['radicado'] or 'No detectado'}"
        )
        st.write(
            f"**Derechos:** "
            f"{', '.join(documento['derechos']) or 'No detectados'}"
        )
        st.write(
            f"**Páginas con posibles órdenes:** "
            f"{documento['paginas_resuelve'] or 'No localizadas'}"
        )

        if documento["pretensiones"]:
            st.markdown("#### Pretensiones identificadas")
            st.write(documento["pretensiones"])

        if documento["ordenes"]:
            st.markdown("#### Órdenes identificadas")
            st.write(documento["ordenes"])

        if documento["plazos"]:
            st.markdown("#### Plazos encontrados")
            for plazo in documento["plazos"]:
                st.write(f"- {plazo}")

        if documento["hallazgos"]:
            st.markdown("#### Alertas preliminares")
            for hallazgo in documento["hallazgos"]:
                st.warning(hallazgo)

        st.markdown("#### Resumen")
        st.write(documento["resumen"])


st.subheader("4. Alertas generales")

alertas_generales = []

tipos_presentes = set(tabla["Tipo"].tolist())

if "Acción de tutela" in tipos_presentes and "Fallo de tutela" not in tipos_presentes:
    alertas_generales.append(
        "Se encontró una tutela, pero no se identificó el fallo."
    )

if "Fallo de tutela" in tipos_presentes and not documentos_cumplimiento:
    alertas_generales.append(
        "Existe un fallo, pero no se identificaron piezas posteriores "
        "que permitan revisar su cumplimiento."
    )

if "Incidente de desacato" in tipos_presentes and "Fallo de tutela" not in tipos_presentes:
    alertas_generales.append(
        "Se encontró un desacato sin el fallo que contiene las órdenes originales."
    )

if not alertas_generales:
    st.success(
        "No se detectaron faltantes estructurales evidentes. "
        "Esto no confirma que el expediente esté completo."
    )
else:
    for alerta in alertas_generales:
        st.warning(alerta)


archivo_excel = io.BytesIO()

with pd.ExcelWriter(archivo_excel, engine="openpyxl") as escritor:
    tabla.to_excel(
        escritor,
        sheet_name="Linea de tiempo",
        index=False,
    )

    comparacion.to_excel(
        escritor,
        sheet_name="Comparacion",
        index=False,
    )




def generar_informe_word(
    tabla: pd.DataFrame,
    comparacion: pd.DataFrame,
    documentos: list[dict],
    alertas: list[str],
) -> bytes:
    documento_word = Document()

    estilos = documento_word.styles

    estilos["Normal"].font.name = "Arial"
    estilos["Normal"].font.size = Pt(11)

    titulo = documento_word.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER

    texto_titulo = titulo.add_run(
        "INFORME PRELIMINAR DE ANÁLISIS JURÍDICO"
    )
    texto_titulo.bold = True
    texto_titulo.font.size = Pt(15)

    subtitulo = documento_word.add_paragraph()
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitulo.add_run(
        "Tutelas, desacatos y derechos de petición"
    ).italic = True

    documento_word.add_paragraph()

    documento_word.add_heading(
        "1. Advertencia sobre el alcance del informe",
        level=1,
    )

    documento_word.add_paragraph(
        "El presente documento fue generado mediante análisis automático "
        "de patrones textuales. Es un apoyo preliminar y no reemplaza la "
        "revisión integral del expediente, la asesoría jurídica ni la "
        "valoración probatoria realizada por una persona competente."
    )

    documento_word.add_heading(
        "2. Resumen general del expediente",
        level=1,
    )

    resumen = documento_word.add_table(rows=4, cols=2)
    resumen.style = "Table Grid"

    resumen.cell(0, 0).text = "Documentos analizados"
    resumen.cell(0, 1).text = str(len(tabla))

    resumen.cell(1, 0).text = "Número total de páginas"
    resumen.cell(1, 1).text = str(int(tabla["Páginas"].sum()))

    resumen.cell(2, 0).text = "Documentos con fecha detectada"
    resumen.cell(2, 1).text = str(
        int(tabla["Fecha"].notna().sum())
    )

    resumen.cell(3, 0).text = "Documentos con alertas"
    resumen.cell(3, 1).text = str(
        int((tabla["Hallazgos"].str.len() > 0).sum())
    )

    documento_word.add_heading(
        "3. Línea de tiempo procesal",
        level=1,
    )

    columnas_tiempo = [
        "Fecha",
        "Documento",
        "Tipo",
        "Radicado",
        "Páginas",
    ]

    tabla_word = documento_word.add_table(
        rows=1,
        cols=len(columnas_tiempo),
    )
    tabla_word.style = "Table Grid"

    for indice, columna in enumerate(columnas_tiempo):
        tabla_word.rows[0].cells[indice].text = columna

    for _, fila in tabla.iterrows():
        celdas = tabla_word.add_row().cells

        for indice, columna in enumerate(columnas_tiempo):
            valor = fila.get(columna, "")
            celdas[indice].text = (
                "" if pd.isna(valor) else str(valor)
            )

    documento_word.add_heading(
        "4. Comparación preliminar",
        level=1,
    )

    for _, fila in comparacion.iterrows():
        parrafo = documento_word.add_paragraph()

        etiqueta = parrafo.add_run(
            f"{fila['Elemento']}: "
        )
        etiqueta.bold = True

        parrafo.add_run(str(fila["Resultado"]))

    documento_word.add_heading(
        "5. Análisis individual de las piezas",
        level=1,
    )

    for numero, pieza in enumerate(documentos, start=1):
        documento_word.add_heading(
            f"5.{numero}. {pieza['tipo']} — {pieza['nombre']}",
            level=2,
        )

        documento_word.add_paragraph(
            f"Fecha detectada: {pieza['fecha'] or 'No detectada'}"
        )
        documento_word.add_paragraph(
            f"Radicado: {pieza['radicado'] or 'No detectado'}"
        )
        documento_word.add_paragraph(
            "Derechos detectados: "
            + (
                ", ".join(pieza["derechos"])
                if pieza["derechos"]
                else "No detectados"
            )
        )

        if pieza["pretensiones"]:
            documento_word.add_heading(
                "Pretensiones identificadas",
                level=3,
            )
            documento_word.add_paragraph(
                pieza["pretensiones"]
            )

        if pieza["ordenes"]:
            documento_word.add_heading(
                "Órdenes identificadas",
                level=3,
            )
            documento_word.add_paragraph(
                pieza["ordenes"]
            )

        if pieza["plazos"]:
            documento_word.add_heading(
                "Plazos detectados",
                level=3,
            )

            for plazo in pieza["plazos"]:
                documento_word.add_paragraph(
                    plazo,
                    style="List Bullet",
                )

        if pieza["hallazgos"]:
            documento_word.add_heading(
                "Alertas preliminares",
                level=3,
            )

            for hallazgo in pieza["hallazgos"]:
                documento_word.add_paragraph(
                    hallazgo,
                    style="List Bullet",
                )

        documento_word.add_heading(
            "Resumen de la pieza",
            level=3,
        )
        documento_word.add_paragraph(
            pieza["resumen"]
        )

    documento_word.add_heading(
        "6. Alertas generales",
        level=1,
    )

    if alertas:
        for alerta in alertas:
            documento_word.add_paragraph(
                alerta,
                style="List Bullet",
            )
    else:
        documento_word.add_paragraph(
            "No se detectaron faltantes estructurales evidentes. "
            "Esto no significa que el expediente esté completo."
        )

    documento_word.add_heading(
        "7. Actuaciones que deben revisarse",
        level=1,
    )

    recomendaciones = [
        (
            "Verificar que las fechas detectadas correspondan a la fecha "
            "real de presentación, notificación o decisión."
        ),
        (
            "Comparar cada pretensión de la tutela con la parte resolutiva "
            "del fallo."
        ),
        (
            "Comparar cada orden judicial con los documentos que acrediten "
            "su cumplimiento material."
        ),
        (
            "Revisar personalmente los términos procesales y las constancias "
            "de notificación."
        ),
        (
            "Confirmar que las respuestas sean de fondo, claras, precisas, "
            "congruentes y oportunas."
        ),
    ]

    for recomendacion in recomendaciones:
        documento_word.add_paragraph(
            recomendacion,
            style="List Bullet",
        )

    salida = io.BytesIO()
    documento_word.save(salida)

    return salida.getvalue()

st.download_button(
    "Descargar auditoría preliminar en Excel",
    data=archivo_excel.getvalue(),
    file_name="auditoria_preliminar_expediente.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
)



informe_word = generar_informe_word(
    tabla,
    comparacion,
    detalle_documentos,
    alertas_generales,
)

st.download_button(
    "Descargar informe jurídico en Word",
    data=informe_word,
    file_name="informe_preliminar_juridico.docx",
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),
)

st.warning(
    "La aplicación identifica patrones de texto, pero todavía no realiza "
    "una valoración jurídica definitiva ni calcula términos con calendario judicial."
)

