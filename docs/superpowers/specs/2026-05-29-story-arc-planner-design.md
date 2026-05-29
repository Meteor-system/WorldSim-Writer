# Story Arc Planner Design

## Summary

Add a Story Arc Planner feature that generates and persists a 10-chapter story arc for a world. The planner uses the current world canon, characters, and foreshadows to produce chapter-level guidance. The frontend displays the generated arc on the world overview page and uses it to prefill the Studio chapter goal for the next unapproved chapter.

## Goals

- Add `POST /worlds/{world_id}/story-arc` to generate a 10-chapter arc.
- Persist the latest generated arc on the world record so it survives refreshes and re-entry.
- Return story arc data from the world overview API.
- Display the arc in warm manuscript-style cards on `WorldPage.tsx`.
- Prefill `StudioPage.tsx` chapter goal with the next arc chapter summary, where next chapter is `approved_chapter_count + 1`.
- Preserve the writing-loop invariant: generated planning data does not change formal world state or event history; only approved chapters commit world-state changes.

## Non-goals

- Story arc history or version browsing.
- Editing story arc chapters in the UI.
- Treating story arc generation as a formal event log entry.
- Planning beyond the first 10 chapters.
- Multi-world selection changes.

## Backend design

### Data model

Add a JSONB field to `World`:

```py
story_arc: list[dict]
```

The default value is an empty list. An Alembic migration will add `story_arc` to the `worlds` table with an empty-array default for existing worlds.

Each story arc item has this shape:

```json
{
  "chapter_number": 1,
  "title": "章节标题",
  "summary": "1-2句章节摘要",
  "core_conflict": "本章核心冲突",
  "pov_suggestion": "建议POV",
  "foreshadow_hints": ["伏笔tag"]
}
```

### API

Add:

```http
POST /worlds/{world_id}/story-arc
```

The endpoint:

1. Requires authenticated ownership of the world.
2. Loads the world, characters, foreshadows, and approved chapter count.
3. Builds Story Arc Planner LLM messages.
4. Calls `LLMClient.generate_story_arc()`.
5. Validates that the model response is exactly 10 ordered chapters.
6. Writes the validated array to `world.story_arc`, replacing any previous arc.
7. Returns:

```json
{
  "world_id": 1,
  "story_arc": []
}
```

Add `story_arc` and `approved_chapter_count` to `GET /worlds/{world_id}/overview`.

### Module placement

Keep the route in `backend/app/world/router.py` because the URL and data ownership are world-scoped. Put Story Arc Planner helpers in a small `backend/app/world/story_arc.py` module to avoid growing `world/service.py` unnecessarily. `world/service.py` can expose or delegate the API-facing function if that matches existing import patterns.

## LLM design

### Schemas

Add `StoryArcChapter` and a root-array parser in `backend/app/llm/schemas.py`. The response must be a JSON array, not a wrapped object.

Validation rules:

- Top-level payload is an array.
- Array length is exactly 10.
- `chapter_number` values are exactly `1..10` in order.
- Required string fields are present and non-blank.
- `foreshadow_hints` is present and is a list of strings; it may be empty.

### Prompt

Add `build_story_arc_messages(world, characters, foreshadows, approved_chapter_count)`.

The system prompt states that the model is WorldSim-Writer's Story Arc Planner and must return only a legal JSON array with exactly 10 objects. Each object must contain only:

- `chapter_number`
- `title`
- `summary`
- `core_conflict`
- `pov_suggestion`
- `foreshadow_hints`

The prompt also instructs:

- `summary` must be 1-2 sentences.
- `foreshadow_hints` should use input foreshadow titles or types as tags.
- The model must not output Markdown, code fences, explanations, or an extra wrapper object.

The user message includes `truth_canon`, `genre_template`, `tone_profile`, characters, foreshadows, and approved chapter count.

### Mock mode

Add `MOCK_STORY_ARC` to `backend/app/llm/client.py` and return it from `LLMClient.generate_story_arc()` when `client.mock` is true. The mock response must always contain 10 valid chapters and should be plausible for the sample world.

### Error mapping

Use the same model error mapping pattern as narrative generation:

- timeout -> `504 MODEL_TIMEOUT`
- invalid JSON/schema -> `502 MODEL_RESPONSE_INVALID`
- request failure -> `502 MODEL_REQUEST_FAILED`

## Frontend design

### Types and client

Add these frontend types:

```ts
export type StoryArcChapter = {
  chapter_number: number;
  title: string;
  summary: string;
  core_conflict: string;
  pov_suggestion: string;
  foreshadow_hints: string[];
};

export type StoryArcResponse = {
  world_id: number;
  story_arc: StoryArcChapter[];
};
```

Extend `WorldOverview` with:

```ts
story_arc: StoryArcChapter[];
approved_chapter_count: number;
```

Add `generateStoryArc(worldId)` to `frontend/src/api/client.ts`.

### WorldPage

In the overview tab:

- Add a button near the existing `进入创作台` action.
- Use `生成故事大纲` when no arc exists and `重新生成故事大纲` when an arc exists.
- Disable the button while the request is in flight and show `规划中...`.
- On success, update local `world.story_arc` state from the response.
- On failure, show `paper-error` without clearing the existing arc.

Display the arc as a list of manuscript-style cards. Each card shows:

- `第 N 章 · title`
- `summary`
- `core_conflict`
- `pov_suggestion`
- `foreshadow_hints` as small warm-tone pill tags

If no story arc exists, show a short empty-state note: generating an arc will also help prefill the Studio chapter goal.

### StudioPage

On entry, if no chapter has been created and the local `goal` is empty:

1. Compute `nextChapterNumber = world.approved_chapter_count + 1`.
2. Find the story arc item with that `chapter_number`.
3. If it exists, set `goal` to its `summary`.

The user can edit the textarea before creating a chapter. After chapter creation, the existing disabled behavior remains.

If `nextChapterNumber` is greater than 10, do not prefill.

## State consistency

Story arc generation is planning metadata. It does not increment `world_version` and does not write `EventLog` entries. Formal world state and event history still change only when a draft is approved.

Regenerating an arc overwrites the previous `world.story_arc`. This is intentional so the user can refresh planning after character or foreshadow changes.

## Testing plan

### Backend

Add tests for:

1. Prompt content and parser validation:
   - Prompt includes canon, characters, foreshadows, strict JSON array requirement, and exactly 10 chapters.
   - Parser rejects non-arrays, wrong lengths, and non-sequential chapter numbers.
2. Successful API generation:
   - Registered user creates a sample world.
   - Fake/mock LLM returns 10 chapters.
   - `POST /worlds/{id}/story-arc` returns 200 and 10 items.
   - `GET /worlds/{id}/overview` returns the same `story_arc` and `approved_chapter_count: 0`.
3. Overwrite behavior:
   - A second generation replaces the previous arc rather than appending.
4. Error mapping:
   - Runtime failure maps to `502 MODEL_REQUEST_FAILED`.
   - Invalid schema maps to `502 MODEL_RESPONSE_INVALID`.
5. Approved chapter count:
   - Approved chapters count.
   - Drafting/reviewing/rejected chapters do not count.

### Frontend and verification

Use build and manual verification:

- `npm run build`
- Generate an arc from the world overview page.
- Confirm 10 cards display.
- Regenerate and confirm the display updates.
- Enter Studio and confirm the goal is prefilled with chapter 1 summary.
- Approve a chapter, return to Studio, and confirm the goal is prefilled with chapter 2 summary.

Run backend tests with the repository's recommended command:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v'
```
