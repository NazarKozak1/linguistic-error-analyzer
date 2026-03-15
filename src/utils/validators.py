from langdetect import detect, LangDetectException
from src.utils.logger import get_logger

logger = get_logger(__name__)


def is_german(text: str) -> bool:
    """Check if the given text is primarily in German."""
    if len(text.split()) < 2:
        return True

    try:
        lang = detect(text)
        return lang == 'de'
    except LangDetectException as e:
        logger.warning(f"Could not detect language for text: '{text}'. Error: {e}")
        return False