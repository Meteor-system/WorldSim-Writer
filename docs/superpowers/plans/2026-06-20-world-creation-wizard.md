# Plan: Convert World Creation Form to Single-Screen Workspace Wizard

Date: 2026-06-20
Branch: feat/import-node-p0
Scope: frontend only — `src/world/WorldCreationForm.tsx` + `WorldCreationForm.test.tsx`. No backend, no API/type changes, no payload changes.

## Problem

`WorldCreationForm` is one ~3500px vertical long-form page. Users scroll forever. Convert to a single-screen workspace wizard: only the current step's content shows at a time; the rest is reachable via step nav + prev/next.

## Layout

Workspace card, bounded height (`max-h-[calc(100vh-...)]`), so the page does not grow unbounded.
- Header: title + current-step caption + progress (`步骤 N / 6`).
- Left: clickable step nav (current step highlighted).
- Center: current step content, internally scrollable.
- Bottom: sticky action bar — `上一步`, `下一步`, and on the final step the create button.

## Steps

1. `世界胚胎` — 3-min loop intro + 内置示例世界按钮 + 模板网格 (GENRE_PRESETS) + SeedLibraryPanel.
2. `一句话开书` — brief input, generate draft, success/error, first-chapter goal (when generated).
3. `基础设定` — title, genre_template, tone style, pacing, truth_canon.
4. `角色` — character list (internally scrollable), add character, role select, delete+undo.
5. `关系与伏笔` — relations + foreshadows (internally scrollable).
6. `确认创建` — summary preview (title, genre, counts of characters/relations/foreshadows, briefDraftApplied flag, first-chapter goal if any) + final create button.

## Behavior

- Default step = `世界胚胎`.
- Left step buttons jump directly; current highlighted.
- `下一步` forward, `上一步` back; hidden at the respective ends.
- Create button (`创建自定义世界` / `创建世界并生成第一章草稿`) only on confirm step; other steps show `下一步`.
- Brief draft success: keep `<form>` mounted (state preserved across steps); show success copy. Low-risk choice: stay on brief step, show success, user clicks 下一步 to review 基础设定. (Do NOT auto-jump — simpler, testable.)
- `onCreate` payload unchanged. autoStartFirstDraft option unchanged.
- Preserve: typed role/foreshadow selects (English values), add-character focus+highlight, delete undo toast, brief friendly errors, cancel brief.

## Key implementation note

All step content stays mounted in the DOM is NOT acceptable (tests assert step-1-only). Use conditional rendering per step so other steps' inputs are absent from the DOM. BUT form state must persist — state lives in `useState` at component top (already does), so unmounting step content does not lose data. The `<form>` wraps everything; submit only fires from confirm step's submit button.

Caution: tests query by label e.g. `screen.getByLabelText('世界标题')`. Those labels only exist when their step is rendered. Existing tests that touch multiple sections in one flow must be updated to navigate steps first.

## TDD test changes (RED → GREEN)

New/updated tests in `WorldCreationForm.test.tsx`:
1. Initial render shows only step 1 (世界胚胎): preset grid + sample button present; 世界标题/角色 inputs NOT in DOM.
2. Clicking `下一步` reaches 一句话开书; left nav button jumps to 基础设定 / 角色.
3. Create button only visible on confirm step; not visible on earlier steps.
4. On confirm step, clicking create passes payload matching current form state to onCreate.
5. Character step `添加角色` still focuses new character name input.
6. Foreshadow/role type selects still store English values.
7. When briefDraftApplied, confirm-step button text is `创建世界并生成第一章草稿`.

Existing tests rewritten to navigate steps before asserting (e.g. brief flow, seed apply, undo, selects). Payload expectations stay the same.

## Verify

- `npm run test -- --run src/world/WorldCreationForm.test.tsx`
- `npm run test -- --run`
- `npm run build`

## Out of scope

Autosave, local draft persistence, full mobile responsive rebuild (mobile must remain usable, not polished). World overview / Studio untouched.
