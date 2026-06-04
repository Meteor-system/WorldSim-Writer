# Import Node Readable Audit Copy Design

## Goal

Make the Import Node preview and audit surfaces fully readable for newcomer/beta use: Chinese user-facing copy, no raw pool enum wording, no raw conflict category wording, and no visible batch or asset IDs.

## Selected MVP Fix

The highest-value small follow-up after Import Node P1 is a frontend-only readability guard in `WorldImportPanel`. The current panel still exposes internal terms such as `canon` in pool labels, counts, and backend conflict messages. That creates cognitive load and weakens the canon-safety promise in the three-minute newcomer loop.

## Scope

- Replace visible import pool labels with Chinese product terms:
  - `canon` -> `正式设定候选`
  - `character` -> `角色候选`
  - `inspiration` -> `灵感候选`
- Replace count copy with Chinese labels:
  - `正式设定 N · 角色 N · 灵感 N`
- Render conflict warnings through a frontend label/sanitizer so internal categories and English `canon` wording are not visible.
- Keep imported candidate materials as creative references only. No backend state mutation changes.
- Keep existing import confirm behavior: confirmation writes candidate assets and import audit only, not formal canon or chapter/canon events.

## Non-Goals

- No backend API shape changes.
- No schema or event changes.
- No new import workflow stage.
- No automatic canon editing from imported materials.

## User-Facing Copy Rules

- Chinese labels only on this surface.
- Do not display raw enum values such as `canon`, `character`, `inspiration`, or `canon_overlap`.
- Do not display raw batch IDs or asset IDs.
- Preserve the safety explanation that imported materials are candidate references and do not auto-edit formal canon.

## Testing

Use TDD against `frontend/src/world/WorldImportPanel.test.tsx`:

1. Update tests to expect Chinese pool/count/conflict copy and absence of raw enum words.
2. Run the targeted test to verify RED.
3. Update `WorldImportPanel.tsx` minimally.
4. Run the targeted test to verify GREEN.
5. Run relevant backend import safety tests, frontend targeted tests, frontend build, and `git diff --check` before committing.

## Self-Review

- Scope is frontend-only and small enough for one implementation pass.
- No placeholders or ambiguous backend changes.
- Safety invariant is explicit: imported candidates remain creative references only.
