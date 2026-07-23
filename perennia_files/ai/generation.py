from ..exceptions import ProcessingError
from .interface import AIProvider


def generate(provider: AIProvider, text: str, instruction: str) -> str:
    try:
        return provider.generate(text, instruction)
    except NotImplementedError:
        raise
    except Exception as exc:
        raise ProcessingError("Content generation failed.") from exc
