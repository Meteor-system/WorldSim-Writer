# MVP14 Custom World / Genre Template Creation 1.0 Design

## Goal

Let users create an original world from the UI without relying on the built-in sample world, while preserving the existing sample-world shortcut and keeping all downstream MVP flows compatible: studio generation, approval consistency, foreshadow ledger, and Markdown export.

## Current context

The repository already has a strong foundation for this MVP:

- Backend `POST /worlds` accepts `WorldCreateRequest` with `title`, `genre_template`, `truth_canon`, `tone_profile`, and `starter_assets`.
- Backend `POST /worlds/from-template` creates the built-in sample world.
- Backend creates `World`, `Character`, `CharacterRelation`, `Foreshadow`, current projection JSON fields, and initial `ForeshadowEvent` rows.
- Frontend `WorldCreationForm` already supports editable genre presets, starter characters, optional relations, and optional foreshadows.

MVP14 should harden and complete this existing path rather than create a new parallel API or rewrite the creation UI.

## Recommended approach

Use the existing `POST /worlds` custom creation endpoint as the canonical API, add missing governance and validation, and add an explicit sample-world shortcut to the frontend creation screen.

This is the best default because it minimizes architectural churn, keeps backend/frontend types aligned, and focuses MVP14 on the real missing product guarantees: visible `WORLD_CREATED` history, stricter invalid-reference validation, clear frontend error display, and preserving one-click sample creation.

## Alternatives considered

### A. Add a separate custom-world endpoint

Example: `POST /worlds/custom`. This would be explicit, but it duplicates the existing `POST /worlds` contract and creates unnecessary API branching.

### B. Replace the current form with a multi-step wizard

A wizard could improve onboarding, but the current creation form already supports the required fields. A full rewrite would increase UI risk without improving backend guarantees.

### C. Keep existing implementation unchanged

The current implementation is close, but not complete for MVP14 because it lacks initial `WORLD_CREATED` event history and a visible one-click sample-world option in the creation UI.

## Backend design

### API surface

Keep:

```http
POST /worlds
POST /worlds/from-template
```

`POST /worlds` remains the custom-world creation API. `POST /worlds/from-template` remains the built-in sample shortcut.

### Request contract

Use existing `WorldCreateRequest`:

```json
{
  "title": "群星边境",
  "genre_template": "sci_fi",
  "truth_canon": "人类边境殖民地依赖一座濒临失控的跃迁灯塔...",
  "tone_profile": {
    "style": "冷峻太空歌剧",
    "pacing": "高压悬疑"
  },
  "starter_assets": {
    "characters": [
      {
        "name": "许砚",
        "role_type": "protagonist",
        "status": "active",
        "public_profile": { "identity": "灯塔维修工程师" },
        "hidden_traits": { "secret": "曾篡改灯塔事故日志" },
        "destiny_flag": "灯塔核心密钥持有者",
        "current_goals": ["查明灯塔异常脉冲来源"]
      }
    ],
    "relations": [
      {
        "source_index": 0,
        "target_index": 1,
        "relation_type": "mutual_suspicion",
        "intensity": 3,
        "visibility": "private"
      }
    ],
    "foreshadows": [
      {
        "title": "黑匣子脉冲",
        "description": "废弃黑匣子收到来自未来的求救信号。",
        "foreshadow_type": "signal_clue",
        "status": "planted",
        "urgency_level": 4,
        "related_character_indexes": [0],
        "expected_resolution_window": "第3-5章"
      }
    ]
  }
}
```

### Validation rules

Backend validation should reject invalid data before committing world state:

- `title`, `genre_template`, and `truth_canon` must be non-blank.
- At least one starter character is required.
- Starter character `name` and `role_type` must be non-blank.
- Relation `source_index` and `target_index` must reference existing starter characters.
- Relation `source_index` and `target_index` must not be the same character.
- Relation `intensity` must be in `1..5`.
- Foreshadow related character indexes must reference existing starter characters.
- Foreshadow `urgency_level` must be in `1..5`.
- Foreshadow status must be one of `planted`, `advanced`, `resolved`, `expired`.

