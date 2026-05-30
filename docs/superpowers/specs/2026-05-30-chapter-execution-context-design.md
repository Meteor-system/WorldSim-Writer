# MVP #4: Chapter Execution Context 1.0 Design

Date: 2026-05-30
Status: Approved design
Branch: `feat/mvp-4-chapter-execution-context`

## 1. Goal

Make the Narrative Control Center's next-chapter preparation signals part of the actual chapter execution pipeline.

MVP #3 passed only a suggested goal string from `WorldPage` into `StudioPage`. MVP #4 upgrades that handoff into a structured, frozen `ChapterExecutionContext` that records why a chapter session was launched, displays that evidence in Studio/review/history, and gives the backend prompt builder a compact execution contract for outline and draft generation.

This milestone does not change formal world-state governance. Execution context is an input snapshot for chapter creation and draft generation; only explicit chapter approval may mutate formal world state or write approval events.

## 2. Scope

### In scope

- Define frontend/backend `ChapterExecutionContext` contract.
- Define frontend `StudioLaunchContext` for `WorldPage -> App -> StudioPage` launch state.
- Build a structured execution context from `NextChapterPrepResponse` instead of passing only a goal string.
- Preserve manual Studio entry by creating a manual context when no NCC context is provided.
- Freeze execution context on `Chapter` at chapter creation time.
- Copy `Chapter.execution_context` to `ChapterDraft.execution_context` when creating draft versions.
- Let outline and writer prompt builders use a compact human-readable execution context summary.
- Extend direct draft creation to accept optional execution context for compatibility with the existing `/worlds/{world_id}/chapters/draft` route.
- Expose execution context in chapter session, draft, chapter, and chapter history detail responses.
- Display launch context summary in `StudioPage` as read-only reference material.
- Display frozen context snapshots in draft/review/history details.
- Add backend and frontend tests for context handoff, persistence, prompt use, and invariants.

### Out of scope

- Snapshot Browser.
- Continuity Dashboard.
- Automatic chapter creation from Next Chapter Prep.
- Automatic approval.
- Complex execution context editor.
- Rollback or context revision UI.
- Heavy referential validation of every ID embedded in the context snapshot.
- Allowing `POST /chapters/{chapter_id}/write` to accept or replace execution context.

## 3. Existing Context

Relevant current state:

- `frontend/src/world/NextChapterPrepPanel.tsx` displays rich next-chapter prep data but currently calls callbacks with `prep.suggested_goal` only.
- `frontend/src/world/WorldPage.tsx` stores `selectedNextGoal` and passes `{ initialChapterGoal }` to `App`.
- `frontend/src/App.tsx` stores `studioInitialGoal` and passes it to `StudioPage`.
- `frontend/src/studio/StudioPage.tsx` initializes `goal` from `initialChapterGoal`, then creates a chapter through `createChapter(world.id, { chapter_goal, title })`.
- `backend/app/narrative/schemas.py` has `CreateChapterRequest` with `chapter_goal` and optional `title` only.
- `backend/app/narrative/models.py` has `Chapter.chapter_goal`, `Chapter.outline_beats`, `Chapter.outline_context`, `Chapter.critique_report`, but no `execution_context`.
- `ChapterDraft` stores generated content metadata, proposed changes, and source world version, but no `execution_context`.
- `build_outline_messages()` and `build_generation_messages()` do not use NCC execution context today.

## 4. Architecture

The MVP #4 data flow is:

```text
NextChapterPrepResponse
        ↓
WorldPage builds ChapterExecutionContext
        ↓
StudioLaunchContext
        ↓
App stores launch context
        ↓
StudioPage displays context summary
        ↓
POST /worlds/{world_id}/chapters
        ↓
Chapter.execution_context is frozen
        ↓
outline/write prompts use Chapter.execution_context
        ↓
ChapterDraft.execution_context copies Chapter.execution_context
        ↓
draft/review/history UI displays frozen context snapshot
```

The key design choice is that context freezes at chapter creation time. Later outline and write steps inherit the same chapter-level context. If a user wants a different context, a future milestone can add a context revision flow or a new execution session. MVP #4 intentionally avoids a complex context editor.

## 5. Execution Context Contract

### 5.1 Frontend type

Add to `frontend/src/api/types.ts`:

