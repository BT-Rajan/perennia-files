from ..exceptions import ProcessingError
from .interface import AIProvider


def extract_text(provider: AIProvider, data: bytes, mime_type: str) -> str:
    try:
        return provider.extract_text(data, mime_type)
    except NotImplementedError:
        raise
    except Exception as exc:
        raise ProcessingError("Text extraction failed.") from exc
