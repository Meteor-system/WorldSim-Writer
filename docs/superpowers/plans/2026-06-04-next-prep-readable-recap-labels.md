# Next Chapter Prep Readable Recap Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw backend-style labels in Next Chapter Prep recap with low-cognitive Chinese labels.

**Architecture:** Frontend-only display update in `NextChapterPrepPanel`. Use existing `labelStatus`, `labelEventType`, and `labelWorldVersion` helpers from `displayLabels.ts`; keep import reference cards, execution-context construction, and Studio handoff unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
  - Update the main render test first.
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
  - Import display label helpers and use them for role/status/event recap text.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Next Chapter Prep recap hides raw backend labels

**Files:**
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `renders next chapter prep signals and uses suggested goal callback`, replace raw-label assertions:

```ts
expect(screen.getByText('林砚 · protagonist')).toBeInTheDocument();
expect(screen.getByText('裂纹玉佩 · advanced · urgency 4')).toBeInTheDocument();
expect(screen.getByText('chapter_approved · 世界 1 → 2')).toBeInTheDocument();
```

with Chinese label assertions:

```ts
expect(screen.getByText('林砚 · 主角')).toBeInTheDocument();
expect(screen.getByText('裂纹玉佩 · 推进中 · 紧迫度 4')).toBeInTheDocument();
expect(screen.getByText('章节写入正史 · 世界第 1 版 → 第 2 版')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('林砚 · protagonist');
expect(document.body).not.toHaveTextContent('裂纹玉佩 · advanced · urgency 4');
expect(document.body).not.toHaveTextContent('chapter_approved · 世界 1 → 2');
```

Keep existing import-reference safety assertions.

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "renders next chapter prep"
```

Expected: FAIL because the panel still renders raw role/status/event labels.

- [ ] **Step 3: Write minimal implementation**

In `NextChapterPrepPanel.tsx`, import display helpers:

```ts
import { labelEventType, labelStatus, labelWorldVersion } from './displayLabels';
```

Update priority character label:

```tsx
<p className="font-bold text-[#3b2511]">{character.name} · {labelStatus(character.role_type)}</p>
```

Update priority foreshadow label:

```tsx
<p className="font-bold text-[#3b2511]">{foreshadow.title} · {labelStatus(foreshadow.status)} · 紧迫度 {foreshadow.urgency_level}</p>
```

Update recent event label:

```tsx
{labelEventType(event.event_type)} · 世界{labelWorldVersion(event.world_version_before)} → {labelWorldVersion(event.world_version_after)}
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx
```

Expected: PASS.

---

### Task 2: Final verification and commit

- [ ] **Step 1: Run backend import safety tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_import_node.py -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/ChapterHistoryPanel.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Run diff checks**

```bash
git -C /opt/WorldSim-Writer diff --check
```

Expected: no output.

- [ ] **Step 5: Inline self-review and commit**

Review diff for readable Chinese copy, hidden raw enums/slugs, preserved import reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-next-prep-readable-recap-labels-design.md docs/superpowers/plans/2026-06-04-next-prep-readable-recap-labels.md frontend/src/world/NextChapterPrepPanel.tsx frontend/src/world/NextChapterPrepPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: localize next prep recap labels"
```

Do not push. Do not merge main.
