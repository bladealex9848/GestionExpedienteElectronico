from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from legal_ui.despacho_store import DATA_DIR

NORMAS_DIR = DATA_DIR / "colombia_normas"
CONSTITUCION_JSON = NORMAS_DIR / "constitucion.json"
CONSTITUCION_FUENTE = NORMAS_DIR / "constitucion_fuente.txt"
CORPUS_VERSION = 6
ILEY_URL = "https://iley.fusense.com/"

ARTICLE_SPLIT = re.compile(
    r"(?:^|\n)\s*ART.{1,8}?CULO\s+(\d+)\.\s*",
    re.IGNORECASE | re.MULTILINE,
)

NORMAS_CATALOGO = [
    {
        "id": "cp1991",
        "nombre": "Constitución Política de Colombia",
        "anio": 1991,
        "tipo": "Constitución",
    },
    {
        "id": "decreto2591",
        "nombre": "Decreto 2591 de 1991 — Acción de tutela",
        "anio": 1991,
        "tipo": "Decreto",
    },
    {
        "id": "ley1755",
        "nombre": "Ley 1755 de 2015 — Derecho de petición",
        "anio": 2015,
        "tipo": "Ley",
    },
]

EMBEDDED_NORMAS: dict[str, dict] = {
    "decreto2591": {
        "id": "decreto2591",
        "nombre": "Decreto 2591 de 1991 — Acción de tutela",
        "anio": 1991,
        "articulos": [
            {
                "numero": 1,
                "seccion": "Disposiciones generales",
                "texto": (
                    "Toda persona tendrá acción de tutela para reclamar ante los jueces, "
                    "en todo momento y lugar, mediante un procedimiento preferente y sumario, "
                    "por sí misma o por quien actúe a su nombre, la protección inmediata de sus "
                    "derechos constitucionales fundamentales, cuando quiera que éstos resulten "
                    "vulnerados o amenazados por la acción o la omisión de cualquier autoridad pública."
                ),
            },
            {
                "numero": 6,
                "seccion": "Procedimiento",
                "texto": (
                    "La acción de tutela procede contra toda acción u omisión de las autoridades "
                    "públicas, que haya violado, viole o amenace violar cualquiera de los derechos "
                    "de que trata el artículo 2 de esta ley. También procede contra acciones u "
                    "omisiones de particulares, de conformidad con lo establecido en el Capítulo III."
                ),
            },
            {
                "numero": 14,
                "seccion": "Términos",
                "texto": (
                    "En caso de urgencia, el juez podrá disponer medidas provisionales "
                    "indispensables para proteger los derechos fundamentales. El fallo de tutela "
                    "deberá proferirse dentro de los diez días siguientes a la presentación de la solicitud."
                ),
            },
        ],
    },
    "ley1755": {
        "id": "ley1755",
        "nombre": "Ley 1755 de 2015 — Derecho de petición",
        "anio": 2015,
        "articulos": [
            {
                "numero": 13,
                "seccion": "Derecho de petición",
                "texto": (
                    "Toda persona tiene derecho a presentar peticiones respetuosas a las autoridades "
                    "por motivos de interés general o particular, y a obtener pronta resolución "
                    "completa y de fondo sobre la misma."
                ),
            },
            {
                "numero": 14,
                "seccion": "Términos de respuesta",
                "texto": (
                    "Las peticiones de documentos y de información deberán resolverse dentro de "
                    "los diez (10) días siguientes a su recepción. Las demás peticiones deberán "
                    "resolverse dentro de los quince (15) días siguientes a su recepción."
                ),
            },
        ],
    },
}


