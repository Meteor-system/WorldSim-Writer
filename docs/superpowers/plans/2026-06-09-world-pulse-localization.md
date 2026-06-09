# World Pulse Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. For this session, the user explicitly requires inline execution with no subagents/agents/code-review subagent.

**Goal:** Localize the WorldPage world-pulse panel and hide raw enum/thread ID tokens from beta-facing copy.

**Architecture:** Keep the existing `WorldPulsePanel` component and API types. Add small local label maps/helper functions for pulse status, mode, focus priority, thread source, and known English product-name normalization.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/world/WorldPulsePanel.test.tsx`: add failing expectations for localized copy and absence of raw tokens/IDs.
- Modify `frontend/src/world/WorldPulsePanel.tsx`: add label helpers and replace raw enum/ID rendering.
- Modify `frontend/src/world/WorldPage.test.tsx`: update related integration expectation from `World Pulse` to the localized title.
- Create this plan and matching design doc.

---

### Task 1: Add failing world-pulse localization assertions

- [ ] In `frontend/src/world/WorldPulsePanel.test.tsx`, update the main render test to expect localized title/status/mode/source copy:

```tsx
expect(screen.getByText('世界心跳')).toBeInTheDocument();
expect(screen.getByText('世界心跳：开放线索压力较高，建议下一章优先收束。')).toBeInTheDocument();
expect(screen.getByText('状态：需要立刻处理')).toBeInTheDocument();
expect(screen.getByText('模式：叙事收束')).toBeInTheDocument();
expect(screen.getByText('84/100 · 需要观察')).toBeInTheDocument();
expect(screen.getByText('来自叙事健康度的聚合风险。')).toBeInTheDocument();
expect(screen.getByText('优先级：需要立刻处理')).toBeInTheDocument();
expect(screen.getByText('建议：查看开放线索看板。')).toBeInTheDocument();
expect(screen.getByText('线索来源：伏笔线索')).toBeInTheDocument();
```

- [ ] Add absence assertions for old English/raw values:

```tsx
expect(document.body).not.toHaveTextContent('Operational Overview');
expect(document.body).not.toHaveTextContent('Narrative Health');
expect(document.body).not.toHaveTextContent('84/100 · watch');
expect(document.body).not.toHaveTextContent('状态：urgent');
expect(document.body).not.toHaveTextContent('模式：converge');
expect(document.body).not.toHaveTextContent('查看 Open Threads Board。');
expect(document.body).not.toHaveTextContent('关联线索：foreshadow:9');
expect(document.body).not.toHaveTextContent('foreshadow:9');
```

- [ ] Run RED:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/world/WorldPulsePanel.test.tsx
```

Expected: fail because the panel still renders English headings, raw enum tokens, and raw IDs.

---

### Task 2: Localize `WorldPulsePanel`

- [ ] In `frontend/src/world/WorldPulsePanel.tsx`, add label maps near the class maps:

```tsx
const STATUS_LABELS: Record<string, string> = {
  stable: '稳定',
  watch: '需要观察',
  urgent: '需要立刻处理',
};

const FOCUS_PRIORITY_LABELS: Record<string, string> = {
  stable: '稳定',
  watch: '需要观察',
  risk: '存在风险',
  urgent: '需要立刻处理',
};

const THREAD_TYPE_LABELS: Record<string, string> = {
  foreshadow: '伏笔线索',
  character_goal: '角色目标',
  progression_hint: '推进提示',
  health_risk: '健康风险',
};
```

- [ ] Add helper functions:

```tsx
function labelFrom(map: Record<string, string>, value: string): string {
  return map[value] ?? value.replace(/_/g, ' ');
}

function labelThreadSource(threadId: string): string {
  const [threadType] = threadId.split(':');
  return THREAD_TYPE_LABELS[threadType] ?? '叙事线索';
}

function localizeCopy(value: string): string {
  return value
    .replace(/World Pulse/g, '世界心跳')
    .replace(/Narrative Health/g, '叙事健康度')
    .replace(/\s*Open Threads Board/g, '开放线索看板')
    .replace(/\bwatch\b/g, '需要观察')
    .replace(/\burgent\b/g, '需要立刻处理')
    .replace(/\bstable\b/g, '稳定')
    .replace(/来自\s+叙事健康度\s+的/g, '来自叙事健康度的');
}
```

- [ ] Replace title copy:

```tsx
<p className="chapter-kicker">世界运营概览</p>
<h2 className="text-2xl font-black text-[#34210f]">世界心跳</h2>
```

- [ ] Render localized status/mode and text fields:

```tsx
<p className="manuscript mt-2 text-sm text-[#5e3b1c]">{localizeCopy(pulse.headline)}</p>
...
状态：{labelFrom(STATUS_LABELS, pulse.pulse_status)}
...
模式：{labelFrom(MODE_LABELS, pulse.primary_mode)}
```

- [ ] Render localized focus priority, suggested action, and thread source:

```tsx
<p className="text-xs font-black tracking-[0.18em]">优先级：{labelFrom(FOCUS_PRIORITY_LABELS, item.priority)}</p>
...
<p className="manuscript mt-1 text-sm">建议：{localizeCopy(item.suggested_action)}</p>
{item.related_thread_id && <p className="mt-2 text-xs font-bold">线索来源：{labelThreadSource(item.related_thread_id)}</p>}
```

- [ ] Run GREEN focused test:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/world/WorldPulsePanel.test.tsx
```

Expected: pass.

---

### Task 3: Verify frontend slice and commit

- [ ] Run related targeted frontend tests:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/world/WorldPulsePanel.test.tsx src/world/WorldPage.test.tsx
```

- [ ] Run frontend build:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run build
```

- [ ] Skip backend pytest and state why: no backend code or API contract changed.

- [ ] Run diff checks:

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add frontend/src/world/WorldPulsePanel.tsx frontend/src/world/WorldPulsePanel.test.tsx frontend/src/world/WorldPage.test.tsx docs/superpowers/specs/2026-06-09-world-pulse-localization-design.md docs/superpowers/plans/2026-06-09-world-pulse-localization.md
git -C /opt/WorldSim-Writer diff --cached --check
```

- [ ] Commit only:

```bash
git -C /opt/WorldSim-Writer commit -m "fix: localize world pulse panel"
```

Do not push or merge.
