from ..exceptions import ProcessingError
from .interface import AIProvider


def answer_question(provider: AIProvider, text: str, question: str) -> str:
    try:
        return provider.answer_question(text, question)
    except NotImplementedError:
        raise
    except Exception as exc:
        raise ProcessingError("Question answering failed.") from exc