```ts
export type ChapterExecutionContext = {
  source: 'next_chapter_prep' | 'manual';
  source_world_version: number;
  next_chapter_number: number | null;
  goal: string;
  recommended_pov: {
    character_id: number | null;
    name: string | null;
  };
  source_signals: string[];
  priority_characters: Array<{
    character_id: number;
    name: string;
    role_type: string;
    status: string;
    reason: string;
  }>;
  priority_foreshadows: Array<{
    foreshadow_id: number;
    title: string;
    status: string;
    urgency_level: number;
    reason: string;
  }>;
  progression_hints: Array<{
    hint_type: string;
    priority: string;
    title: string;
    rationale: string;
    suggested_next_beat: string;
    related_character_ids: number[];
    related_foreshadow_ids: number[];
    can_seed_next_chapter_goal: boolean;
  }>;
  continuity_warnings: Array<{
    severity: string;
    category: string;
    message: string;
    related_character_ids: number[];
    related_foreshadow_ids: number[];
  }>;
  recent_events: Array<{
    id: number;
    event_type: string;
    world_version_before: number;
    world_version_after: number;
    created_at: string;
  }>;
};

export type StudioLaunchContext = {
  initialChapterGoal?: string;
  executionContext?: ChapterExecutionContext;
};
```

`initialChapterGoal` is still useful because it initializes the editable Studio textarea. `executionContext.goal` records the launch evidence. Before creating a chapter, Studio normalizes the context so the frozen `execution_context.goal` matches the final edited `chapter_goal`.

### 5.2 Backend schema

Add Pydantic schemas to `backend/app/narrative/schemas.py`:

```py
class ExecutionContextPov(BaseModel):
    character_id: int | None = None
    name: str | None = None


class ExecutionContextPriorityCharacter(BaseModel):
    character_id: int
    name: str
    role_type: str
    status: str
    reason: str


class ExecutionContextPriorityForeshadow(BaseModel):
    foreshadow_id: int
    title: str
    status: str
    urgency_level: int
    reason: str


class ExecutionContextProgressionHint(BaseModel):
    hint_type: str
    priority: str
    title: str
    rationale: str
    suggested_next_beat: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)
    can_seed_next_chapter_goal: bool = False


class ExecutionContextContinuityWarning(BaseModel):
    severity: str
    category: str
    message: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)


class ExecutionContextRecentEvent(BaseModel):
    id: int
    event_type: str
    world_version_before: int
    world_version_after: int
    created_at: str


class ChapterExecutionContext(BaseModel):
    source: Literal['next_chapter_prep', 'manual'] = 'manual'
    source_world_version: int
    next_chapter_number: int | None = None
    goal: str = Field(min_length=3)
    recommended_pov: ExecutionContextPov = Field(default_factory=ExecutionContextPov)
    source_signals: list[str] = Field(default_factory=list)
    priority_characters: list[ExecutionContextPriorityCharacter] = Field(default_factory=list)
    priority_foreshadows: list[ExecutionContextPriorityForeshadow] = Field(default_factory=list)
    progression_hints: list[ExecutionContextProgressionHint] = Field(default_factory=list)
    continuity_warnings: list[ExecutionContextContinuityWarning] = Field(default_factory=list)
    recent_events: list[ExecutionContextRecentEvent] = Field(default_factory=list)
```

Extend request schemas:

```py
class DraftRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)
    execution_context: ChapterExecutionContext | None = None


class CreateChapterRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)
    title: str | None = None
    execution_context: ChapterExecutionContext | None = None
```

Extend response schemas with:

```py
execution_context: dict | None = None
```

for:

- `DraftResponse`
- `ChapterPipelineResponse`
- `ChapterResponse`

Also expose `execution_context` in chapter history detail responses so the review/history UI can show the frozen basis for a chapter.

## 6. Persistence

Add JSONB columns:

```py
class Chapter(Base):
    execution_context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class ChapterDraft(Base):
    execution_context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
```

Add Alembic migration:

```py
op.add_column(
    'chapters',
    sa.Column('execution_context', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
)
op.add_column(
    'chapter_drafts',
    sa.Column('execution_context', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
)
op.alter_column('chapters', 'execution_context', server_default=None)
op.alter_column('chapter_drafts', 'execution_context', server_default=None)
```

SQLite tests should continue to use the repository's existing JSONB compilation shim.

## 7. Backend Service Design

### 7.1 Normalize context at chapter creation

