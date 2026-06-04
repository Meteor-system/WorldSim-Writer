# Character Arc Readable Audit Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw Studio character arc report labels, raw proposed-change JSON, and same-surface English/internal safety copy with readable Chinese audit copy.

**Architecture:** Frontend-only presentation update in `CharacterArcPanel.tsx`. Add local label helpers for character arc report values and render proposed state changes as short lines; do not change report data, Studio actions, approval preview, or canon mutation behavior.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/CharacterArcPanel.test.tsx`
  - Update the existing report test first to expect readable Chinese labels and absence of raw internals.
- Modify: `frontend/src/studio/CharacterArcPanel.tsx`
  - Add small label maps and readable proposed-change formatting.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Character arc report hides raw audit labels

**Files:**
- Modify: `frontend/src/studio/CharacterArcPanel.test.tsx`
- Modify: `frontend/src/studio/CharacterArcPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `renders stale warning, character arcs, relationship notes, and progression hints`, replace raw-label assertions with:

```ts
expect(screen.getByText('林砚 · 主角')).toBeInTheDocument();
expect(screen.getByText('出现：主要登场 · 阶段：做出选择')).toBeInTheDocument();
expect(screen.getByText('拟提交变化：状态改为「开始调查密信」；当前目标改为「追查湿信来源」')).toBeInTheDocument();
expect(screen.getByText('林砚 → 沈微霜 · 不稳盟友')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('林砚 · protagonist');
expect(document.body).not.toHaveTextContent('出现：major · 阶段：choice');
expect(document.body).not.toHaveTextContent('uneasy_ally');
expect(document.body).not.toHaveTextContent('{"status":"开始调查密信"');
```

Keep the existing safety copy and CTA assertion.

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/CharacterArcPanel.test.tsx -t "renders stale warning"
```

Expected: FAIL because the panel still shows raw labels and raw JSON proposed changes.

- [ ] **Step 3: Write minimal implementation**

In `CharacterArcPanel.tsx`:

- Add label maps for role, presence, arc stage, relation type, and proposed state-change fields.
- Replace visible raw values with helpers.
- Replace `JSON.stringify(arc.proposed_state_change)` with a readable sentence.
- Replace `approval preview` in the safety note with `批准预览`.

Use these labels:

```ts
const ROLE_LABELS: Record<string, string> = {
  protagonist: '主角',
  antagonist: '对手',
  supporting: '配角',
  minor: '龙套',
};

const PRESENCE_LABELS: Record<string, string> = {
  absent: '未登场',
  mentioned: '被提及',
  supporting: '辅助登场',
  major: '主要登场',
};

const ARC_STAGE_LABELS: Record<string, string> = {
  setup: '铺垫',
  pressure: '承压',
  choice: '做出选择',
  consequence: '承接后果',
  growth: '成长',
  regression: '退回',
  resolution: '收束',
  unknown: '未知阶段',
};

const RELATION_TYPE_LABELS: Record<string, string> = {
  uneasy_ally: '不稳盟友',
};

const PROPOSED_CHANGE_LABELS: Record<string, string> = {
  status: '状态',
  current_goals: '当前目标',
};
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/CharacterArcPanel.test.tsx -t "renders stale warning"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/CharacterArcPanel.test.tsx src/studio/StudioPage.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for readable Chinese copy, hidden raw labels, preserved advisory/canon safety, and no backend mutation path, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-character-arc-readable-audit-labels-design.md docs/superpowers/plans/2026-06-04-character-arc-readable-audit-labels.md frontend/src/studio/CharacterArcPanel.tsx frontend/src/studio/CharacterArcPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: localize character arc audit labels"
```

Do not push. Do not merge main.
