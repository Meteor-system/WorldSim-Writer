# MVP #3: Next Chapter Execution Bridge Design

Date: 2026-05-30
Status: Approved design
Branch: `feat/mvp-3-next-chapter-bridge`

## 1. Goal

Close the frontend loop between the Narrative Control Center and the Studio writing flow.

MVP #3 includes two pieces:

1. Mount the already-built `RelationManager` in `WorldPage`.
2. Implement the Next Chapter Execution Bridge:
   - A selected Narrative Control Center next-chapter goal can initialize the Studio chapter goal textarea.
   - `NextChapterPrepPanel` also provides a one-step action to enter Studio with the suggested goal.

This milestone does not add backend state mutation behavior. `next-chapter-prep` remains read-only.

## 2. Scope

### In scope

- Add a `relations` tab to `WorldPage`.
- Render `RelationManager` with existing props:
  - `worldId`
  - `characters`
  - `onChanged`
- Extend frontend state flow:
  - `WorldPage -> App -> StudioPage`
- Add `initialChapterGoal` support to `StudioPage`.
- Keep existing Story Arc fallback when no initial goal is provided.
- Add `进入创作台并使用此目标` to `NextChapterPrepPanel`.
- Ensure existing `用作下一章目标` remains available.
- Add frontend tests for relation tab mounting and goal handoff.
- Run backend regression for next-chapter-prep read-only behavior.
- After implementation, commit and merge into `main`.

### Out of scope

- Backend API changes.
- Automatic chapter creation from Next Chapter Prep.
- Persisting selected next goal to the database.
- Persisting selected next goal to localStorage.
- New routing system.
- Multi-world selection changes.
- Relationship model/API changes.

## 3. Existing Context

Current `WorldPage` tabs:

```ts
type Tab = 'overview' | 'characters' | 'foreshadows';
```

Existing `RelationManager` is implemented in:

```text
frontend/src/components/RelationManager.tsx
```

It already uses:

- `getRelations`
- `createRelation`
- `updateRelation`
- `deleteRelation`

Current `WorldPage` already has local state:

```ts
const [selectedNextGoal, setSelectedNextGoal] = useState('');
```

Current `NextChapterPrepPanel` supports:

```tsx
onUseGoal={setSelectedNextGoal}
```

Current `App` only sends a world into Studio:

```tsx
<WorldPage onEnterStudio={setStudioWorld} />
```

Current `StudioPage` initializes goal as empty:

```tsx
const [goal, setGoal] = useState('');
```

It then falls back to the story arc next chapter summary when `goal` is empty.

## 4. RelationManager Mount Design

Update `WorldPage` tab type:

```ts
type Tab = 'overview' | 'characters' | 'relations' | 'foreshadows';
```

Update tab list:

```ts
const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: '世界概览' },
  { key: 'characters', label: '角色管理' },
  { key: 'relations', label: '关系管理' },
  { key: 'foreshadows', label: '伏笔账本' },
];
```

Render tab:

```tsx
{tab === 'relations' && (
  <RelationManager
    worldId={world.id}
    characters={world.characters}
    onChanged={loadWorld}
  />
)}
```

Behavior:

- Creating, updating, or deleting a relation continues to use existing relation APIs.
- `onChanged={loadWorld}` refreshes `WorldOverview` after relation mutation.
- Existing backend governance remains responsible for:
  - incrementing `world_version`
  - writing `EventLog`
  - refreshing `current_relations`

## 5. Next Chapter Execution Bridge Design

### 5.1 Shared type

Add or inline an options type:

```ts
type EnterStudioOptions = {
  initialChapterGoal?: string;
};
```

The callback shape becomes:

```ts
onEnterStudio: (world: WorldOverview, options?: EnterStudioOptions) => void;
```

This is intentionally small. It only carries the initial chapter goal for MVP #3.

### 5.2 App state flow

`App` should maintain both selected world and initial Studio goal:

```tsx
const [studioWorld, setStudioWorld] = useState<WorldOverview | null>(null);
const [studioInitialGoal, setStudioInitialGoal] = useState('');
```

Add a wrapper:

```tsx
function enterStudio(world: WorldOverview, options?: EnterStudioOptions) {
  setStudioWorld(world);
  setStudioInitialGoal(options?.initialChapterGoal ?? '');
}
```

Pass into `WorldPage`:

```tsx
<WorldPage onEnterStudio={enterStudio} autoFocusTitle={!approvedWorld} />
```

Pass into `StudioPage`:

```tsx
<StudioPage
  world={studioWorld}
  initialChapterGoal={studioInitialGoal}
  onBack={() => {
    setStudioWorld(null);
    setStudioInitialGoal('');
  }}
  onApproved={(world) => {
    setApprovedWorld(world);
    setStudioWorld(null);
    setStudioInitialGoal('');
  }}
/>
```

Clearing `studioInitialGoal` on back/approval prevents stale goals from leaking into later Studio sessions.

### 5.3 WorldPage behavior

The existing top-level `进入创作台` button should use the selected goal if present:

```tsx
<button onClick={() => onEnterStudio(world, { initialChapterGoal: selectedNextGoal || undefined })}>
  进入创作台
</button>
```

This supports the base flow:

1. User clicks `用作下一章目标` in `NextChapterPrepPanel`.
2. `WorldPage` stores the selected goal.
3. User clicks `进入创作台`.
4. `StudioPage` receives the selected goal.

### 5.4 NextChapterPrepPanel enhanced action

Extend `NextChapterPrepPanel` props:

```tsx
type Props = {
  prep: NextChapterPrepResponse | null;
  loading?: boolean;
  error?: string;
  onUseGoal?: (goal: string) => void;
  onEnterStudioWithGoal?: (goal: string) => void;
};
```

