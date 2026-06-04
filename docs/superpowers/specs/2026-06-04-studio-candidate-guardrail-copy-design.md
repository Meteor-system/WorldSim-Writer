# Studio Candidate Guardrail Copy Design

## Goal

Make Studio chapter-writing and settlement guardrails consistently describe imported references as candidate materials.

## Selected Small MVP Fix

Studio already shows `候选素材参考：1 条`, but related guardrails still use generic `导入素材` or `素材参考` wording:

- Execution context card: `导入素材只是本章写作参考，不会自动改写正式设定。`
- Frozen execution context snapshot: `素材参考不会自动改写正式设定。`
- Post-approval settlement: `导入素材仍是本章创作参考，没有自动写入正式设定。`

These are safe, but less explicit than the current Import Node P1 wording. The smallest useful fix is to change them to candidate-material copy while leaving chapter creation, approval, and world-state behavior unchanged.

## Scope

- Frontend-only copy update in `frontend/src/studio/StudioPage.tsx`.
- Update `frontend/src/studio/StudioPage.test.tsx` to expect the clearer Studio candidate-material guardrails and reject the older generic copy.
- Keep execution context payloads, draft generation, approval behavior, settlement data, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import parsing or classification changes.
- No chapter generation or approval transaction changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate-only writing references. This task changes visible Studio copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Expect `候选素材只是本章写作参考，不会自动改写正式设定。` in the launch execution context summary.
2. Expect `候选素材参考不会自动改写正式设定。` in the frozen execution context snapshot.
3. Expect `候选素材仍是本章创作参考，没有自动写入正式设定。` in the settlement panel.
4. Assert the older generic strings are not exposed.
5. Preserve existing assertions that raw IDs, slugs, enums, and `正式 canon` are not exposed.
6. Verify RED before changing production copy.
7. Change only visible frontend strings in `StudioPage.tsx`.
8. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves chapter-writing reference clarity in Studio, the key later-creation surface.
- The design keeps imported candidates out of formal canon until explicit approval.
