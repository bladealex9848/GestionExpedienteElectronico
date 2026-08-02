"""Compatibilidad entre pypdf y PyPDF2."""

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.errors import EmptyFileError, PdfReadError, PdfStreamError
except ModuleNotFoundError:
    from PyPDF2 import PdfReader, PdfWriter

    try:
        from PyPDF2.errors import PdfReadError, PdfStreamError
    except ImportError:
        PdfReadError = Exception
        PdfStreamError = Exception
    EmptyFileError = PdfReadError

__all__ = ["PdfReader", "PdfWriter", "PdfReadError", "EmptyFileError", "PdfStreamError"]
