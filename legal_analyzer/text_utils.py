from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


STOPWORDS = {
    "para", "como", "esta", "este", "estos", "estas", "desde", "hasta",
    "sobre", "entre", "dentro", "fuera", "ante", "bajo", "contra",
    "segun", "mediante", "porque", "cuando", "donde", "quien", "cual",
    "del", "las", "los", "una", "unos", "unas", "por", "con", "sin",
    "que", "sus", "son", "sea", "ser", "fue", "han", "hay", "mas",
    "al", "se", "de", "la", "el", "en", "y", "o", "a", "un", "su",
}


def normalize(text: str) -> str:
    text = text or ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )
    text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    text = (text or "").replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def useful_characters(text: str) -> int:
    return len(re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9]", "", text or ""))


def meaningful_words(text: str) -> set[str]:
    words = re.findall(r"\b[a-záéíóúñ]{4,}\b", normalize(text))
    return {word for word in words if word not in STOPWORDS}


def text_similarity(left: str, right: str) -> float:
    left_words = meaningful_words(left)
    right_words = meaningful_words(right)

    if not left_words or not right_words:
        return 0.0

    intersection = left_words.intersection(right_words)
    union = left_words.union(right_words)

    jaccard = len(intersection) / max(len(union), 1)
    sequence = SequenceMatcher(
        None,
        " ".join(sorted(left_words)),
        " ".join(sorted(right_words)),
    ).ratio()

    return round((jaccard * 0.75) + (sequence * 0.25), 4)


def split_fragments(text: str, min_length: int = 30) -> list[str]:
    text = clean_text(text)

    fragments = re.split(
        r"(?:\n\s*\n)|"
        r"(?<=[.;:])\s+(?=(?:primero|segundo|tercero|cuarto|quinto|"
        r"sexto|septimo|octavo|noveno|decimo|ordenar|ordenese|"
        r"requerir|requierase|disponer|autorizar|entregar|garantizar)\b)",
        text,
        flags=re.IGNORECASE,
    )

    return [
        re.sub(r"\s+", " ", fragment).strip()
        for fragment in fragments
        if len(fragment.strip()) >= min_length
    ]
