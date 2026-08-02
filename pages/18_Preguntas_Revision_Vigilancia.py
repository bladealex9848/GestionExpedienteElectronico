import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Preguntas Vigilancia Judicial",
    page_icon="❓",
    layout="wide",
)

st.title("❓ Preguntas para revisar la Vigilancia Judicial")
st.caption(
    "Responde con base en los documentos del proceso. "
    "El sistema indicará si está lista, si faltan soportes o si no corresponde al mecanismo."
)

st.warning(
    "La Vigilancia Judicial Administrativa revisa oportunidad y eficacia de la gestión. "
    "No sustituye recursos ni permite cambiar el contenido de una providencia."
)

QUESTIONS = [
    ("Competencia", "¿La autoridad cuestionada es un juzgado, tribunal o despacho judicial?", 12, True,
     "La autoridad parece estar dentro del ámbito de la Vigilancia Judicial.",
     "Debe verificarse otro mecanismo porque la autoridad no parece ser un despacho judicial.",
     "Providencia o consulta oficial donde aparezca el despacho."),
    ("Identificación", "¿Se conoce el nombre exacto del despacho judicial?", 8, True,
     "El despacho está individualizado.",
     "Falta identificar con precisión el despacho vigilado.",
     "Encabezado de providencia o consulta del proceso."),
    ("Identificación", "¿Se conoce el número completo de radicación?", 8, True,
     "El proceso está individualizado.",
     "Falta el número completo del proceso.",
     "Carátula, providencia o consulta oficial."),
    ("Actuación pendiente", "¿Puedes señalar exactamente qué actuación judicial está pendiente?", 12, True,
     "Existe una actuación concreta pendiente.",
     "Debe precisarse qué actuación falta por realizar.",
     "Memorial, auto o constancia que identifique la actuación pendiente."),
    ("Fecha y mora", "¿Existe prueba de la fecha en que se solicitó o debía realizarse la actuación?", 12, True,
     "Puede construirse una cronología verificable.",
     "Sin una fecha comprobable no puede evaluarse bien la demora.",
     "Correo, sello de recibido, radicación o constancia del sistema."),
    ("Fecha y mora", "¿El término legal o judicial aplicable ya venció?", 12, False,
     "Existe un indicio objetivo de posible demora.",
     "La solicitud puede ser prematura.",
     "Norma, auto que fijó el término y constancia de notificación."),
    ("Gestión previa", "¿Se presentó memorial de impulso, solicitud de decisión o petición de información?", 8, False,
     "Se acredita gestión previa del interesado.",
     "Conviene valorar primero una solicitud de impulso o información.",
     "Memorial y constancia de recepción."),
    ("Gestión posterior", "¿Después de esa solicitud el despacho permaneció sin pronunciamiento?", 10, False,
     "Hay un indicio adicional de falta de gestión.",
     "Debe revisarse si ya existe una actuación posterior.",
     "Consulta actual del expediente y última providencia."),
    ("Finalidad correcta", "¿La solicitud busca que el despacho actúe y no que el Consejo cambie una decisión judicial?", 12, True,
     "La finalidad coincide con el control administrativo de oportunidad y eficacia.",
     "La Vigilancia no sustituye recursos ni modifica providencias.",
     "Texto revisado de la solicitud."),
    ("Soportes", "¿Los documentos permiten reconstruir la secuencia completa de actuaciones?", 6, False,
     "La cronología documental es suficiente para una revisión preliminar.",
     "Faltan piezas para demostrar la secuencia.",
     "Providencias, memoriales, respuestas, notificaciones y consulta del proceso."),
]

responses = []
score = 0
maximum = sum(item[2] for item in QUESTIONS)
critical_failure = False
positive = []
negative = []
missing = []

for index, (category, question, weight, required, yes_text, no_text, evidence) in enumerate(QUESTIONS, 1):
    answer = st.radio(
        f"{index}. {question}",
        ["Sí", "No", "No estoy seguro"],
        horizontal=True,
        key=f"review_question_{index}",
    )

    if answer == "Sí":
        score += weight
        result = yes_text
        positive.append(result)
    elif answer == "No":
        result = no_text
        negative.append(result)
        missing.append(evidence)
        if required:
            critical_failure = True
    else:
        result = "Debe comprobarse antes de radicar."
        missing.append(evidence)
        if required:
            critical_failure = True

    responses.append({
        "Categoría": category,
        "Pregunta": question,
        "Respuesta": answer,
        "Peso": weight,
        "Resultado": result,
        "Soporte requerido": evidence,
    })

percentage = round((score / maximum) * 100) if maximum else 0

if critical_failure or percentage < 45:
    color = "Rojo"
    title = "NO ESTÁ LISTA PARA RADICAR"
    recommendation = (
        "Faltan requisitos esenciales o debe corregirse la finalidad. "
        "Completa los soportes y revisa las respuestas antes de radicar."
    )
elif percentage < 75:
    color = "Amarillo"
    title = "REQUIERE COMPLETAR Y REVISAR"
    recommendation = (
        "Existen elementos útiles, pero todavía faltan soportes o confirmaciones importantes."
    )
else:
    color = "Verde"
    title = "LISTA PRELIMINARMENTE PARA PREPARAR"
    recommendation = (
        "Las respuestas respaldan preliminarmente la preparación. "
        "Haz una revisión final del escrito y de los anexos."
    )

icon = {"Verde": "🟢", "Amarillo": "🟡", "Rojo": "🔴"}[color]

if color == "Verde":
    st.success(f"{icon} {title} — {percentage}/100")
elif color == "Amarillo":
    st.warning(f"{icon} {title} — {percentage}/100")
else:
    st.error(f"{icon} {title} — {percentage}/100")

st.markdown(f"**Conclusión:** {recommendation}")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### Aspectos favorables")
    if positive:
        for item in positive:
            st.markdown(f"✅ {item}")
    else:
        st.caption("No se registraron respuestas favorables.")

with c2:
    st.markdown("### Aspectos por corregir")
    if negative:
        for item in negative:
            st.markdown(f"❌ {item}")
    else:
        st.caption("No se registraron respuestas negativas.")

st.markdown("### Soportes o verificaciones pendientes")

unique_missing = list(dict.fromkeys(missing))

if unique_missing:
    for item in unique_missing:
        st.markdown(f"📎 {item}")
else:
    st.success("No se detectaron soportes pendientes.")

df = pd.DataFrame(responses)

with st.expander("Ver matriz completa"):
    st.dataframe(df, use_container_width=True, hide_index=True)

summary = pd.DataFrame([{
    "Semáforo": color,
    "Resultado": title,
    "Puntaje": percentage,
    "Conclusión": recommendation,
    "Soportes pendientes": " | ".join(unique_missing),
}])

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Preguntas", index=False)
    summary.to_excel(writer, sheet_name="Resultado", index=False)

st.download_button(
    "Descargar revisión en Excel",
    data=output.getvalue(),
    file_name="revision_vigilancia_judicial.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)
