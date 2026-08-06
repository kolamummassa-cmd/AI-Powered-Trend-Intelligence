from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RawSignalData:
    """What every adapter hands back, regardless of platform. Adapters
    translate whatever shape their source API returns into this before
    it ever touches the database — the ingestion pipeline (apps.trends)
    never needs to know TikTok's JSON looks nothing like an RSS entry.
    """

    external_id: str
    title: str
    url: str = ""
    summary: str = ""
    published_at: datetime | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


class TrendSourceAdapter(ABC):
    """Base class for every platform integration.

    Adding a new platform means writing one subclass and registering
    it — nothing else in the ingestion pipeline changes. `config` is
    whatever that Platform row's JSON config holds (e.g. an RSS feed
    URL, a subreddit name); adapters should treat it as read-only.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def fetch_signals(self) -> list[RawSignalData]:
        """Fetch whatever is currently available from the source. Should
        raise on hard failures (auth, network) — the calling task
        decides how to log/retry, adapters don't swallow errors."""
        raise NotImplementedError


_ADAPTER_REGISTRY: dict[str, type[TrendSourceAdapter]] = {}


def register_adapter(slug: str):
    """Class decorator: `@register_adapter("google-trends")`."""

    def decorator(cls: type[TrendSourceAdapter]) -> type[TrendSourceAdapter]:
        _ADAPTER_REGISTRY[slug] = cls
        return cls

    return decorator


def get_adapter(slug: str, config: dict[str, Any] | None = None) -> TrendSourceAdapter:
    try:
        adapter_cls = _ADAPTER_REGISTRY[slug]
    except KeyError:
        raise ValueError(
            f"No adapter registered for '{slug}'. Available: {sorted(_ADAPTER_REGISTRY)}"
        )
    return adapter_cls(config)


def available_adapter_slugs() -> list[str]:
    return sorted(_ADAPTER_REGISTRY)
