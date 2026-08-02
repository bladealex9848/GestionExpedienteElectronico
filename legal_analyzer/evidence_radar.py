from __future__ import annotations

import re
from collections import Counter, defaultdict

from .models import PageTrace
from .text_utils import normalize, split_fragments


EVIDENCE_TYPES = {
    "Acta de entrega": ("acta de entrega", "recibido a satisfaccion", "firma de recibido"),
    "Constancia de envío": ("constancia de envio", "correo enviado", "guia", "radicado"),
    "Concepto médico": ("concepto medico", "medico tratante", "valoracion medica"),
    "Autorización": ("autorizacion", "servicio autorizado", "orden de servicio"),
    "Factura o soporte económico": ("factura", "comprobante de pago", "recibo"),
    "Respuesta institucional": ("en respuesta", "se informa", "contestacion"),
    "Notificación": ("notificacion", "notificado", "acuse de recibo"),
    "Fórmula u orden médica": ("formula medica", "orden medica", "prescripcion"),
    "Historia clínica": ("historia clinica", "epicrisis", "evolucion"),
    "Registro fotográfico": ("fotografia", "imagen", "captura de pantalla"),
}

ENTITY_PATTERNS = (
    r"\b(?:EPS|IPS|JUZGADO|TRIBUNAL|SECRETAR[IÍ]A|MINISTERIO|ALCALD[IÍ]A|"
    r"PROCURADUR[IÍ]A|DEFENSOR[IÍ]A|SUPERINTENDENCIA)\s+[A-ZÁÉÍÓÚÑ0-9][A-ZÁÉÍÓÚÑ0-9 .,&\-]{2,70}",
    r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}\b",
)

RELATION_WORDS = {
    "ordenó": ("ordena", "ordeno", "ordenar", "dispone"),
    "respondió": ("respondio", "contesto", "informa", "manifesto"),
    "entregó": ("entrego", "hizo entrega", "suministro"),
    "autorizó": ("autorizo", "aprobo", "emitio autorizacion"),
    "negó": ("nego", "rechazo", "no autorizo"),
    "notificó": ("notifico", "comunico", "envio"),
    "solicitó": ("solicito", "pidio", "requirio"),
}


def extract_entities(documents: dict[str, list[PageTrace]]) -> list[dict]:
    counter: Counter[str] = Counter()
    sources: defaultdict[str, set[str]] = defaultdict(set)

    for name, pages in documents.items():
        for page in pages:
            text = page.text
            for pattern in ENTITY_PATTERNS:
                for match in re.findall(pattern, text):
                    entity = re.sub(r"\s+", " ", match).strip(" ,.-")
                    if 4 <= len(entity) <= 80:
                        counter[entity] += 1
                        sources[entity].add(f"{name}, p. {page.page}")

    rows = []
    for entity, count in counter.most_common(30):
        rows.append({
            "Entidad o persona": entity,
            "Menciones": count,
            "Fuentes": " | ".join(sorted(sources[entity])[:8]),
        })
    return rows


def extract_relations(documents: dict[str, list[PageTrace]], entities: list[dict]) -> list[dict]:
    names = [row["Entidad o persona"] for row in entities]
    relations = []

    for document_name, pages in documents.items():
        for page in pages:
            for fragment in split_fragments(page.text, min_length=30):
                normalized = normalize(fragment)
                present = [name for name in names if normalize(name) in normalized]

                if not present:
                    continue

                relation = ""
                for label, expressions in RELATION_WORDS.items():
                    if any(expression in normalized for expression in expressions):
                        relation = label
                        break

                if not relation:
                    continue

                subject = present[0]
                object_name = present[1] if len(present) > 1 else "hecho o documento referido"

                relations.append({
                    "Origen": subject,
                    "Relación": relation,
                    "Destino": object_name,
                    "Documento": document_name,
                    "Página": page.page,
                    "Fragmento": fragment[:900],
                })

    unique = []
    seen = set()
    for row in relations:
        key = (row["Origen"], row["Relación"], row["Destino"], row["Documento"], row["Página"])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique[:80]


