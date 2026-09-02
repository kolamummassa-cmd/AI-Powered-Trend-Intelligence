import re

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_INSTRUCTION_MARKERS = re.compile(
    r"\b(ignore\s+(all|any|the)?\s*(previous|prior)\s+instructions?|system\s+prompt|"
    r"developer\s+message|you\s+are\s+chatgpt|act\s+as)\b",
    re.IGNORECASE,
)


def sanitize_untrusted_source_text(value: str, limit: int) -> str:
    """Keep source evidence readable while neutralising prompt-like markup."""
    text = _CONTROL_CHARS.sub(" ", str(value or ""))
    text = _INSTRUCTION_MARKERS.sub("[redacted instruction-like text]", text)
    return " ".join(text.split())[:limit]
