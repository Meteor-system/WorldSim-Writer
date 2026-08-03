import json
import logging
import re
import unicodedata
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, field_validator

parse_logger = logging.getLogger('worldsim.llm.parse')

_DIAGNOSTIC_SNIPPET_LIMIT = 400


def _shape_snippet(text: str) -> str:
    """Return a bounded, irreversible character-class shape for diagnostics.

    Every input character is represented only by a category and run length;
    this intentionally preserves no syntax, whitespace, Unicode symbol, or
    control character from the input.
    """
    parts: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            category = "WS"
            predicate = str.isspace
        elif unicodedata.category(char).startswith("C"):
            category = "CTRL"
            predicate = lambda value: unicodedata.category(value).startswith("C")
        elif "一" <= char <= "鿿":
            category = "CJK"
            predicate = lambda value: "一" <= value <= "鿿"
        elif char.isascii() and char.isalpha():
            category = "ASCII"
            predicate = lambda value: value.isascii() and value.isalpha()
        elif char.isdigit():
            category = "DIGIT"
            predicate = str.isdigit
        elif unicodedata.category(char).startswith("P"):
            category = "PUNCT"
            predicate = lambda value: unicodedata.category(value).startswith("P")
        elif unicodedata.category(char).startswith("S"):
            category = "SYMBOL"
            predicate = lambda value: unicodedata.category(value).startswith("S")
        else:
            category = "TEXT"
            predicate = lambda value: not (
                value.isspace()
                or unicodedata.category(value).startswith("C")
                or "一" <= value <= "鿿"
                or (value.isascii() and value.isalpha())
                or value.isdigit()
                or unicodedata.category(value).startswith(("P", "S"))
            )
        end = index + 1
        while end < len(text) and predicate(text[end]):
            end += 1
        parts.append(f"[{category}:{end - index}]")
        index = end

    if not parts:
        return ""
    if sum(map(len, parts)) <= _DIAGNOSTIC_SNIPPET_LIMIT:
        return "".join(parts)

    omitted_count = len(parts)
    omission = f"[OMITTED:{omitted_count}]"
    if len(omission) > _DIAGNOSTIC_SNIPPET_LIMIT:
        omission = "[OMITTED:0]"
    available = _DIAGNOSTIC_SNIPPET_LIMIT - len(omission)

    # Select whole tokens from both ends.  The shaped representation is never
    # sliced, so truncation cannot expose a partial marker.
    left: list[str] = []
    right: list[str] = []
    left_index = 0
    right_index = len(parts)
    left_budget = available // 2
    while left_index < right_index and len(left) < len(parts):
        token = parts[left_index]
        if len("".join(left)) + len(token) > left_budget:
            break
        left.append(token)
        left_index += 1
    right_budget = available - len("".join(left))
    while left_index < right_index:
        token = parts[right_index - 1]
        if len("".join(right)) + len(token) > right_budget:
            break
        right.append(token)
        right_index -= 1

    # If one side's first token is too large for its share, use any remaining
    # capacity on the other side while keeping the two selections disjoint.
    remaining = available - len("".join(left)) - len("".join(right))
    while left_index < right_index:
        token = parts[left_index]
        if len(token) > remaining:
            break
        left.append(token)
        left_index += 1
        remaining -= len(token)
    while left_index < right_index:
        token = parts[right_index - 1]
        if len(token) > remaining:
            break
        right.append(token)
        right_index -= 1
        remaining -= len(token)

    return "".join(left) + omission + "".join(reversed(right))


