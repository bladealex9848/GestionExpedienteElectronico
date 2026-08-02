from __future__ import annotations

import io
from dataclasses import dataclass

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pdf_compat import PdfReader
from pytesseract import Output

from .models import PageTrace
from .text_utils import clean_text, useful_characters


@dataclass(frozen=True)
class OCRConfig:
    enabled: bool = True
    min_useful_characters: int = 80
    max_ocr_pages: int = 40
    dpi: int = 220
    language: str = "spa"


def preprocess_image(image: Image.Image) -> Image.Image:
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image = ImageEnhance.Contrast(image).enhance(1.6)
    return image


def calculate_ocr_confidence(image: Image.Image, language: str) -> tuple[str, float]:
    data = pytesseract.image_to_data(
        image,
        lang=language,
        config="--oem 3 --psm 6",
        output_type=Output.DICT,
    )

    words: list[str] = []
    confidences: list[float] = []

    for word, confidence in zip(data.get("text", []), data.get("conf", [])):
        word = (word or "").strip()
        try:
            score = float(confidence)
        except (TypeError, ValueError):
            score = -1

        if word:
            words.append(word)
        if score >= 0:
            confidences.append(score)

    text = clean_text(" ".join(words))
    average = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    return text, average


def extract_pdf_pages(
    document_name: str,
    content: bytes,
    config: OCRConfig,
) -> list[PageTrace]:
    reader = PdfReader(io.BytesIO(content))
    results: list[PageTrace] = []

    for page_number, page in enumerate(reader.pages, start=1):
        warnings: list[str] = []

        try:
            digital_text = clean_text(page.extract_text() or "")
        except Exception as error:
            digital_text = ""
            warnings.append(f"Extracción digital falló: {error}")

        digital_chars = useful_characters(digital_text)
        must_ocr = (
            config.enabled
            and digital_chars < config.min_useful_characters
            and page_number <= config.max_ocr_pages
        )

        if not must_ocr:
            if (
                config.enabled
                and digital_chars < config.min_useful_characters
                and page_number > config.max_ocr_pages
            ):
                warnings.append("No se aplicó OCR por el límite máximo configurado.")

            results.append(
                PageTrace(
                    document=document_name,
                    page=page_number,
                    text=digital_text,
                    extraction_method="texto digital",
                    ocr_confidence=None,
                    useful_characters=digital_chars,
                    warnings=warnings,
                )
            )
            continue

        try:
            images = convert_from_bytes(
                content,
                dpi=config.dpi,
                first_page=page_number,
                last_page=page_number,
                grayscale=True,
                thread_count=1,
                fmt="png",
            )

            if not images:
                raise RuntimeError("No se generó imagen para OCR.")

            prepared = preprocess_image(images[0])
            ocr_text, confidence = calculate_ocr_confidence(
                prepared,
                config.language,
            )
            ocr_chars = useful_characters(ocr_text)

            if ocr_chars > digital_chars:
                selected_text = ocr_text
                method = "OCR"
                selected_chars = ocr_chars
            else:
                selected_text = digital_text
                method = "texto digital"
                selected_chars = digital_chars
                warnings.append("El OCR no mejoró el texto digital disponible.")

            results.append(
                PageTrace(
                    document=document_name,
                    page=page_number,
                    text=selected_text,
                    extraction_method=method,
                    ocr_confidence=confidence,
                    useful_characters=selected_chars,
                    warnings=warnings,
                )
            )

        except Exception as error:
            warnings.append(f"OCR falló: {error}")
            results.append(
                PageTrace(
                    document=document_name,
                    page=page_number,
                    text=digital_text,
                    extraction_method="texto digital",
                    ocr_confidence=None,
                    useful_characters=digital_chars,
                    warnings=warnings,
                )
            )

    return results


def quality_label(trace: PageTrace) -> str:
    if trace.extraction_method != "OCR":
        if trace.useful_characters >= 250:
            return "Buena"
        if trace.useful_characters >= 80:
            return "Aceptable"
        return "Baja"

    confidence = trace.ocr_confidence or 0.0

    if confidence >= 85 and trace.useful_characters >= 150:
        return "Buena"
    if confidence >= 65 and trace.useful_characters >= 80:
        return "Aceptable"
    return "Baja"


def quality_score(trace: PageTrace) -> float:
    return {
        "Buena": 1.0,
        "Aceptable": 0.7,
        "Baja": 0.35,
    }[quality_label(trace)]
