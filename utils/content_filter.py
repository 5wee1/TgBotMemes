import hashlib
import re
import logging

logger = logging.getLogger(__name__)

# Patterns that are always blocked regardless of context
_BLOCKED_PATTERNS = [
    r"\bcsam\b",
    r"\bchild\s+porn",
    r"\bchild\s+sex",
    r"\bдетское\s+порно",
    r"\bдетская\s+порнография",
    r"\bнасилие\s+над\s+детьми",
    r"\buberkill\s+children",
    # Violence instructions
    r"\bкак\s+(убить|взорвать|отравить)\b",
    r"\bhow\s+to\s+(kill|bomb|poison|murder)\b",
    r"\bбомба\s+своими\s+руками\b",
    r"\bhomemade\s+(bomb|explosive)",
    r"\bизготовление\s+оружия\b",
    # Terrorism/extremism
    r"\b(isis|игил|игиш|даиш)\b",
    r"\bтеррористическ",
    # Doxxing
    r"\bличные\s+данные\b.{0,30}\b(слить|опубликовать)\b",
    r"\bdox(x)?(ing)?\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]


def is_blocked(text: str) -> bool:
    for pattern in _COMPILED:
        if pattern.search(text):
            _log_block(text)
            return True
    return False


def _log_block(text: str):
    short = text[:40].replace("\n", " ")
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:12]
    logger.warning("blocked_request hash=%s snippet=%r", text_hash, short)
