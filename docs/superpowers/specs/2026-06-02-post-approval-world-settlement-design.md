# Post-Approval World Settlement Design

## Goal

After a user approves a chapter, keep them in Studio and show a visible world-progression settlement area that explains what was written into canon and what changed in the world.

## Context

`docs/UX_UPDATE_PHASE.md` defines the P0 UX update: approval should feel like writing into canon, not like a backend status transition. Existing frontend data is enough for this first round:

- `approvalPreview.world_version_before` and `approvalPreview.world_version_after` show world progress.
- Selected approval change indexes show how many character and suspense/foreshadow changes were committed.
- Refreshed `/worlds/{id}/overview` shows `world_version`, `approved_chapter_count`, and `recent_events`.
- `exportWorldArchiveMarkdown(world.id)` supports the export CTA.

No backend API change is needed.

## User Experience

When approval succeeds:

1. Studio remains open.
2. A settlement panel appears with the heading `世界推进结算`.
3. The panel uses user-facing terminology:
   - `世界进度 v1 → v2`
   - `已写入正史章节：N`
   - `角色变化：N`
   - `悬念/伏笔变化：N`
   - `已写入世界历史记录`
4. The panel states that the next chapter will be generated from these canon changes.
5. The panel includes CTAs:
   - `继续下一章`
   - `查看世界概览`
   - `导出世界档案`

## CTA Behavior

- `查看世界概览`: calls the existing `onApproved(updatedOverview)` callback so `App` returns to the world overview with fresh world data.
- `导出世界档案`: calls `exportWorldArchiveMarkdown(world.id)` and shows a small success message with the returned archive filename when available.
- `继续下一章`: clears the current chapter/draft/review state, updates the local Studio context to the refreshed overview, clears the chapter goal, and leaves the user ready to create another chapter. This is the minimum useful behavior for the first round; richer next-chapter prefill can come later.

## State Model

Add a local `settlement` state to `StudioPage`:

- `worldBefore`: number
- `worldAfter`: number
- `approvedChapterCount`: number
- `characterChangeCount`: number
- `foreshadowChangeCount`: number
- `hasChapterApprovedEvent`: boolean
- `overview`: `WorldOverview`
- optional export status text

The state is created immediately after `approveChapter()` and the post-approval overview refresh both succeed.

## Error Handling

- If approval or overview refresh fails, keep the existing `审批草稿失败` error path.
- If export fails, show a local export error message in the settlement panel and keep the settlement visible.
- If `recent_events` does not include `chapter_approved`, still show the panel but phrase history evidence as not found. The primary acceptance path expects the event evidence to be present.

## Testing

Add frontend tests in `frontend/src/studio/StudioPage.test.tsx` before implementation:

1. Approval creates the settlement panel, does not call `onApproved` immediately, shows world progress, counts, event evidence, next-chapter copy, and all CTAs. Clicking `查看世界概览` calls `onApproved(updatedOverview)`.
2. Clicking `导出世界档案` calls `exportWorldArchiveMarkdown(world.id)` and shows export success text.
3. Clicking `继续下一章` clears the settlement and current draft flow so the user can create a new chapter.

## Scope Boundaries

This first round does not add backend fields, a full-screen route, automatic next-chapter recommendation, download decoding, or global terminology replacement. Those remain for later UX update priorities.
