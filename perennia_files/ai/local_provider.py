"""Optional reference implementation of AIProvider for local text extraction.

Requires the 'ai' extras (pypdf, python-docx). Only extract_text is
implemented here — OCR, summarisation, question answering, and generation
require a real model backend and are left for the application to supply
via its own AIProvider implementation (e.g. wrapping the Anthropic API).
"""
import io

from .interface import AIProvider
from ..exceptions import ProcessingError


class LocalDocumentProvider(AIProvider):
    """Extraction-only provider. Does not perform any AI inference."""

    def extract_text(self, data: bytes, mime_type: str) -> str:
        if mime_type == "application/pdf":
            return self._extract_pdf(data)
        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._extract_docx(data)
        if mime_type == "text/plain":
            return data.decode("utf-8", errors="replace")
        raise NotImplementedError(f"No text extractor available for '{mime_type}'.")

    def _extract_pdf(self, data: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ProcessingError(
                "pypdf is required for PDF extraction. Install the 'ai' extra."
            ) from exc
        try:
            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ProcessingError("Failed to extract text from PDF.") from exc

    def _extract_docx(self, data: bytes) -> str:
        try:
            import docx
        except ImportError as exc:
            raise ProcessingError(
                "python-docx is required for DOCX extraction. Install the 'ai' extra."
            ) from exc
        try:
            document = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in document.paragraphs)
        except Exception as exc:
            raise ProcessingError("Failed to extract text from DOCX.") from exc

    def ocr(self, data: bytes, mime_type: str) -> str:
        raise NotImplementedError("OCR requires an AI-backed provider.")

    def summarize(self, text: str) -> str:
        raise NotImplementedError("Summarisation requires an AI-backed provider.")

    def answer_question(self, text: str, question: str) -> str:
        raise NotImplementedError("Question answering requires an AI-backed provider.")

    def generate(self, text: str, instruction: str) -> str:
        raise NotImplementedError("Content generation requires an AI-backed provider.")
