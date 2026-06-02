# UI Motion Layout Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository request explicitly forbids subagents and dynamic workflows, so execute inline.

**Goal:** Polish the WorldSim-Writer frontend core entry and world workspace screens with clearer hierarchy, roomier responsive layout, and testable motion that respects `prefers-reduced-motion`.

**Architecture:** Keep this frontend-only and low-risk. Add reusable CSS motion/layout utilities in `frontend/src/styles.css`, then apply those utilities to the existing React surfaces without changing API data flow or backend contracts. Preserve Chinese user-facing copy and keep internal enum/status identifiers hidden by continuing to use `displayLabels.ts` where values are rendered.

**Tech Stack:** Vite, React, TypeScript, Tailwind utility classes, Vitest, React Testing Library.

---

## File Structure

- Modify: `frontend/src/styles.css`
  - Add reusable motion tokens/utilities: page entrance, soft hover lift, card depth, workspace grid, reduced-motion override.
  - Keep existing parchment/book visual identity.
- Modify: `frontend/src/App.tsx`
  - Give the authenticated shell a clearer app frame with a sticky-feeling header, broader layout rhythm, and localized success copy using `第 N 版`.
- Modify: `frontend/src/auth/AuthPage.tsx`
  - Improve the core login/register entry with layered hero copy, softer panel hierarchy, responsive CTA wrapping, and motion utility classes.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Improve the world overview/workbench hierarchy: primary world workspace gets the main stage, side content is grouped as supporting material, dashboard/cards/actions get motion/layout utilities and more breathable responsive grids.
- Modify: `frontend/src/world/WorldCreationForm.tsx`
  - Improve newcomer entry hierarchy and form spacing without changing form behavior.
- Modify: `frontend/src/world/WorldSearchPanel.tsx`
  - Apply reusable workspace section classes and responsive form rhythm to global search and bulk-tag controls.
- Modify: `frontend/src/world/WorldTagsPanel.tsx`
  - Apply reusable workspace section classes and responsive layout utilities to tag creation/filter/detail controls.
- Modify: `frontend/src/world/WorldTimelinePanel.tsx`
  - Apply card/list motion utilities and roomier timeline grouping.
- Test: `frontend/src/styles.test.ts`
  - Assert motion utility CSS exists and the reduced-motion media query disables animation/transition/transform.
- Test: `frontend/src/auth/AuthPage.test.tsx`
  - Assert the entry page renders natural Chinese copy, responsive CTA wrapping, and motion/layout classes.
- Test: `frontend/src/world/WorldPage.test.tsx`
  - Add coverage for overview/workbench shell classes, dashboard motion/layout classes, responsive primary/supporting grid, and internal identifier non-regression.
- Test: `frontend/src/world/WorldSearchPanel.test.tsx`
  - Add coverage for search panel motion/layout classes and responsive bulk form.
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
  - Add coverage for tag workspace motion/layout classes and responsive detail forms.
- Test: `frontend/src/world/WorldTimelinePanel.test.tsx`
  - Add coverage for timeline motion/list classes and Chinese event labels.

## Design Decisions

- Primary task for the world workbench: decide what to do next in the story world, then enter/prepare the next chapter.
- First viewport priority: world title/canon status, 今日运营 dashboard, primary CTA, and compact supporting signals.
- Deferred/reference blocks: story arc planner, narrative control panels, search, tags, timeline, archive remain below the first workspace area and retain existing IDs for anchors.
- Motion policy: use CSS-only transform/opacity/shadow transitions and short entrance animations. Content must be visible by default; motion only enhances appearance. In `prefers-reduced-motion: reduce`, animation/transition is removed and transforms are disabled.
- Copy policy: Chinese user-facing labels only in primary UI. Do not introduce English headings such as `WORLD CANON`, `WORLD OPERATIONS`, `TOOLS WORKSPACE`, or raw values such as `xianxia`, `active`, `planted`, `v1` in main flows.

---

### Task 1: Add RED tests for motion utilities and entry page polish

**Files:**
- Create: `frontend/src/styles.test.ts`
- Modify: `frontend/src/auth/AuthPage.test.tsx`

- [ ] **Step 1: Write failing stylesheet tests**

Create `frontend/src/styles.test.ts`:

```ts
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const css = readFileSync(join(process.cwd(), 'src/styles.css'), 'utf8');

describe('frontend motion utilities', () => {
  it('defines reusable motion and layered surface utilities', () => {
    expect(css).toContain('.motion-page-enter');
    expect(css).toContain('.motion-soft-lift');
    expect(css).toContain('.surface-layer');
    expect(css).toContain('.workspace-shell');
    expect(css).toContain('@keyframes page-rise');
  });

  it('disables animation, transition, and transform for reduced motion users', () => {
    const reducedMotionBlock = css.slice(css.indexOf('@media (prefers-reduced-motion: reduce)'));

    expect(reducedMotionBlock).toContain('.motion-page-enter');
    expect(reducedMotionBlock).toContain('animation: none');
    expect(reducedMotionBlock).toContain('transition: none');
    expect(reducedMotionBlock).toContain('transform: none');
  });
});
```

- [ ] **Step 2: Write failing AuthPage UI tests**

Create or update `frontend/src/auth/AuthPage.test.tsx` with this test if the file is missing:

```tsx
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthPage } from './AuthPage';

vi.mock('../api/client', () => ({ apiRequest: vi.fn() }));

afterEach(() => cleanup());

describe('AuthPage layout polish', () => {
  it('renders a layered Chinese entry page with responsive actions and motion classes', () => {
    render(<AuthPage onAuth={vi.fn()} />);

    expect(screen.getByText('进入故事世界运营台')).toBeInTheDocument();
    expect(screen.getByText('登录后创建世界胚胎、推进章节草稿，并把通过审核的章节写入正史。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('WorldSim Archive');

    const panel = screen.getByTestId('auth-entry-panel');
    expect(panel).toHaveClass('motion-page-enter');
    expect(panel).toHaveClass('surface-layer');

    const actions = screen.getByTestId('auth-actions');
    expect(actions).toHaveClass('flex-wrap');
    expect(actions).toHaveClass('gap-3');
  });
});
```

If `AuthPage.test.tsx` already exists, add only the `it(...)` body above and imports as needed.

- [ ] **Step 3: Run tests to verify RED**

Run from `frontend/`:

```bash
npm run test -- src/styles.test.ts src/auth/AuthPage.test.tsx
```

Expected: FAIL because `.motion-page-enter`, `.surface-layer`, `.workspace-shell`, the reduced-motion utility block, `auth-entry-panel`, `auth-actions`, and the new Chinese entry copy are not implemented yet.

---

### Task 2: Implement motion utilities and entry page polish

**Files:**
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/auth/AuthPage.tsx`
- Test: `frontend/src/styles.test.ts`
- Test: `frontend/src/auth/AuthPage.test.tsx`

- [ ] **Step 1: Add minimal CSS utilities**

In `frontend/src/styles.css`, add reusable utilities before the existing `@media (prefers-reduced-motion: reduce)` block:

```css
.motion-page-enter {
  animation: page-rise 320ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

.motion-soft-lift {
  transition: transform 180ms cubic-bezier(0.22, 1, 0.36, 1), box-shadow 180ms cubic-bezier(0.22, 1, 0.36, 1), border-color 180ms ease, background 180ms ease;
}

.motion-soft-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 60px rgb(83 53 18 / 18%);
}

.surface-layer {
  border: 1px solid rgb(128 83 34 / 22%);
  background: rgb(255 248 232 / 72%);
  box-shadow: 0 18px 55px rgb(83 53 18 / 14%);
}

.workspace-shell {
  display: grid;
  gap: 2rem;
}

@media (min-width: 1024px) {
  .workspace-shell {
    grid-template-columns: minmax(0, 1.35fr) minmax(18rem, 0.65fr);
    align-items: start;
  }
}

@keyframes page-rise {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.99);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```

Then extend the existing reduced-motion block so it includes:

```css
  .motion-page-enter,
  .motion-soft-lift {
    animation: none;
    transition: none;
    transform: none;
  }

  .motion-soft-lift:hover {
    transform: none;
  }