def evidence_inventory(documents: dict[str, list[PageTrace]]) -> list[dict]:
    rows = []

    for evidence_type, expressions in EVIDENCE_TYPES.items():
        matches = []
        for name, pages in documents.items():
            for page in pages:
                normalized = normalize(page.text)
                if any(expression in normalized for expression in expressions):
                    matches.append(f"{name}, p. {page.page}")

        rows.append({
            "Tipo de prueba": evidence_type,
            "Estado": "Localizada" if matches else "No localizada",
            "Cantidad de fuentes": len(matches),
            "Fuentes": " | ".join(matches[:12]),
            "Revisión humana": "",
        })

    return rows


def missing_evidence_actions(inventory: list[dict]) -> list[str]:
    mapping = {
        "Acta de entrega": "Solicitar acta firmada, fecha, identificación del bien y persona que recibió.",
        "Constancia de envío": "Solicitar soporte de radicación, guía, acuse o registro de entrega electrónica.",
        "Concepto médico": "Solicitar concepto del médico tratante con fecha, identificación y fundamento clínico.",
        "Autorización": "Solicitar número, vigencia, prestador asignado y servicio autorizado.",
        "Factura o soporte económico": "Solicitar factura, comprobante, orden de compra o soporte de pago.",
        "Respuesta institucional": "Solicitar respuesta expresa, congruente y de fondo.",
        "Notificación": "Solicitar constancia de notificación y fecha exacta de recepción.",
        "Fórmula u orden médica": "Aportar orden médica completa y vigente.",
        "Historia clínica": "Solicitar historia clínica o extracto pertinente con reserva de datos sensibles.",
        "Registro fotográfico": "Aportar imágenes legibles con contexto, fecha y origen verificable.",
    }

    return [
        mapping[row["Tipo de prueba"]]
        for row in inventory
        if row["Estado"] == "No localizada"
    ]


def graphviz_source(relations: list[dict]) -> str:
    lines = [
        "digraph expediente {",
        'rankdir="LR";',
        'graph [bgcolor="transparent", pad="0.3", nodesep="0.5", ranksep="0.8"];',
        'node [shape="box", style="rounded,filled", fillcolor="white", fontname="Arial"];',
        'edge [fontname="Arial", fontsize="10"];',
    ]

    safe_nodes = {}
    node_id = 0

    for row in relations[:35]:
        for label in (row["Origen"], row["Destino"]):
            if label not in safe_nodes:
                node_id += 1
                safe_nodes[label] = f"n{node_id}"
                escaped = label.replace('"', "'")
                lines.append(f'{safe_nodes[label]} [label="{escaped}"];')

        relation = row["Relación"].replace('"', "'")
        lines.append(
            f'{safe_nodes[row["Origen"]]} -> {safe_nodes[row["Destino"]]} '
            f'[label="{relation}"];'
        )

    lines.append("}")
    return "\n".join(lines)


def theory_of_case(
    metadata: dict[str, str],
    inventory: list[dict],
    relations: list[dict],
) -> str:
    located = [row["Tipo de prueba"] for row in inventory if row["Estado"] == "Localizada"]
    missing = [row["Tipo de prueba"] for row in inventory if row["Estado"] == "No localizada"]

    parts = [
        f"El expediente identificado con radicado {metadata.get('Radicado') or 'no determinado'} "
        f"relaciona como accionante a {metadata.get('Accionante') or 'parte no identificada'} "
        f"y como parte accionada a {metadata.get('Accionado') or 'entidad no identificada'}.",
        f"Se localizaron {len(located)} categorías de prueba: "
        + (", ".join(located) if located else "ninguna con las reglas actuales")
        + ".",
        f"Permanecen sin localizar {len(missing)} categorías relevantes: "
        + (", ".join(missing) if missing else "ninguna")
        + ".",
        f"El mapa detectó {len(relations)} relaciones documentales entre personas, entidades, "
        "actuaciones y hechos.",
        "La teoría del caso debe consolidarse únicamente después de verificar cada fragmento "
        "contra el documento original, su fecha, integridad y autenticidad.",
    ]

    return " ".join(parts)
