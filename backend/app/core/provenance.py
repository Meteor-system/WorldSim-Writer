"""Pure helpers for stable provenance metadata."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


_REFERENCE_TYPES = {"profile", "chapter_spec", "knowledge"}
_CONTENT_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _require_positive_int(value: Any, name: str) -> int:
    """Validate an integer version/bound without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name}_MUST_BE_POSITIVE_INTEGER")
    return value


def _json_default(value: Any) -> Any:
    """Serialize Pydantic models without mutating them."""
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    dict_method = getattr(value, "dict", None)
    if callable(dict_method):
        return dict_method()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def canonical_json_hash(value: Any) -> str:
    """Return the SHA-256 hash of a stable, UTF-8 JSON representation."""
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_source_world_version(
    source_world_version: int, current_world_version: int
) -> None:
    """Ensure provenance was produced from the current positive world version."""
    _require_positive_int(source_world_version, "SOURCE_WORLD_VERSION")
    _require_positive_int(current_world_version, "CURRENT_WORLD_VERSION")
    if source_world_version != current_world_version:
        raise ValueError("WORLD_VERSION_MISMATCH")


def bounded_text(value: Any, max_chars: int) -> tuple[str, bool]:
    """Convert text safely and truncate it to at most ``max_chars`` characters."""
    _require_positive_int(max_chars, "MAX_CHARS")
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        text = str(value)
    return text[:max_chars], len(text) > max_chars


def bounded_items(items: Any, max_items: int) -> tuple[list[Any], bool]:
    """Copy at most ``max_items`` items, reporting whether any were dropped."""
    _require_positive_int(max_items, "MAX_ITEMS")
    source = [] if items is None else list(items)
    return list(source[:max_items]), len(source) > max_items


def build_provenance_reference(
    reference_type: str,
    reference_id: str,
    version: int,
    content_hash: str,
    source_world_version: int,
) -> dict[str, Any]:
    """Build validated reference metadata without retaining source content."""
    if reference_type not in _REFERENCE_TYPES:
        raise ValueError("INVALID_REFERENCE_TYPE")
    if not isinstance(reference_id, str) or not reference_id.strip():
        raise ValueError("REFERENCE_ID_REQUIRED")
    _require_positive_int(version, "VERSION")
    _require_positive_int(source_world_version, "SOURCE_WORLD_VERSION")
    if not isinstance(content_hash, str) or not _CONTENT_HASH_PATTERN.fullmatch(content_hash):
        raise ValueError("INVALID_CONTENT_HASH")
    return {
        "reference_type": reference_type,
        "reference_id": reference_id,
        "version": version,
        "content_hash": content_hash,
        "source_world_version": source_world_version,
    }