```

- [ ] **Step 2: Update AuthPage markup minimally**

In `frontend/src/auth/AuthPage.tsx`:

- Change the main section class to include `motion-page-enter surface-layer` and `data-testid="auth-entry-panel"`.
- Replace `WorldSim Archive` with `故事世界入口`.
- Replace the hero heading with `进入故事世界运营台`.
- Replace the body copy with `登录后创建世界胚胎、推进章节草稿，并把通过审核的章节写入正史。`.
- Change the MVP note to `审批通过后，系统会更新世界进度、角色目标、悬念/伏笔和世界历史记录。`.
- Add `data-testid="auth-actions"` and `flex-wrap` to the button row.
- Add `motion-soft-lift` to both buttons.

- [ ] **Step 3: Run tests to verify GREEN**

Run from `frontend/`:

```bash
npm run test -- src/styles.test.ts src/auth/AuthPage.test.tsx
```

Expected: PASS.

---

### Task 3: Add RED tests for WorldPage workspace hierarchy, motion, and responsive layout

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldCreationForm.test.tsx`

- [ ] **Step 1: Add failing WorldPage tests**

Append to `frontend/src/world/WorldPage.test.tsx`:

```tsx
describe('WorldPage motion and layout polish', () => {
  it('renders the overview as a staged responsive workspace without internal identifiers', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();

    const workspace = screen.getByTestId('world-overview-workspace');
    expect(workspace).toHaveClass('workspace-shell');
    expect(workspace).toHaveClass('motion-page-enter');

    const primary = screen.getByTestId('world-primary-stage');
    expect(primary).toHaveClass('space-y-8');

    const supporting = screen.getByTestId('world-supporting-rail');
    expect(supporting).toHaveClass('space-y-5');

    expect(document.body).not.toHaveTextContent('WORLD CANON');
    expect(document.body).not.toHaveTextContent('WORLD OPERATIONS');
    expect(document.body).not.toHaveTextContent('xianxia');
    expect(document.body).not.toHaveTextContent('running');
  });

  it('adds motion and hierarchy classes to dashboard cards and actions', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('世界运营仪表盘'));
    expect(dashboard.getByTestId('world-dashboard-metrics')).toHaveClass('gap-4');
    expect(dashboard.getByTestId('world-dashboard-actions')).toHaveClass('lg:grid-cols-3');
    dashboard.getAllByTestId('world-dashboard-action-card').forEach((card) => {
      expect(card).toHaveClass('motion-soft-lift');
      expect(card).toHaveClass('surface-layer');
    });
  });
});
```

- [ ] **Step 2: Add failing WorldCreationForm tests**

Add to `frontend/src/world/WorldCreationForm.test.tsx`:

```tsx
it('uses a layered responsive creation layout with motion classes', () => {
  renderWorldCreationForm();

  const form = screen.getByTestId('world-creation-form');
  expect(form).toHaveClass('motion-page-enter');

  const loop = screen.getByTestId('newcomer-loop-panel');
  expect(loop).toHaveClass('surface-layer');

  const presetGrid = screen.getByTestId('genre-preset-grid');
  expect(presetGrid).toHaveClass('gap-4');
  expect(presetGrid).toHaveClass('md:grid-cols-3');
});
```

If the existing helper is not named `renderWorldCreationForm`, use the existing render helper in that file and keep the same assertions.

- [ ] **Step 3: Run tests to verify RED**

Run from `frontend/`:

```bash
npm run test -- src/world/WorldPage.test.tsx src/world/WorldCreationForm.test.tsx
```

Expected: FAIL because the new test IDs and motion/surface classes are absent.

---