def _log_parse_failure(stage: str, raw_text: str, reason: str) -> None:
    """Record an irreversible shape of an invalid model response."""
    stripped = raw_text.strip()
    payload = {
        "event": "llm.parse_failed",
        "stage": stage,
        "reason": reason,
        "raw_length": len(raw_text),
        "fence_count": stripped.count("```"),
        "starts_with": _shape_snippet(stripped[:1]),
        "ends_with": _shape_snippet(stripped[-1:]),
        "snippet": _shape_snippet(stripped),
    }
    parse_logger.warning(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


class _JsonLoadError(ValueError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class BeatCard(BaseModel):
    beat_id: str
    summary: str
    pov_character: str | None = None
    location: str | None = None
    emotional_arc: str
    key_dialogue_hints: list[str]


class OpeningContract(BaseModel):
    background: str
    protagonist_identity: str
    motivation: str
    personality_evidence_plan: str
    conflict_goal: str
    locked_pov: str
    # 零认知开篇锚点：默认空串，保持与既有大纲数据和既有 fixture 的向后兼容。
    # 这三项只参与质量报告的 advisories，不进入 OPENING_CHECKS 硬门禁，
    # 因此不加入下方 validate_required_text（空串在该校验器下会被拒绝）。
    inciting_incident: str = ''
    prior_state: str = ''
    grounded_emotion: str = ''

    @field_validator(
        'background',
        'protagonist_identity',
        'motivation',
        'personality_evidence_plan',
        'conflict_goal',
        'locked_pov',
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError('must not be blank')
        return stripped


class OpeningEvidence(BaseModel):
    check: Literal[
        'background',
        'protagonist_identity',
        'motivation',
        'personality_evidence_plan',
        'conflict_goal',
        'locked_pov',
    ]
    paragraph_index: int = Field(ge=0)
    quote: str = Field(min_length=1)


class OpeningEvidenceRepair(BaseModel):
    model_config = ConfigDict(extra='forbid')

    opening_evidence: list[OpeningEvidence]


class ChapterOutline(BaseModel):
    beats: list[BeatCard]
    core_conflict: str
    pov_suggestion: str | None = None
    pacing: str
    role_skill_targets: list[str]
    opening_contract: OpeningContract | None = None


class StoryArcChapter(BaseModel):
    chapter_number: int = Field(ge=1, le=10)
    title: str
    summary: str
    core_conflict: str
    pov_suggestion: str
    foreshadow_hints: list[str] = Field(default_factory=list)

    @field_validator('title', 'summary', 'core_conflict', 'pov_suggestion')
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError('must not be blank')
        return stripped

    @field_validator('foreshadow_hints')
    @classmethod
    def validate_foreshadow_hints(cls, value: list[str]) -> list[str]:
        hints = [hint.strip() for hint in value if hint.strip()]
        if len(hints) != len(value):
            raise ValueError('foreshadow hints must not be blank')
        return hints


class WorldCreationDraftPayload(BaseModel):
    draft: dict[str, Any]
    first_chapter_goal: str
    generation_notes: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    followup_questions: list[str] = Field(default_factory=list)

    @field_validator('first_chapter_goal')
    @classmethod
    def validate_first_chapter_goal(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError('must not be blank')
        return stripped

    @field_validator('followup_questions')
    @classmethod
    def validate_followup_questions(cls, value: list[str]) -> list[str]:
        return [question.strip() for question in value if question.strip()][:3]


WORLD_CREATION_DRAFT_JSON_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'draft': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'title': {'type': 'string'},
                'genre_template': {'type': 'string'},
                'truth_canon': {'type': 'string'},
                'tone_profile': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'style': {'type': 'string'},
                        'pacing': {'type': 'string'},
                        'theme': {'type': 'string'},
                    },
                    'required': ['style', 'pacing', 'theme'],
                },
                'starter_assets': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'characters': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'additionalProperties': False,
                                'properties': {
                                    'name': {'type': 'string'},
                                    'role_type': {'type': 'string'},
                                    'status': {'type': 'string'},
                                    'public_profile': {
                                        'type': 'object',
                                        'additionalProperties': False,
                                        'properties': {
                                            'identity': {'type': 'string'},
                                            'skill': {'type': 'string'},
                                            'public_motivation': {'type': 'string'},
                                        },
                                        'required': ['identity', 'skill', 'public_motivation'],
                                    },
                                    'hidden_traits': {
                                        'type': 'object',
                                        'additionalProperties': False,
                                        'properties': {
                                            'secret': {'type': 'string'},
                                            'fear': {'type': 'string'},
                                            'private_agenda': {'type': 'string'},
                                            'weakness': {'type': 'string'},
                                        },
                                        'required': ['secret', 'fear', 'private_agenda', 'weakness'],
                                    },
                                    'destiny_flag': {'type': 'string'},
                                    'current_goals': {'type': 'array', 'items': {'type': 'string'}},
                                },
                                'required': [
                                    'name', 'role_type', 'status', 'public_profile', 'hidden_traits',
                                    'destiny_flag', 'current_goals',
                                ],
                            },
                        },
                        'relations': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'additionalProperties': False,
                                'properties': {
                                    'source_index': {'type': 'integer'},
                                    'target_index': {'type': 'integer'},
                                    'relation_type': {'type': 'string'},
                                    'intensity': {'type': 'integer', 'enum': [1, 2, 3, 4, 5]},
                                    'visibility': {'type': 'string'},
                                },
                                'required': ['source_index', 'target_index', 'relation_type', 'intensity', 'visibility'],
                            },
                        },
                        'foreshadows': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'additionalProperties': False,
                                'properties': {
                                    'title': {'type': 'string'},
                                    'description': {'type': 'string'},
                                    'foreshadow_type': {'type': 'string'},
                                    'status': {'type': 'string', 'enum': ['planted', 'advanced', 'resolved', 'expired']},
                                    'urgency_level': {'type': 'integer', 'enum': [1, 2, 3, 4, 5]},
                                    'related_character_indexes': {'type': 'array', 'items': {'type': 'integer'}},
                                    'expected_resolution_window': {'type': 'string'},
                                },
                                'required': [
                                    'title', 'description', 'foreshadow_type', 'status', 'urgency_level',
                                    'related_character_indexes', 'expected_resolution_window',
                                ],
                            },
                        },
                    },
                    'required': ['characters', 'relations', 'foreshadows'],
                },
            },
            'required': ['title', 'genre_template', 'truth_canon', 'tone_profile', 'starter_assets'],
        },
        'first_chapter_goal': {'type': 'string'},
        'generation_notes': {'type': 'array', 'items': {'type': 'string'}},
        'safety_notes': {'type': 'array', 'items': {'type': 'string'}},
        'followup_questions': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['draft', 'first_chapter_goal', 'generation_notes', 'safety_notes', 'followup_questions'],
}


