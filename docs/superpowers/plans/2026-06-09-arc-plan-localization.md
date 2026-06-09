# Arc Plan Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. For this session, the user explicitly requires inline execution with no subagents/agents/code-review subagent.

**Goal:** Localize the Story Arc Planner panel and hide internal enum/ID tokens from beta-facing copy.

**Architecture:** Keep the existing `ArcPlanPanel` component and API types. Add small local label maps/helper functions for arc mode, expansion budget, closure treatment, and priority, then replace raw enum/ID rendering with Chinese labels and count-based related item copy.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/world/ArcPlanPanel.test.tsx`: add failing expectations for localized copy and absence of raw tokens/IDs.
- Modify `frontend/src/world/ArcPlanPanel.tsx`: add label helpers and replace raw enum/ID display.
- Create this plan and matching design doc.

---

### Task 1: Add failing localization assertions

- [ ] In `frontend/src/world/ArcPlanPanel.test.tsx`, update the main render test to expect localized title/status copy:

```tsx
expect(screen.getByText('篇章收束计划')).toBeInTheDocument();
expect(screen.getByText('叙事阶段：收束旧线索')).toBeInTheDocument();
expect(screen.getByText('开放新线索：暂停新增')).toBeInTheDocument();
expect(screen.getByText('处理方式：本章收束 · 优先级：必须处理')).toBeInTheDocument();
expect(screen.getByText('关联角色：2 位')).toBeInTheDocument();
expect(screen.getByText('关联伏笔：1 条')).toBeInTheDocument();
```

- [ ] Add absence assertions for raw internal values:

```tsx
expect(document.body).not.toHaveTextContent('Arc Mode / Closure Plan');
expect(document.body).not.toHaveTextContent('模式：converge');
expect(document.body).not.toHaveTextContent('扩张预算：locked');
expect(document.body).not.toHaveTextContent('close · must_close');
expect(document.body).not.toHaveTextContent('关联伏笔：9');
expect(document.body).not.toHaveTextContent('关联角色：1、2');
```

- [ ] Run RED:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ArcPlanPanel.test.tsx
```

Expected: fail because the panel still renders English headings, raw enum tokens, and raw IDs.

---

### Task 2: Localize ArcPlanPanel labels

- [ ] In `frontend/src/world/ArcPlanPanel.tsx`, add label maps near the class maps:

```tsx
const ARC_MODE_LABELS: Record<string, string> = {
  expand: '扩展世界与人物',
  organize: '整理线索',
  pressure: '提高叙事压力',
  converge: '收束旧线索',
  payoff: '兑现承诺',
  endgame: '终局推进',
};

const EXPANSION_BUDGET_LABELS: Record<string, string> = {
  locked: '暂停新增',
  limited: '谨慎新增',
  open: '可以新增',
};

const TREATMENT_LABELS: Record<string, string> = {
  close: '本章收束',
  advance: '继续推进',
  merge: '合并处理',
  watch: '继续观察',
};

const PRIORITY_LABELS: Record<string, string> = {
  must_close: '必须处理',
  should_advance: '建议推进',
  can_wait: '可以等待',
};
```

- [ ] Add helper:

```tsx
function labelFrom(map: Record<string, string>, value: string): string {
  return map[value] ?? value.replace(/_/g, ' ');
}
```

- [ ] Replace the title copy:

```tsx
<p className="chapter-kicker">篇章规划</p>
<h2 className="text-2xl font-black text-[#34210f]">篇章收束计划</h2>
```

- [ ] Replace raw status pills:

```tsx
叙事阶段：{labelFrom(ARC_MODE_LABELS, arcPlan.arc_mode)}
开放新线索：{labelFrom(EXPANSION_BUDGET_LABELS, arcPlan.expansion_budget)}
```

- [ ] Replace closure metadata:

```tsx
处理方式：{labelFrom(TREATMENT_LABELS, item.treatment)} · 优先级：{labelFrom(PRIORITY_LABELS, item.priority)}
```

- [ ] Replace raw related IDs with count labels:

```tsx
{item.related_character_ids.length > 0 && <p className="mt-1 text-xs font-bold">关联角色：{item.related_character_ids.length} 位</p>}
{item.related_foreshadow_ids.length > 0 && <p className="mt-1 text-xs font-bold">关联伏笔：{item.related_foreshadow_ids.length} 条</p>}
```

- [ ] Run GREEN focused test:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ArcPlanPanel.test.tsx
```

Expected: pass.

---

### Task 3: Verify frontend slice and commit

- [ ] Run full frontend test suite:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
```

- [ ] Run frontend build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] Skip backend pytest and state why: no backend code or API contract changed.

- [ ] Run diff checks:

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add frontend/src/world/ArcPlanPanel.tsx frontend/src/world/ArcPlanPanel.test.tsx docs/superpowers/specs/2026-06-09-arc-plan-localization-design.md docs/superpowers/plans/2026-06-09-arc-plan-localization.md
git -C /opt/WorldSim-Writer diff --cached --check
```

- [ ] Commit only:

```bash
git -C /opt/WorldSim-Writer commit -m "fix: localize arc plan panel"
```

Do not push or merge.
