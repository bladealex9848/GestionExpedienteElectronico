from __future__ import annotations

import re

from .models import OrderRecord, PageTrace
from .text_utils import meaningful_words, normalize, split_fragments


ORDER_VERBS = (
    "ordenar", "ordena", "ordenese", "requerir", "requiere",
    "requierase", "disponer", "dispone", "autorizar", "autorice",
    "entregar", "garantizar", "realizar", "programar", "suministrar",
    "responder", "resolver", "remitir", "abstenerse", "vincular",
    "notificar", "adoptar",
)


def looks_like_judgment(pages: list[PageTrace]) -> bool:
    text = normalize(" ".join(page.text for page in pages))
    signals = (
        "fallo de tutela",
        "administrando justicia",
        "en merito de lo expuesto",
        "resuelve",
        "amparar",
        "negar el amparo",
    )
    return sum(signal in text for signal in signals) >= 2


def extract_responsible(order_text: str) -> str:
    patterns = [
        r"ordenar\s+a\s+(.{3,160}?)(?:\s+que\s+|\s+para\s+|,|\.)",
        r"ordenese\s+a\s+(.{3,160}?)(?:\s+que\s+|\s+para\s+|,|\.)",
        r"requerir\s+a\s+(.{3,160}?)(?:\s+para\s+|\s+que\s+|,|\.)",
        r"requierase\s+a\s+(.{3,160}?)(?:\s+para\s+|\s+que\s+|,|\.)",
    ]

    normalized = normalize(order_text)

    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" ,.;:")

    return "Requiere identificación manual"


def extract_deadline(order_text: str) -> str:
    patterns = [
        r"(?:dentro de|en el termino de|plazo de)\s+"
        r"(?:las\s+|los\s+)?(?:\d+|[a-záéíóúñ]+)\s+"
        r"(?:horas|dias)(?:\s+habiles)?",
        r"termino improrrogable de\s+"
        r"(?:\d+|[a-záéíóúñ]+)\s+"
        r"(?:horas|dias)(?:\s+habiles)?",
        r"de manera inmediata",
        r"inmediatamente",
    ]

    normalized = normalize(order_text)

    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return match.group(0)

    return "No detectado"


def extract_conduct(order_text: str) -> str:
    normalized = normalize(order_text)
    for verb in ORDER_VERBS:
        position = normalized.find(verb)
        if position >= 0:
            return normalized[position:position + 350]
    return normalized[:350]


def extract_orders(
    source_document: str,
    pages: list[PageTrace],
) -> list[OrderRecord]:
    orders: list[OrderRecord] = []
    inside_resolves = False
    order_id = 1

    for page in pages:
        normalized_page = normalize(page.text)

        if "resuelve" in normalized_page:
            inside_resolves = True

        if not inside_resolves:
            continue

        for fragment in split_fragments(page.text):
            normalized_fragment = normalize(fragment)

            if not any(verb in normalized_fragment for verb in ORDER_VERBS):
                continue

            text = fragment[:2200]
            orders.append(
                OrderRecord(
                    order_id=order_id,
                    text=text,
                    source_document=source_document,
                    source_page=page.page,
                    responsible=extract_responsible(text),
                    deadline=extract_deadline(text),
                    conduct=extract_conduct(text),
                    keywords=sorted(meaningful_words(text))[:25],
                )
            )
            order_id += 1

    if orders:
        return orders[:40]

    for page in pages:
        for fragment in split_fragments(page.text):
            normalized_fragment = normalize(fragment)

            if any(verb in normalized_fragment for verb in ORDER_VERBS):
                text = fragment[:2200]
                orders.append(
                    OrderRecord(
                        order_id=order_id,
                        text=text,
                        source_document=source_document,
                        source_page=page.page,
                        responsible=extract_responsible(text),
                        deadline=extract_deadline(text),
                        conduct=extract_conduct(text),
                        keywords=sorted(meaningful_words(text))[:25],
                    )
                )
                order_id += 1

    return orders[:40]