Update `create_chapter_session()` to accept optional `execution_context`.

Rules:

1. Load and authorize the world with `require_owned_world()`.
2. If context is provided, serialize it through Pydantic with `model_dump(mode='json')`.
3. If context is omitted, build a manual context from the current world and `chapter_goal`.
4. Always set `context['goal'] = chapter_goal` before saving so `Chapter.chapter_goal` and `Chapter.execution_context.goal` match.
5. Save the context on `Chapter.execution_context`.
6. Do not write `EventLog` and do not increment `world_version`.

Manual fallback context:

```py
def build_manual_execution_context(world: World, chapter_goal: str, next_chapter_number: int | None) -> dict:
    return {
        'source': 'manual',
        'source_world_version': world.world_version,
        'next_chapter_number': next_chapter_number,
        'goal': chapter_goal,
        'recommended_pov': {'character_id': None, 'name': None},
        'source_signals': ['manual'],
        'priority_characters': [],
        'priority_foreshadows': [],
        'progression_hints': [],
        'continuity_warnings': [],
        'recent_events': [],
    }
```

Derive `next_chapter_number` from approved chapter count plus one rather than relying on lazy relationship length.

### 7.2 Direct draft endpoint

Update `/worlds/{world_id}/chapters/draft` to accept optional `execution_context` through `DraftRequest`.

Rules:

- Normalize or build manual context the same way as chapter session creation.
- Save it to both `Chapter.execution_context` and the generated `ChapterDraft.execution_context`.
- Use it in the generation prompt.
- Preserve existing behavior for callers that send only `chapter_goal`.

### 7.3 Outline prompt

Update `build_outline_messages()` to accept:

```py
execution_context: dict | None = None
```

Use a compact human-readable formatter, not a raw JSON dump. Include:

- source
- recommended POV
- priority characters with reasons
- priority foreshadows with urgency and reasons
- progression hints
- continuity warnings
- recent event summaries

The prompt should state that execution context is guidance for the current chapter and does not itself change formal world state.

### 7.4 Writer prompt

Update `build_generation_messages()` to accept:

```py
execution_context: dict | None = None
```

The user message should include a compact `本章执行上下文` section and instruct the Writer Agent to prioritize:

1. chapter goal
2. recommended POV
3. priority characters
4. priority foreshadows
5. progression hints
6. continuity warnings
7. outline beats

Do not change the model output schema in MVP #4.

### 7.5 Draft versioning

When creating a generated draft from the chapter pipeline, copy:

```py
execution_context=chapter.execution_context
```

When creating edited/stashed/paragraph-revised draft versions through `_create_draft_version()`, copy:

```py
execution_context=previous_draft.execution_context
```

This preserves the original execution basis across draft revisions.

### 7.6 Response payloads

Update `_draft_payload()`:

```py
'execution_context': draft.execution_context or chapter.execution_context,
```

For chapter/session responses, return `chapter.execution_context`.

For chapter history detail, return the latest approved draft execution context if available; otherwise return `chapter.execution_context`.

## 8. Frontend Design

### 8.1 Context helper

Create `frontend/src/world/chapterExecutionContext.ts`.

Responsibilities:

```ts
export function buildExecutionContextFromPrep(prep: NextChapterPrepResponse): ChapterExecutionContext;
export function buildManualExecutionContext(world: WorldOverview, goal: string): ChapterExecutionContext;
export function withEditedGoal(
  context: ChapterExecutionContext | undefined,
  world: WorldOverview,
  goal: string,
): ChapterExecutionContext;
```

`buildExecutionContextFromPrep()` maps the structured fields from `NextChapterPrepResponse` into `ChapterExecutionContext` and sets `source: 'next_chapter_prep'`.

`buildManualExecutionContext()` creates a minimal manual context with `source_signals: ['manual']`.

`withEditedGoal()` returns `{ ...context, goal }` when context exists, or a manual context when it does not.

### 8.2 NextChapterPrepPanel callbacks

Replace string callbacks:

```ts
onUseGoal?: (goal: string) => void;
onEnterStudioWithGoal?: (goal: string) => void;
```

with context callbacks:

```ts
onUseContext?: (context: ChapterExecutionContext) => void;
onEnterStudioWithContext?: (context: ChapterExecutionContext) => void;
```

Button labels stay the same:

- `用作下一章目标`
- `进入创作台并使用此目标`

