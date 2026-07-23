from ..exceptions import ProcessingError
from .interface import AIProvider


def ocr(provider: AIProvider, data: bytes, mime_type: str) -> str:
    try:
        return provider.ocr(data, mime_type)
    except NotImplementedError:
        raise
    except Exception as exc:
        raise ProcessingError("OCR processing failed.") from exc