def _fix_mojibake_pairs(text: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        try:
            return match.group(0).encode("latin-1").decode("utf-8")
        except UnicodeDecodeError:
            return match.group(0)

    return re.sub(r"[\u00c2\u00c3][\u0080-\u00bf]", _repl, text)


def _fix_encoding(text: str) -> str:
    text = text.lstrip("\ufeff").replace("\ufeff", "")

    def _fix_latin_mojibake(value: str) -> str | None:
        try:
            return value.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            return None

    if not any(marker in text for marker in ("Ã", "Â", "â€")):
        return _cleanup_encoding_artifacts(text)

    fixed = _fix_latin_mojibake(text)
    if fixed is not None:
        return _cleanup_encoding_artifacts(_fix_mojibake_pairs(fixed))

    fixed_lines: list[str] = []
    for line in text.split("\n"):
        if "Ã" not in line and "Â" not in line and "â€" not in line:
            fixed_lines.append(line)
            continue

        fixed_line = _fix_latin_mojibake(line)
        if fixed_line is not None:
            fixed_lines.append(fixed_line)
            continue

        parts: list[str] = []
        buffer: list[str] = []
        for char in line:
            if ord(char) <= 255:
                buffer.append(char)
                continue
            if buffer:
                chunk = _fix_latin_mojibake("".join(buffer))
                parts.append(chunk if chunk is not None else _fix_mojibake_pairs("".join(buffer)))
                buffer = []
            parts.append(char)
        if buffer:
            chunk = _fix_latin_mojibake("".join(buffer))
            parts.append(chunk if chunk is not None else _fix_mojibake_pairs("".join(buffer)))
        fixed_lines.append("".join(parts))

    return _cleanup_encoding_artifacts(_fix_mojibake_pairs("\n".join(fixed_lines)))


def _cleanup_encoding_artifacts(text: str) -> str:
    for broken, fixed in (
        ("\u00c3\u201c", "Ó"),
        ("\u00c3\u201d", "Ó"),
        ("\u00c3\u0161", "Ú"),
        ("\u00c3\u2030", "É"),
    ):
        text = text.replace(broken, fixed)
    text = text.replace("\u00c2\u00a0", " ")
    text = re.sub(r"\u00c2(?=\s)", "", text)
    return text


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _strip_references(text: str) -> str:
    for marker in (
        "Jurisprudencia Vigencia",
        "Leyes y Sentencias",
        "Ver la Constit",
        "Los datos publicados tienen propósitos",
        "Los datos publicados tienen propÃ³sitos",
    ):
        idx = text.find(marker)
        if idx >= 0:
            text = text[:idx]

    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if stripped.startswith("#####"):
            continue
        if stripped.startswith("######"):
            continue
        if stripped.startswith("- Concepto "):
            continue
        if re.match(r"^Modificado (parcialmente )?por ", stripped, re.IGNORECASE):
            continue
        if re.match(r"^Adicionado por ", stripped, re.IGNORECASE):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\(Ver [^)]+\)", "", text, flags=re.IGNORECASE)
    return _clean(text)


def _find_constitution_body(raw: str) -> str:
    for marker in ("DE LOS PRINCIPIOS FUNDAMENTALES", "PREAMBULO"):
        idx = raw.find(marker)
        if idx >= 0:
            return raw[idx:]
    start = raw.find("CONSTITUCI")
    if start < 0:
        raise ValueError("No se encontró la Constitución en la fuente local.")
    return raw[start:]


def _extract_preamble(raw: str) -> str:
    start = raw.find("PREAMBULO")
    end = raw.find("DE LOS PRINCIPIOS FUNDAMENTALES")
    if start < 0 or end <= start:
        return ""
    return _cleanup_encoding_artifacts(_fix_mojibake_pairs(_clean(raw[start:end])))


def _read_constitution_source() -> str:
    path = CONSTITUCION_FUENTE
    if not path.exists():
        legacy = NORMAS_DIR / "colombia_normas" / "constitucion_fuente.txt"
        if legacy.exists():
            path = legacy
        else:
            raise FileNotFoundError(
                "No hay corpus local. Coloque constitucion_fuente.txt en "
                "data/colombia_normas/ o ejecute _helpers/build_constitucion_corpus.py"
            )
    return _fix_encoding(path.read_text(encoding="utf-8", errors="replace"))


def _chunk_to_article(number: int, chunk: str, current_section: str) -> tuple[dict | None, str]:
    chunk = _strip_references(chunk)
    if not chunk:
        return None, current_section

    body_lines: list[str] = []
    for line in chunk.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        norm_line = _normalize(stripped)
        if (
            len(stripped) < 120
            and stripped == stripped.upper()
            and any(
                word in norm_line
                for word in ("titulo", "capitulo", "de los", "de las", "disposiciones")
            )
        ):
            current_section = _cleanup_encoding_artifacts(_fix_mojibake_pairs(stripped)).title()
            continue
        body_lines.append(stripped)

    text = _cleanup_encoding_artifacts(_fix_mojibake_pairs(_clean(" ".join(body_lines))))
    if not text or len(text) < 20:
        return None, current_section

    return (
        {
            "numero": number,
            "seccion": current_section,
            "texto": text,
            "norma": "Constitución Política de Colombia",
            "norma_id": "cp1991",
        },
        current_section,
    )