The behavior changes from sending only `prep.suggested_goal` to sending full `ChapterExecutionContext`.

### 8.3 WorldPage state

Replace:

```ts
const [selectedNextGoal, setSelectedNextGoal] = useState('');
```

with:

```ts
const [selectedExecutionContext, setSelectedExecutionContext] = useState<ChapterExecutionContext | null>(null);
```

The regular Studio button calls:

```ts
onEnterStudio(world, {
  initialChapterGoal: selectedExecutionContext?.goal,
  executionContext: selectedExecutionContext ?? undefined,
});
```

The direct prep button calls:

```ts
onEnterStudio(world, {
  initialChapterGoal: context.goal,
  executionContext: context,
});
```

### 8.4 App state

Replace `studioInitialGoal` with:

```ts
const [studioLaunchContext, setStudioLaunchContext] = useState<StudioLaunchContext>({});
```

`enterStudio()` becomes:

```ts
function enterStudio(world: WorldOverview, context: StudioLaunchContext = {}) {
  setStudioWorld(world);
  setStudioLaunchContext(context);
}
```

Clear `studioLaunchContext` on back and approval to prevent stale context from leaking into later sessions.

### 8.5 StudioPage

Replace `initialChapterGoal` prop with optional `launchContext`:

```ts
type Props = {
  world: WorldOverview;
  launchContext?: StudioLaunchContext;
  onBack: () => void;
  onApproved: (world: WorldOverview) => void;
};
```

Initialize state from launch-time values:

```ts
const [goal, setGoal] = useState(launchContext?.initialChapterGoal ?? '');
const [executionContext] = useState(launchContext?.executionContext);
```

Before creating a chapter:

```ts
const frozenContext = withEditedGoal(executionContext, world, goal);
const created = await createChapterRequest(world.id, {
  chapter_goal: goal,
  title: goal.slice(0, 40),
  execution_context: frozenContext,
});
```

After the backend responds, treat `created.execution_context` as the authoritative frozen context.

### 8.6 Studio UI

Add a read-only sidebar panel titled:

```text
本章执行上下文
```

If launched from NCC, show:

- source label: 下一章准备台
- source world version
- next chapter number
- recommended POV
- priority character names
- priority foreshadow titles
- progression hint count
- continuity warning count

If no context was launched, show:

```text
本章暂无 NCC 执行上下文。创建章节时会根据当前目标生成手动上下文快照。
```

After a chapter is created, show that the backend froze the context:

```text
已冻结执行上下文：next_chapter_prep · v2
```

### 8.7 Draft/review/history UI

When `draft.execution_context` exists, display a read-only section inside the Writer Draft article:

```text
执行上下文快照
```

Show:

- source
- goal
- recommended POV
- priority characters
- priority foreshadows
- progression hints
- continuity warnings

For chapter history detail, render a similar context snapshot if `execution_context` is present.

### 8.8 API client

Change `createChapter()` to accept optional context:

```ts
export function createChapter(
  worldId: number,
  data: {
    chapter_goal: string;
    title?: string;
    execution_context?: ChapterExecutionContext;
  },
) { ... }
```

`writeChapter()` remains unchanged and does not accept context.

## 9. Validation and Authorization

Authorization remains world/chapter ownership based:

- chapter creation uses `require_owned_world()`.
- chapter-scoped actions use `_require_owned_chapter()`.

MVP #4 performs minimal shape validation only:

- `chapter_goal` must be present and at least 3 characters.
- provided `execution_context.goal` must be present and at least 3 characters.
- nested context must match Pydantic schema.

No heavy referential validation is required for embedded character/foreshadow/event IDs because the context is a historical input snapshot, not a formal state mutation. Approval-time mutation validation remains the formal safety boundary.

## 10. Error Handling and Edge Cases

### No NCC context

Studio can still create chapters. Frontend submits a manual context; backend also creates one if omitted.

### User edits goal after launch

Before creating a chapter, Studio normalizes the context with the final edited goal so `Chapter.chapter_goal` and `execution_context.goal` match.

### Source world version mismatch

If an NCC context was built at world version N and the current world is now version N+1, MVP #4 does not reject creation. `Chapter.base_world_version` records the actual creation base version; `execution_context.source_world_version` records the context source version.

### Write request attempts to pass context

`POST /chapters/{chapter_id}/write` does not accept or replace context. It uses the frozen `Chapter.execution_context`.

