"""Opt-in canary for the configured real LLM provider; it never touches the database."""

import os

import pytest

from app.character.models import Character
from app.core.config import get_settings
from app.foreshadow.models import Foreshadow
from app.llm.client import LLMClient
from app.llm.schemas import ChapterGeneration, ChapterOutline, WorldCreationDraftPayload
from app.narrative.service import build_generation_messages, build_outline_messages
from app.world.models import World


pytestmark = pytest.mark.real_llm


_REQUIRED_OPT_INS = {
    "RUN_REAL_LLM_CANARY": "1",
    "LLM_CANARY_ACK_COST": "1",
}
_PLACEHOLDER_VALUES = {"test-key", "test-model"}


def _canary_enabled() -> bool:
    return all(os.getenv(name) == value for name, value in _REQUIRED_OPT_INS.items())


@pytest.mark.parametrize(
    ('run_canary', 'ack_cost', 'expected'),
    [
        (None, None, False),
        ('1', None, False),
        (None, '1', False),
        ('true', '1', False),
        ('1', 'true', False),
        ('1', '1', True),
    ],
)
def test_real_llm_canary_requires_both_exact_opt_ins(
    monkeypatch: pytest.MonkeyPatch,
    run_canary: str | None,
    ack_cost: str | None,
    expected: bool,
) -> None:
    for name, value in (
        ('RUN_REAL_LLM_CANARY', run_canary),
        ('LLM_CANARY_ACK_COST', ack_cost),
    ):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)

    assert _canary_enabled() is expected


@pytest.mark.skipif(
    not _canary_enabled(),
    reason="requires RUN_REAL_LLM_CANARY=1 and LLM_CANARY_ACK_COST=1",
)
def test_real_provider_generates_valid_world_creation_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    """Call the configured provider once with a small fictional world premise."""
    monkeypatch.setenv("LLM_MOCK", "false")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        base_url = str(settings.llm_base_url).rstrip("/").casefold()

        assert settings.llm_mock is False
        assert "example.test" not in base_url
        assert settings.llm_api_key.strip().casefold() not in _PLACEHOLDER_VALUES
        assert settings.llm_model.strip().casefold() not in _PLACEHOLDER_VALUES

        result = LLMClient(settings=settings).generate_world_creation_draft(
            [
                {
                    "role": "user",
                    "content": "Create a tiny fictional clockwork island mystery.",
                }
            ]
        )

        assert isinstance(result, WorldCreationDraftPayload)
        assert result.first_chapter_goal.strip()
        assert isinstance(result.draft, dict)
        for field in ("title", "genre_template", "truth_canon"):
            assert isinstance(result.draft.get(field), str)
            assert result.draft[field].strip()
    finally:
        get_settings.cache_clear()


@pytest.mark.skipif(
    not _canary_enabled(),
    reason="requires RUN_REAL_LLM_CANARY=1 and LLM_CANARY_ACK_COST=1",
)
def test_real_provider_generates_outline_then_chapter_from_in_memory_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise production chapter prompts without creating a database engine or session."""
    world = World(
        id=901,
        owner_id=1,
        title="雾港钟楼",
        genre_template="都市奇幻悬疑",
        truth_canon="雾港每逢雨夜，钟楼会交还一段被偷走的记忆。",
        tone_profile={"style": "克制悬疑", "pacing": "紧凑", "theme": "信任"},
        world_version=1,
    )
    characters = [
        Character(
            id=101,
            world_id=world.id,
            name="林雾",
            role_type="protagonist",
            public_profile={"identity": "修表学徒"},
            hidden_traits={"secret": "她丢失了昨夜的记忆"},
            destiny_flag="听钟者",
            current_goals=["在午夜前找回记忆"],
        ),
        Character(
            id=102,
            world_id=world.id,
            name="周砚",
            role_type="watchman",
            public_profile={"identity": "钟楼守夜人"},
            hidden_traits={"secret": "他知道记忆藏处"},
            destiny_flag="守钟人",
            current_goals=["阻止钟楼停摆"],
        ),
    ]
    foreshadows = [
        Foreshadow(
            id=201,
            world_id=world.id,
            title="裂纹银表",
            description="林雾的银表在雨声中倒转一分钟。",
            foreshadow_type="artifact_clue",
            status="planted",
            urgency_level=5,
            related_character_ids=[101, 102],
            expected_resolution_window="第1章",
        ),
    ]
    chapter_goal = "首章让林雾发现裂纹银表倒转，并向周砚追问失忆真相。"
    execution_context = {
        "next_chapter_number": 1,
        "recommended_pov": {"name": "林雾"},
        "priority_characters": [{"name": "林雾", "reason": "首章主视角"}],
        "priority_foreshadows": [{"title": "裂纹银表", "urgency_level": 5, "reason": "首章推进"}],
    }
    character_names = {character.name for character in characters}
    character_ids = {character.id for character in characters}
    foreshadow_ids = {foreshadow.id for foreshadow in foreshadows}

    monkeypatch.setenv("LLM_MOCK", "false")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        base_url = str(settings.llm_base_url).rstrip("/").casefold()

        assert settings.llm_mock is False
        assert "example.test" not in base_url
        assert settings.llm_api_key.strip().casefold() not in _PLACEHOLDER_VALUES
        assert settings.llm_model.strip().casefold() not in _PLACEHOLDER_VALUES

        client = LLMClient(settings=settings)
        outline = client.generate_outline(
            build_outline_messages(
                world,
                characters,
                foreshadows,
                chapter_goal,
                execution_context=execution_context,
            )
        )

        assert isinstance(outline, ChapterOutline)
        assert outline.pov_suggestion in character_names
        assert outline.beats
        assert all(beat.pov_character in character_names for beat in outline.beats)

        chapter = client.generate_chapter(
            build_generation_messages(
                world,
                characters,
                foreshadows,
                chapter_goal,
                outline_beats=[beat.model_dump() for beat in outline.beats],
                outline_context=outline.model_dump(exclude={"beats"}),
                execution_context=execution_context,
            )
        )

        assert isinstance(chapter, ChapterGeneration)
        assert chapter.draft_content.strip()
        assert all(change.character_id in character_ids for change in chapter.proposed_character_changes)
        assert all(change.foreshadow_id in foreshadow_ids for change in chapter.proposed_foreshadow_changes)

        expected_checks = {
            "background",
            "protagonist_identity",
            "motivation",
            "personality_evidence_plan",
            "conflict_goal",
            "locked_pov",
        }
        paragraphs = chapter.draft_content.split("\n\n")
        assert len(chapter.opening_evidence) == 6
        assert {evidence.check for evidence in chapter.opening_evidence} == expected_checks
        for evidence in chapter.opening_evidence:
            assert evidence.paragraph_index < len(paragraphs)
            assert evidence.quote in paragraphs[evidence.paragraph_index]
    finally:
        get_settings.cache_clear()