Add a second action next to `用作下一章目标`:

```tsx
<button onClick={() => onEnterStudioWithGoal?.(prep.suggested_goal)}>
  进入创作台并使用此目标
</button>
```

Only render this button when:

- `prep` exists
- `onEnterStudioWithGoal` is provided

`WorldPage` passes:

```tsx
<NextChapterPrepPanel
  prep={nextPrep}
  loading={nextPrepLoading}
  error={nextPrepError}
  onUseGoal={setSelectedNextGoal}
  onEnterStudioWithGoal={(goal) => onEnterStudio(world, { initialChapterGoal: goal })}
/>
```

This supports the enhanced flow:

1. User clicks `进入创作台并使用此目标`.
2. `WorldPage` invokes `onEnterStudio(world, { initialChapterGoal: goal })`.
3. `App` stores both world and initial goal.
4. `StudioPage` opens with the textarea pre-filled.

### 5.5 StudioPage initial goal

Update props:

```tsx
type Props = {
  world: WorldOverview;
  initialChapterGoal?: string;
  onBack: () => void;
  onApproved: (world: WorldOverview) => void;
};
```

Initialize goal:

```tsx
const [goal, setGoal] = useState(initialChapterGoal ?? '');
```

Keep existing story arc fallback. It already exits when `goal.trim().length > 0`, so an initial goal will not be overwritten.

## 6. Backend Behavior

No backend API changes are required.

The existing endpoint remains read-only:

```http
GET /worlds/{world_id}/next-chapter-prep
```

The existing invariant remains:

- Next Chapter Prep may read current world state.
- Next Chapter Prep must not increment `world_version`.
- Next Chapter Prep must not write `EventLog`.
- Next Chapter Prep must not create chapters or drafts.

Chapter creation still only occurs when the user explicitly clicks `创建章节` in `StudioPage`.

## 7. Error Handling and Edge Cases

### No selected goal

If `selectedNextGoal` is empty, `WorldPage` enters Studio without `initialChapterGoal`.

`StudioPage` then uses the existing story arc fallback if available.

### Next prep loading or error

When `prep` is `null`, no goal buttons are rendered by `NextChapterPrepPanel`.

Existing loading/error states remain unchanged.

### User edits the goal

The Studio textarea remains editable until a chapter session is created.

Initial goal is only a starting value.

### Back navigation

When the user leaves Studio, `App` clears `studioInitialGoal`.

### Approval

When the user approves a chapter, `App` clears `studioInitialGoal` and returns to `WorldPage` with the existing approval success banner.

## 8. Testing Strategy

### 8.1 RelationManager mount test

Add/update `WorldPage` test coverage:

- render `WorldPage` with a mocked world overview
- verify the `关系管理` tab exists
- click `关系管理`
- verify RelationManager content appears, such as `+ 新增关系` or a loading/empty relation state

Because `RelationManager` calls relation APIs internally, tests should mock API/fetch consistently with existing frontend test patterns.

### 8.2 NextChapterPrepPanel test

Update `frontend/src/world/NextChapterPrepPanel.test.tsx`:

- existing `用作下一章目标` assertion remains
- add `onEnterStudioWithGoal` mock
- assert `进入创作台并使用此目标` renders
- click it
- assert callback receives `prep.suggested_goal`

### 8.3 StudioPage test

Add/update StudioPage test coverage:

- render `StudioPage` with `initialChapterGoal`
- assert `章节目标` textarea has the initial value
- assert it can be edited
- assert story arc fallback does not overwrite the provided value

### 8.4 WorldPage handoff test

Add/update `WorldPage` test coverage:

- when `NextChapterPrepPanel` invokes `onEnterStudioWithGoal`, `WorldPage` calls:
  ```ts
  onEnterStudio(world, { initialChapterGoal: prep.suggested_goal })
  ```
- when the user first clicks `用作下一章目标` and then clicks top-level `进入创作台`, `WorldPage` calls the same shape.

### 8.5 App handoff test

If existing App tests make this practical, add one integration test:

- `WorldPage` enters Studio with options
- `App` passes `initialChapterGoal` into `StudioPage`

If App-level mocking is too brittle, the `WorldPage` handoff test plus `StudioPage` prop test is sufficient for MVP #3.

### 8.6 Backend regression

Run targeted backend test:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_narrative_control_center.py::test_next_chapter_prep_does_not_mutate_world_version_or_write_events -v
```

Also run full backend regression before final commit if time permits:

```bash
cd /opt/WorldSim-Writer/backend && pytest -v
```

## 9. Acceptance Criteria

- `WorldPage` shows a `关系管理` tab.
- The `关系管理` tab renders `RelationManager`.
- `RelationManager` receives current world characters and refreshes overview on changes.
- Clicking `用作下一章目标` stores the suggested goal in `WorldPage`.
- Clicking regular `进入创作台` after selecting a goal opens Studio with the goal pre-filled.
- Clicking `进入创作台并使用此目标` opens Studio directly with the goal pre-filled.
- `StudioPage` accepts `initialChapterGoal`.
- `StudioPage` story arc fallback does not overwrite an explicit initial goal.
- Studio does not automatically create a chapter session from the bridge.
- `next-chapter-prep` backend remains read-only.
- Frontend tests cover the goal handoff path.
- Verification passes:
  - targeted frontend tests
  - full frontend tests
  - frontend build
  - targeted backend read-only regression
  - full backend tests before final merge

## 10. Implementation Commit/Merge Plan

After implementation and verification:

1. Commit on `feat/mvp-3-next-chapter-bridge`.
2. Merge into `main` with a merge commit.
3. Do not use dynamic workflows.
4. Skip code-review subagent because it is unavailable in this environment.