### Task 4: Implement WorldPage and creation form layout polish

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldCreationForm.tsx`
- Test: `frontend/src/world/WorldPage.test.tsx`
- Test: `frontend/src/world/WorldCreationForm.test.tsx`

- [ ] **Step 1: Polish App shell**

In `frontend/src/App.tsx`:

- Add `motion-page-enter` to the outer authenticated container.
- Change the success copy from `世界版本更新为 {approvedWorld.world_version}` to `世界进度更新为第 {approvedWorld.world_version} 版`.
- Make the header wrap naturally with `flex flex-wrap items-center justify-between gap-3`.

- [ ] **Step 2: Add WorldPage workspace test hooks/classes**

In `frontend/src/world/WorldPage.tsx`:

- Change the overview content wrapper from `className="grid gap-8 md:grid-cols-[1fr_1fr]"` to:

```tsx
<div className="workspace-shell motion-page-enter" data-testid="world-overview-workspace">
```

- Change the primary column from `<div>` to:

```tsx
<div className="space-y-8" data-testid="world-primary-stage">
```

- Remove duplicated `mt-8` spacing from child blocks where `space-y-8` now handles rhythm only if it creates excessive gaps.
- Change the supporting rail wrapper from `className="space-y-4"` to:

```tsx
<div className="space-y-5" data-testid="world-supporting-rail">
```

- Add `motion-soft-lift` to supporting `book-card` articles.

- [ ] **Step 3: Add dashboard hierarchy classes**

In `WorldOperationsDashboard`:

- Change metrics wrapper to include `data-testid="world-dashboard-metrics"`.
- Add `surface-layer motion-soft-lift` and `data-testid="world-dashboard-action-card"` to each recommendation card.
- Add `motion-soft-lift` to the sidebar cards.

- [ ] **Step 4: Polish creation form classes**

In `frontend/src/world/WorldCreationForm.tsx`:

- Add `data-testid="world-creation-form"` and `motion-page-enter` to the `<form>`.
- Add `data-testid="newcomer-loop-panel"` and `surface-layer` to the first newcomer loop panel.
- Change preset grid from `gap-3` to `gap-4` and add `data-testid="genre-preset-grid"`.
- Add `motion-soft-lift` to preset buttons and repeated character/foreshadow cards.

- [ ] **Step 5: Run tests to verify GREEN**

Run from `frontend/`:

```bash
npm run test -- src/world/WorldPage.test.tsx src/world/WorldCreationForm.test.tsx
```

Expected: PASS.

---

### Task 5: Add RED tests for tools workspace panels and timeline polish

**Files:**
- Modify: `frontend/src/world/WorldSearchPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTimelinePanel.test.tsx`

- [ ] **Step 1: Add failing WorldSearchPanel tests**

Append to `frontend/src/world/WorldSearchPanel.test.tsx`:

```tsx
it('uses layered motion classes for the search workspace and bulk controls', async () => {
  renderWorldSearchPanel();

  expect(await screen.findByText('全局搜索')).toBeInTheDocument();
  const panel = screen.getByTestId('world-search-panel');
  expect(panel).toHaveClass('motion-page-enter');

  expect(screen.getByTestId('world-search-controls')).toHaveClass('flex-wrap');

  await userEvent.type(screen.getByLabelText('搜索世界资料'), '灯塔');
  await userEvent.click(screen.getByRole('button', { name: '搜索' }));

  const bulkForm = await screen.findByTestId('world-search-bulk-form');
  expect(bulkForm).toHaveClass('surface-layer');
  expect(bulkForm).toHaveClass('gap-4');
});
```

Use the existing render helper name if it differs from `renderWorldSearchPanel`.

- [ ] **Step 2: Add failing WorldTagsPanel tests**

Append to `frontend/src/world/WorldTagsPanel.test.tsx`:

```tsx
it('uses layered motion classes for tag workspace controls and detail cards', async () => {
  renderWorldTagsPanel();

  expect(await screen.findByText('标签与收藏')).toBeInTheDocument();
  expect(screen.getByTestId('world-tags-panel')).toHaveClass('motion-page-enter');
  expect(screen.getByTestId('tag-create-form')).toHaveClass('gap-4');
  expect(screen.getByTestId('tag-filter-controls')).toHaveClass('gap-4');

  await userEvent.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  expect(await screen.findByTestId('tag-detail-panel')).toHaveClass('surface-layer');
});
```

Use the existing render helper name if it differs from `renderWorldTagsPanel`.

- [ ] **Step 3: Add failing WorldTimelinePanel tests**

Append to `frontend/src/world/WorldTimelinePanel.test.tsx`:

```tsx
it('uses layered timeline cards with motion while keeping Chinese event labels', async () => {
  renderTimelinePanel();

  expect(await screen.findByText('世界历史记录')).toBeInTheDocument();
  expect(screen.getByTestId('world-timeline-panel')).toHaveClass('motion-page-enter');
  expect(screen.getByTestId('world-timeline-summary')).toHaveClass('gap-4');

  const eventCards = screen.getAllByTestId('world-timeline-event-card');
  expect(eventCards[0]).toHaveClass('motion-soft-lift');
  expect(document.body).not.toHaveTextContent('WORLD_CREATED');
});
```

Use the existing render helper name if it differs from `renderTimelinePanel`.

- [ ] **Step 4: Run tests to verify RED**

Run from `frontend/`:

```bash
npm run test -- src/world/WorldSearchPanel.test.tsx src/world/WorldTagsPanel.test.tsx src/world/WorldTimelinePanel.test.tsx
```

Expected: FAIL because the new panel/detail/card test IDs and motion/surface classes are absent.

---

### Task 6: Implement tools workspace and timeline polish

**Files:**
- Modify: `frontend/src/world/WorldSearchPanel.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`
- Modify: `frontend/src/world/WorldTimelinePanel.tsx`
- Test: `frontend/src/world/WorldSearchPanel.test.tsx`
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Test: `frontend/src/world/WorldTimelinePanel.test.tsx`

- [ ] **Step 1: Polish WorldSearchPanel classes**

In `WorldSearchPanel.tsx`:

- Add `data-testid="world-search-panel"` and `motion-page-enter` to the root `<section>`.
- Change the bulk assignment form to `className="grid gap-4 rounded-2xl surface-layer p-4 md:grid-cols-[minmax(0,1fr)_auto]"` and add `data-testid="world-search-bulk-form"`.
- Add `motion-soft-lift` to result article cards.
- Keep existing Chinese labels and `labelObjectType`, `labelTagName`, `localizeSubtitle` usage.

- [ ] **Step 2: Polish WorldTagsPanel classes**

In `WorldTagsPanel.tsx`:

- Add `data-testid="world-tags-panel"` and `motion-page-enter` to the root `<section>`.
- Change filter controls grid to include `gap-4` and `data-testid="tag-filter-controls"`.
- Add `data-testid="tag-detail-panel"`, `surface-layer`, and `motion-page-enter` to the tag detail wrapper.
- Add `motion-soft-lift` to visible tag buttons and object result cards.

- [ ] **Step 3: Polish WorldTimelinePanel classes**

In `WorldTimelinePanel.tsx`:

- Add `data-testid="world-timeline-panel"` and `motion-page-enter` to the root `<section>`.
- Add `data-testid="world-timeline-summary"` and change summary grid gap from `gap-3` to `gap-4`.
- Add `data-testid="world-timeline-event-card"`, `surface-layer`, and `motion-soft-lift` to each event article.

- [ ] **Step 4: Run tests to verify GREEN**

Run from `frontend/`:

```bash
npm run test -- src/world/WorldSearchPanel.test.tsx src/world/WorldTagsPanel.test.tsx src/world/WorldTimelinePanel.test.tsx
```

Expected: PASS.

---

### Task 7: Full verification and commit

**Files:**
- All modified frontend files and tests.

- [ ] **Step 1: Run full frontend tests**

Run from `frontend/`:

```bash
npm run test
```

Expected: PASS with zero failing test files.

- [ ] **Step 2: Run frontend build**

Run from `frontend/`:

```bash
npm run build
```

Expected: PASS with Vite build completing successfully.

- [ ] **Step 3: Run whitespace diff check**

Run from repository root or any directory:

```bash
git -C /opt/WorldSim-Writer diff --check
```

Expected: no output.

- [ ] **Step 4: Inspect git status**

Run:

```bash
git -C /opt/WorldSim-Writer status --short --branch
```

Expected: branch is `feat/ui-motion-layout-polish` with only intended frontend/test/plan changes.

- [ ] **Step 5: Commit without push or merge**

Run:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/plans/2026-06-02-ui-motion-layout-polish.md frontend/src/styles.css frontend/src/styles.test.ts frontend/src/App.tsx frontend/src/auth/AuthPage.tsx frontend/src/auth/AuthPage.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx frontend/src/world/WorldCreationForm.tsx frontend/src/world/WorldCreationForm.test.tsx frontend/src/world/WorldSearchPanel.tsx frontend/src/world/WorldSearchPanel.test.tsx frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx frontend/src/world/WorldTimelinePanel.tsx frontend/src/world/WorldTimelinePanel.test.tsx && git -C /opt/WorldSim-Writer commit -m "feat: polish ui motion and layout"
```

Expected: local commit created on `feat/ui-motion-layout-polish`. Do not push. Do not merge main.

## Self-Review

- Spec coverage: Covers branch setup already completed, low-risk frontend-only UI polish, testable motion/reduced-motion, responsive/spacing classes, Chinese copy preservation, full frontend tests/build/diff-check, commit without push/merge.
- Placeholder scan: No `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: Tests refer only to CSS classes/test IDs added in implementation tasks and existing component names/helpers. If an existing test helper name differs, use that file's existing helper while preserving assertions.
