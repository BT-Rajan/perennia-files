from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Single interface every AI backend must implement. Swappable without
    touching any application-facing file API. Keep this the only abstraction."""

    @abstractmethod
    def extract_text(self, data: bytes, mime_type: str) -> str:
        """Extracts text content from a supported document (PDF, DOCX, TXT)."""
        raise NotImplementedError

    @abstractmethod
    def ocr(self, data: bytes, mime_type: str) -> str:
        """Runs OCR on an image or scanned document."""
        raise NotImplementedError

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Produces a summary of the given extracted text."""
        raise NotImplementedError

    @abstractmethod
    def answer_question(self, text: str, question: str) -> str:
        """Answers a question grounded strictly in the given extracted text."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, text: str, instruction: str) -> str:
        """Generates new content derived from the source text and an instruction."""
        raise NotImplementedError
