# Studio Approval Candidate Reference Note Design

## Goal

Make imported candidate material visible at the draft review and approval checkpoint, so new users understand it helped as writing reference but is not being written into formal world state automatically.

## Selected Small MVP Fix

Studio already shows candidate references before chapter creation and inside the execution context snapshot. The approval checkpoint (`写入正史前确认`) is the moment users decide what formal changes will be committed. Add a short, low-cognitive note there when the active draft/chapter context includes candidate material references:

- Heading: `候选素材写作参考`
- Summary: `本章参考候选素材：雨夜审讯。`
- Safety note: `候选素材只帮助生成正文，不会作为正式设定变化写入；只有下方勾选的角色或伏笔变化会更新世界。`

This makes the review boundary clearer: candidate material can influence prose, but formal state changes still come only from explicit approval selections.

## Scope

- Frontend-only rendering in `frontend/src/studio/StudioPage.tsx`.
- Update `frontend/src/studio/StudioPage.test.tsx` to cover the approval checkpoint note.
- Preserve chapter creation payloads, draft generation payloads, approval payloads, backend behavior, import persistence, world versioning, and event history rules.
- Preserve raw ID, enum, slug, and internal terminology hiding.

## Non-Goals

- No backend API changes.
- No database changes.
- No import candidate persistence changes.
- No automatic canon edits from imported candidate materials.
- No changes to LLM prompts or generation logic.
- No broad Studio layout redesign.

## Safety Invariant

Candidate imported materials remain writing/reference context only. The new note does not commit formal canon, world projections, world version, or event history. Formal world-state changes still require explicit approval after draft review.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. In a Studio drafting flow that uses execution-context candidate references, expect the approval checkpoint to show `候选素材写作参考`, `本章参考候选素材：雨夜审讯。`, and the safety note.
2. Assert raw/internal terms remain hidden: `asset_id`, `batch_id`, `inspiration`, and `正式 canon`.
3. Verify RED before changing production.
4. Add the minimal render helper and conditional UI in the approval preview section.
5. Verify GREEN, then run relevant backend/frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and user-facing.
- The fix improves the later chapter review checkpoint rather than adding new backend behavior.
- The design does not create or alter any canon mutation path.
- Copy uses `候选素材` and avoids raw technical terms.
