import copy

import pytest

from app.core.provenance import (
    bounded_items,
    bounded_text,
    build_provenance_reference,
    canonical_json_hash,
    validate_source_world_version,
)


def test_canonical_json_hash_is_stable_for_mapping_order():
    first = {"alpha": 1, "nested": {"x": "世界", "y": [1, 2]}}
    second = {"nested": {"y": [1, 2], "x": "世界"}, "alpha": 1}

    assert canonical_json_hash(first) == canonical_json_hash(second)


def test_canonical_json_hash_changes_when_semantics_change():
    assert canonical_json_hash({"value": 1}) != canonical_json_hash({"value": 2})


def test_canonical_json_hash_does_not_mutate_input():
    value = {"items": ["a", "b"]}
    original = copy.deepcopy(value)

    canonical_json_hash(value)

    assert value == original


def test_validate_source_world_version():
    assert validate_source_world_version(3, 3) is None

    with pytest.raises(ValueError, match="^WORLD_VERSION_MISMATCH$"):
        validate_source_world_version(2, 3)

    with pytest.raises(ValueError):
        validate_source_world_version(0, 1)


def test_bounded_text_truncates_and_handles_empty_or_non_string_values():
    assert bounded_text("abcdef", 3) == ("abc", True)
    assert bounded_text("abc", 3) == ("abc", False)
    assert bounded_text(None, 3) == ("", False)
    assert bounded_text(12345, 3) == ("123", True)

    with pytest.raises(ValueError):
        bounded_text("text", 0)


def test_bounded_items_truncates_without_modifying_input():
    items = ["one", "two", "three"]
    result, truncated = bounded_items(items, 2)

    assert result == ["one", "two"]
    assert truncated is True
    assert result is not items
    assert items == ["one", "two", "three"]
    assert bounded_items(None, 2) == ([], False)


def test_bounded_items_rejects_invalid_bound():
    with pytest.raises(ValueError):
        bounded_items([1], 0)


def test_build_provenance_reference_validates_and_omits_extra_content():
    content_hash = "a" * 64
    reference = build_provenance_reference(
        "profile", "profile-1", 2, content_hash, 4
    )

    assert reference == {
        "reference_type": "profile",
        "reference_id": "profile-1",
        "version": 2,
        "content_hash": content_hash,
        "source_world_version": 4,
    }
    assert "content" not in reference
    assert "extra" not in reference


@pytest.mark.parametrize("reference_type", ["profile", "chapter_spec", "knowledge"])
def test_build_provenance_reference_accepts_supported_types(reference_type):
    assert build_provenance_reference(reference_type, "id", 1, "b" * 64, 1)[
        "reference_type"
    ] == reference_type


@pytest.mark.parametrize(
    "kwargs",
    [
        {"reference_type": "unknown", "reference_id": "id", "version": 1, "content_hash": "a" * 64, "source_world_version": 1},
        {"reference_type": "profile", "reference_id": "", "version": 1, "content_hash": "a" * 64, "source_world_version": 1},
        {"reference_type": "profile", "reference_id": "id", "version": 0, "content_hash": "a" * 64, "source_world_version": 1},
        {"reference_type": "profile", "reference_id": "id", "version": 1, "content_hash": "A" * 64, "source_world_version": 1},
        {"reference_type": "profile", "reference_id": "id", "version": 1, "content_hash": "short", "source_world_version": 1},
        {"reference_type": "profile", "reference_id": "id", "version": 1, "content_hash": "a" * 64, "source_world_version": 0},
    ],
)
def test_build_provenance_reference_rejects_invalid_values(kwargs):
    with pytest.raises(ValueError):
        build_provenance_reference(**kwargs)