def _parse_constitution(raw: str) -> dict:
    raw = _fix_encoding(raw)
    preamble = _extract_preamble(raw)
    body = _find_constitution_body(raw)
    stop_markers = (
        "INSTRUMENTOS INTERNACIONALES",
        "INSTRUMENTOS INTERNACIONALES Y",
        "TRATADOS INTERNACIONALES",
    )
    for marker in stop_markers:
        idx = body.find(marker)
        if idx > 0:
            body = body[:idx]
            break

    parts = ARTICLE_SPLIT.split(body)
    articles_by_num: dict[int, dict] = {}
    current_section = "Disposiciones generales"

    for idx in range(1, len(parts), 2):
        number = int(parts[idx])
        article, current_section = _chunk_to_article(number, parts[idx + 1], current_section)
        if not article:
            continue

        existing = articles_by_num.get(number)
        if existing is None or len(article["texto"]) > len(existing["texto"]):
            articles_by_num[number] = article

    articles = sorted(articles_by_num.values(), key=lambda item: item["numero"])
    sections: list[dict] = []
    for article in articles:
        section_name = article["seccion"]
        if not sections or sections[-1]["nombre"] != section_name:
            sections.append({"nombre": section_name, "articulos": []})
        sections[-1]["articulos"].append(article["numero"])

    return {
        "_version": CORPUS_VERSION,
        "id": "cp1991",
        "nombre": "Constitución Política de Colombia",
        "anio": 1991,
        "preambulo": preamble[:2000] if preamble else "",
        "secciones": sections,
        "articulos": articles,
    }


def _ensure_constitution_json() -> dict:
    if CONSTITUCION_JSON.exists():
        data = json.loads(CONSTITUCION_JSON.read_text(encoding="utf-8"))
        if data.get("_version") == CORPUS_VERSION:
            return data

    corpus = _parse_constitution(_read_constitution_source())
    NORMAS_DIR.mkdir(parents=True, exist_ok=True)
    CONSTITUCION_JSON.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return corpus


def load_norma(norma_id: str) -> dict:
    if norma_id == "cp1991":
        return _ensure_constitution_json()
    if norma_id in EMBEDDED_NORMAS:
        return EMBEDDED_NORMAS[norma_id]
    raise KeyError(f"Norma no disponible: {norma_id}")


def list_normas() -> list[dict]:
    return NORMAS_CATALOGO


def get_article(norma_id: str, numero: int) -> dict | None:
    norma = load_norma(norma_id)
    for article in norma.get("articulos", []):
        if int(article.get("numero", -1)) == int(numero):
            return article
    return None


def search_articles(norma_id: str, query: str, *, limit: int = 40) -> list[dict]:
    query = _normalize(query.strip())
    if not query:
        return []
    norma = load_norma(norma_id)
    results: list[dict] = []

    if query.isdigit():
        article = get_article(norma_id, int(query))
        return [article] if article else []

    for article in norma.get("articulos", []):
        haystack = _normalize(
            f"{article.get('numero', '')} {article.get('seccion', '')} {article.get('texto', '')}"
        )
        if query in haystack:
            results.append(article)
        if len(results) >= limit:
            break
    return results


def list_sections(norma_id: str) -> list[dict]:
    norma = load_norma(norma_id)
    return norma.get("secciones", [])


def format_article_text(article: dict) -> str:
    header = f"Artículo {article.get('numero', '')}. {article.get('norma', '')}"
    section = article.get("seccion")
    if section:
        header += f"\nSección: {section}"
    return f"{header}\n\n{article.get('texto', '').strip()}"


def export_articles_markdown(articles: list[dict]) -> str:
    blocks = [format_article_text(article) for article in articles]
    return "\n\n---\n\n".join(blocks)
