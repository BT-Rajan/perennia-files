from ..exceptions import ProcessingError
from .interface import AIProvider


def summarize(provider: AIProvider, text: str) -> str:
    try:
        return provider.summarize(text)
    except NotImplementedError:
        raise
    except Exception as exc:
        raise ProcessingError("Summarisation failed.") from exc
