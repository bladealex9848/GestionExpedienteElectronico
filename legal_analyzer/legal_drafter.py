from __future__ import annotations

from datetime import date


DOCUMENT_TITLES = {
    "Solicitud de cumplimiento": "SOLICITUD DE CUMPLIMIENTO DEL FALLO DE TUTELA",
    "Incidente de desacato": "INCIDENTE DE DESACATO",
    "Pronunciamiento frente a respuesta": "PRONUNCIAMIENTO FRENTE A LA RESPUESTA DE LA ENTIDAD",
    "Solicitud de expediente electrónico": "SOLICITUD DE ACCESO Y REMISIÓN DEL EXPEDIENTE ELECTRÓNICO",
    "Memorial de impulso procesal": "MEMORIAL DE IMPULSO PROCESAL",
    "Derecho de petición": "DERECHO DE PETICIÓN",
}


def build_legal_text(
    document_type: str,
    city: str,
    court: str,
    claimant: str,
    respondent: str,
    case_number: str,
    facts: str,
    requests: str,
    evidence: str,
    legal_basis: str,
    observations: str,
) -> dict[str, str]:
    title = DOCUMENT_TITLES.get(document_type, document_type.upper())
    today = date.today().strftime("%d/%m/%Y")

    heading = (
        f"{city}, {today}\n\n"
        f"Señor(a)\n{court or 'JUZGADO COMPETENTE'}\n"
        f"E. S. D.\n\n"
        f"Referencia: {title}\n"
        f"Radicado: {case_number or 'Por completar'}\n"
        f"Accionante: {claimant or 'Por completar'}\n"
        f"Accionado: {respondent or 'Por completar'}"
    )

    intro_by_type = {
        "Solicitud de cumplimiento": (
            "Respetuosamente solicito al Despacho adoptar las medidas necesarias "
            "para asegurar el cumplimiento material, integral y oportuno de las "
            "órdenes impartidas dentro del proceso de la referencia."
        ),
        "Incidente de desacato": (
            "Respetuosamente promuevo incidente de desacato, con fundamento en "
            "el incumplimiento que se expone a continuación, sin perjuicio de las "
            "medidas directas de cumplimiento que correspondan."
        ),
        "Pronunciamiento frente a respuesta": (
            "Dentro de la oportunidad correspondiente, presento pronunciamiento "
            "frente a la respuesta allegada por la entidad, con el fin de precisar "
            "los aspectos que permanecen sin acreditar o requieren verificación."
        ),
        "Solicitud de expediente electrónico": (
            "Respetuosamente solicito acceso, consulta y remisión íntegra del "
            "expediente electrónico, incluidos memoriales, anexos, constancias, "
            "notificaciones, autos y demás actuaciones."
        ),
        "Memorial de impulso procesal": (
            "Respetuosamente solicito impulsar la actuación y adoptar la decisión "
            "o actuación pendiente dentro de un plazo razonable."
        ),
        "Derecho de petición": (
            "En ejercicio del derecho fundamental de petición, presento las "
            "solicitudes concretas que se relacionan en este escrito."
        ),
    }

    introduction = intro_by_type.get(
        document_type,
        "Respetuosamente presento el siguiente escrito."
    )

    facts_text = facts.strip() or (
        "1. Se deberá completar la relación cronológica y verificable de los hechos.\n"
        "2. Cada afirmación debe relacionarse con su documento y página de respaldo."
    )

    requests_text = requests.strip() or (
        "1. Que se estudie de fondo la presente solicitud.\n"
        "2. Que se adopten las medidas necesarias según los hechos acreditados.\n"
        "3. Que la decisión sea comunicada por el medio indicado."
    )

    evidence_text = evidence.strip() or (
        "Se relacionarán los documentos anexos, indicando nombre del archivo, "
        "fecha, página pertinente y hecho que acredita."
    )

    legal_text = legal_basis.strip() or (
        "La fundamentación jurídica deberá completarse de acuerdo con la naturaleza "
        "de la actuación, el contenido del expediente y las normas vigentes aplicables."
    )

    obs_text = observations.strip()

    closing = (
        "Solicito que las decisiones y comunicaciones sean incorporadas al expediente "
        "y notificadas por los canales procesales correspondientes.\n\n"
        "Atentamente,\n\n"
        f"{claimant or 'Nombre del solicitante'}\n"
        "Documento de identidad: ____________________\n"
        "Correo electrónico: _______________________\n"
        "Teléfono: _________________________________"
    )

    return {
        "title": title,
        "heading": heading,
        "introduction": introduction,
        "facts": facts_text,
        "requests": requests_text,
        "evidence": evidence_text,
        "legal_basis": legal_text,
        "observations": obs_text,
        "closing": closing,
    }