class CritiqueIssue(BaseModel):
    category: str
    severity: str
    message: str


class CritiqueReport(BaseModel):
    score: int = Field(ge=0, le=100)
    issues: list[CritiqueIssue]
    suggestions: list[str]
    consistency_check: dict[str, Any]


class LiteraryCriticIssue(BaseModel):
    severity: str
    dimension: str
    message: str
    paragraph_index: int | None = None
    suggested_action: str | None = None


class LiteraryCriticDimension(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str
    issues: list[LiteraryCriticIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class LiteraryCriticReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    summary: str
    dimensions: dict[str, LiteraryCriticDimension]
    issues: list[LiteraryCriticIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class CharacterArcEntry(BaseModel):
    character_id: int
    name: str
    role_type: str | None = None
    current_status: str | None = None
    current_goals: list[str] = Field(default_factory=list)
    presence_level: Literal['absent', 'mentioned', 'supporting', 'major']
    arc_stage: Literal['setup', 'pressure', 'choice', 'consequence', 'growth', 'regression', 'resolution', 'unknown']
    chapter_function: str
    observed_shift: str
    proposed_state_change: dict[str, Any] | None = None
    continuity_risk: Literal['none', 'low', 'medium', 'high']
    risk_reason: str | None = None
    suggested_revision: str | None = None
    next_chapter_setup: str | None = None


class RelationshipProgressionNote(BaseModel):
    source_character_id: int
    target_character_id: int
    source_name: str
    target_name: str
    relation_type: str
    current_intensity: int | None = None
    visibility: str | None = None
    chapter_shift: str
    progression_hint: str
    risk_level: Literal['none', 'low', 'medium', 'high']
    risk_reason: str | None = None


class ChapterProgressionHint(BaseModel):
    hint_type: Literal['character', 'relationship', 'foreshadow', 'plot']
    priority: Literal['low', 'medium', 'high']
    title: str
    rationale: str
    suggested_next_beat: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)
    can_seed_next_chapter_goal: bool = False


class CharacterArcReport(BaseModel):
    summary: str
    character_arcs: list[CharacterArcEntry] = Field(default_factory=list)
    relationship_notes: list[RelationshipProgressionNote] = Field(default_factory=list)
    progression_hints: list[ChapterProgressionHint] = Field(default_factory=list)


class ProposedCharacterChange(BaseModel):
    character_id: int
    status: str | None = None
    current_goals: list[str] | None = None


class ProposedForeshadowChange(BaseModel):
    foreshadow_id: int
    status: str
    description_note: str | None = None


class ChapterGeneration(BaseModel):
    title: str
    draft_content: str
    context_summary: str
    review_hints: list[str]
    proposed_character_changes: list[ProposedCharacterChange]
    proposed_foreshadow_changes: list[ProposedForeshadowChange]
    opening_evidence: list[OpeningEvidence] = Field(default_factory=list)


class ParagraphRevision(BaseModel):
    paragraph: str = Field(min_length=1)
    revision_note: str | None = None

    @field_validator('paragraph')
    @classmethod
    def validate_paragraph(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError('must not be blank')
        if re.search(r'\r?\n[ \t]*\r?\n', stripped):
            raise ValueError('must contain exactly one paragraph')
        return stripped


def _load_json(raw_text: str) -> Any:
    text = raw_text.strip()
    if not text:
        raise _JsonLoadError("empty_response")

    try:
        return json.loads(text)
    except (TypeError, json.JSONDecodeError):
        fence_match = re.fullmatch(r"```(?:json|JSON)?\n(.+?)\n```", text, flags=re.DOTALL)
        if not fence_match:
            raise _JsonLoadError("not_bare_json_and_no_single_json_fence") from None
        try:
            return json.loads(fence_match.group(1))
        except (TypeError, json.JSONDecodeError):
            raise _JsonLoadError("fenced_body_not_valid_json") from None


def _parse_model_response(raw_text: str, stage: str, validator: Any) -> Any:
    """Parse one model response, logging exactly once for every failure."""
    try:
        return validator(_load_json(raw_text))
    except _JsonLoadError as error:
        reason = error.reason
        cause = error
    except ValidationError as error:
        reason = f"schema_validation: {error.error_count()} errors"
        cause = error
    except ValueError as error:
        reason = "semantic_validation"
        cause = error
    _log_parse_failure(stage, raw_text, reason)
    raise ValueError("MODEL_RESPONSE_INVALID") from cause


def parse_chapter_generation(raw_text: str) -> ChapterGeneration:
    return _parse_model_response(raw_text, "chapter_generation", ChapterGeneration.model_validate)


def parse_opening_evidence_repair(raw_text: str) -> OpeningEvidenceRepair:
    return _parse_model_response(raw_text, "opening_evidence_repair", OpeningEvidenceRepair.model_validate)


def parse_paragraph_revision(raw_text: str) -> ParagraphRevision:
    return _parse_model_response(raw_text, "paragraph_revision", ParagraphRevision.model_validate)


def parse_chapter_outline(raw_text: str) -> ChapterOutline:
    return _parse_model_response(raw_text, "chapter_outline", ChapterOutline.model_validate)


def parse_world_creation_draft(raw_text: str) -> WorldCreationDraftPayload:
    return _parse_model_response(raw_text, "world_creation_draft", WorldCreationDraftPayload.model_validate)


def _validate_story_arc(chapters: list[StoryArcChapter]) -> list[StoryArcChapter]:
    if len(chapters) != 10:
        raise ValueError("MODEL_RESPONSE_INVALID")
    if [chapter.chapter_number for chapter in chapters] != list(range(1, 11)):
        raise ValueError("MODEL_RESPONSE_INVALID")
    return chapters


def parse_story_arc(raw_text: str) -> list[StoryArcChapter]:
    def validate(payload: Any) -> list[StoryArcChapter]:
        if not isinstance(payload, list):
            raise ValueError("MODEL_RESPONSE_INVALID")
        return _validate_story_arc(TypeAdapter(list[StoryArcChapter]).validate_python(payload))

    return _parse_model_response(raw_text, "story_arc", validate)


def parse_critique_report(raw_text: str) -> CritiqueReport:
    return _parse_model_response(raw_text, "critique_report", CritiqueReport.model_validate)


def parse_literary_critic_report(raw_text: str) -> LiteraryCriticReport:
    return _parse_model_response(raw_text, "literary_critic_report", LiteraryCriticReport.model_validate)


def parse_character_arc_report(raw_text: str) -> CharacterArcReport:
    return _parse_model_response(raw_text, "character_arc_report", CharacterArcReport.model_validate)