### Draft revisions

Edited/stashed/paragraph revised drafts keep the previous draft's execution context.

## 11. Testing Strategy

### 11.1 Backend tests

Add/update tests under `backend/tests/`.

Coverage:

1. `CreateChapterRequest` accepts optional `execution_context`.
2. `create_chapter_session` saves context to `Chapter.execution_context`.
3. omitted context creates manual context.
4. `generate_chapter_outline` includes execution context in outline prompt.
5. `write_chapter_from_outline` includes execution context in generation prompt.
6. generated `ChapterDraft` copies `Chapter.execution_context`.
7. direct draft endpoint accepts optional `execution_context` and stores it on both Chapter and ChapterDraft.
8. direct draft endpoint without context creates manual context.
9. draft response includes `execution_context`.
10. chapter/session response includes `execution_context`.
11. chapter history detail includes `execution_context`.
12. approval invariant remains unchanged: context creation/generation does not increment `world_version` or write formal events; approval is still required.
13. reject invariant remains unchanged: rejection does not mutate world state.

Useful targeted commands:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_chapter_execution_context.py -v
cd /opt/WorldSim-Writer/backend && pytest tests/test_narrative_approval.py -v
cd /opt/WorldSim-Writer/backend && pytest tests/test_narrative_control_center.py::test_next_chapter_prep_does_not_mutate_world_version_or_write_events -v
```

Full backend regression before final merge:

```bash
cd /opt/WorldSim-Writer/backend && pytest -v
```

### 11.2 Frontend tests

Add/update tests:

- `frontend/src/world/chapterExecutionContext.test.ts`
  - maps `NextChapterPrepResponse` to `ChapterExecutionContext`
  - builds manual context
  - applies edited goal

- `frontend/src/world/NextChapterPrepPanel.test.tsx`
  - callbacks receive full context, not only goal string

- `frontend/src/world/WorldPage.test.tsx`
  - selected prep context is passed to `onEnterStudio`
  - direct enter with prep context passes full `StudioLaunchContext`

- `frontend/src/App.test.tsx` if existing test structure supports it, otherwise keep WorldPage + StudioPage split coverage
  - App stores and passes `StudioLaunchContext`

- `frontend/src/studio/StudioPage.test.tsx`
  - launch context initializes editable goal
  - sidebar shows execution context summary
  - create chapter submits `execution_context` with edited goal
  - draft display shows frozen `execution_context`

- `frontend/src/world/ChapterHistoryPanel.test.tsx`
  - history detail displays `execution_context` snapshot when present

Useful targeted commands:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/chapterExecutionContext.test.ts src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
```

Full frontend regression before final merge:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
cd /opt/WorldSim-Writer/frontend && npm run build
```

## 12. Acceptance Criteria

- `ChapterExecutionContext` and `StudioLaunchContext` are defined in frontend types.
- `NextChapterPrepPanel` callbacks pass full context objects.
- `WorldPage` stores selected execution context, not only selected goal.
- `App` stores and clears `StudioLaunchContext`.
- `StudioPage` initializes the goal from launch context while keeping it editable.
- `StudioPage` displays a read-only execution context summary.
- Creating a chapter sends `execution_context` with the final edited goal.
- Backend freezes context on `Chapter.execution_context` at chapter creation.
- Backend creates manual context if request omits execution context.
- Outline prompt uses frozen chapter execution context.
- Writer prompt uses frozen chapter execution context.
- `writeChapter` does not accept or replace context.
- `ChapterDraft.execution_context` copies `Chapter.execution_context`.
- Draft revisions preserve previous draft context.
- Draft/review/history details expose and display frozen context snapshots.
- Direct draft endpoint supports optional context and preserves backward compatibility.
- Next Chapter Prep remains read-only.
- Creating chapter, generating outline, generating draft, and rejecting drafts do not mutate formal world state.
- Approval remains the only operation that commits generated formal world-state changes.
- Targeted and full backend/frontend tests pass.

## 13. Implementation Process

Follow the user-requested process:

1. Brainstorming.
2. Writing-plans.
3. TDD implementation.

Constraints:

- Do not use dynamic workflows.
- Skip code-review subagent because it is unavailable in this environment due to the 403 plan limit.
- Implement on branch `feat/mvp-4-chapter-execution-context`.
- Commit and merge to `main` after verification.