Existing error behavior should stay simple and deterministic. Pydantic validation can return normal `422` errors for field constraints. Custom starter index validation should continue returning `422` with clear details like `INVALID_CHARACTER_INDEX` or `INVALID_RELATION_SELF_REFERENCE`.

### Persistence behavior

Creation initializes:

- `World`
- `Character`
- `CharacterRelation`
- `Foreshadow`
- `ForeshadowEvent` for starter foreshadows
- current projection JSON fields
- a formal `EventLog` row with:
  - `event_type`: `WORLD_CREATED`
  - `source_type`: `world_creation`
  - `world_version_before`: `0`
  - `world_version_after`: `1`
  - payload summary containing starter counts and world title

This event makes new worlds visible in recent events, timeline queries, and Markdown export timeline.

## Frontend design

### Creation screen

Keep the existing `WorldCreationForm` as the custom world creator. It already supports:

- genre preset selection;
- title and genre label editing;
- truth canon editing;
- tone profile editing;
- starter character editing;
- optional starter relations;
- optional starter foreshadows.

Add a separate sample-world shortcut button near the top or submit area:

```text
创建内置示例世界
```

Behavior:

- Custom form submit calls `createWorld(payload)`.
- Sample shortcut calls new frontend helper `createSampleWorld()` mapped to `POST /worlds/from-template`.
- Both load the created world overview and enter the normal World overview flow.
- Backend validation errors surface in the existing `WorldPage` error area.

### Validation display

Use existing API error formatting. When backend rejects invalid starter asset references or invalid fields, the creation page should display the error text and keep the user on the form.

Frontend should avoid generating invalid references through normal UI interactions:

- relation selectors are based on starter character indexes;
- removing a character remaps/drops affected relations;
- foreshadow character checkboxes are based on current starter characters;
- urgency inputs use min/max `1..5`.

## Compatibility expectations

A custom-created world must work with existing MVP flows:

- World overview displays canon, characters, relations, foreshadows, recent `WORLD_CREATED` event.
- Studio can create a draft from the custom world.
- Approval consistency still runs against current projections.
- Foreshadow ledger can load starter foreshadows.
- Markdown export includes custom world canon, characters, relations, foreshadows, approved chapters, and `WORLD_CREATED` timeline event.
- Sample world creation remains available and tested.

## Testing strategy

Backend TDD:

- Add tests that custom world creation writes a `WORLD_CREATED` event and exposes it through overview/events/export timeline.
- Add tests that invalid relation self-reference is rejected and does not create a world.
- Add tests that invalid relation intensity and foreshadow status/urgency are rejected.
- Keep existing tests for invalid relation and foreshadow character indexes.
- Add a smoke test that a custom-created world can create a draft using a fake LLM.

Frontend TDD:

- Add `createSampleWorld()` API helper test.
- Add `WorldCreationForm` tests for custom payload submission and sample shortcut.
- Add `WorldPage` test proving sample shortcut calls sample API and then loads overview.
- Add `WorldPage` test proving backend validation error is displayed on creation failure.
- Keep existing World overview / manager tests green.

## Non-goals

MVP14 does not implement:

- template marketplace;
- multi-template management;
- AI-generated full world setup;
- Markdown/Obsidian reverse import;
- complex multi-world switching UI;
- complex schema editor;
- cloud template storage;
- paid templates or plugin ecosystem;
- push to remote git.

## Inline self-review

- Placeholder scan: no TBD/TODO placeholders remain.
- Scope check: this is a focused hardening/completion pass for the existing custom world creation path.
- Compatibility: existing `POST /worlds` and `POST /worlds/from-template` remain; sample creation is preserved.
- Canon invariant: creation initializes formal world state, while later generated drafts still only propose changes until approval.
- Ambiguity resolved: MVP14 uses the existing creation API and form; it does not introduce a separate template marketplace or AI world generator.
