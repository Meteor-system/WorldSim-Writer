# Character and Foreshadow CRUD hardening design

## Goal

Review and improve the existing Character and Foreshadow CRUD implementation while staying within the MVP loop. Preserve hard deletes and the current domain-folder architecture, and align behavior with `app/world/` ownership patterns.

## Backend design

Keep the current character and foreshadow routers and services. Use `require_owned_world()` for world-scoped create/list operations and owned-resource checks for get/update/delete operations.

Character schemas will reject blank `name` and `role_type`. Optional JSON fields remain optional, with service defaults matching model defaults: `status='active'`, empty profile objects, and an empty goals list.

Foreshadow schemas will reject blank `title`, `description`, and `foreshadow_type`. `urgency_level` must be in the range 1 through 5. Optional fields keep their current defaults: `status='planted'`, empty `related_character_ids`, and nullable `source_chapter_id` / `expected_resolution_window`.

Foreshadow create/update must strictly validate references. Every `related_character_id` must identify a character in the same owned world. If `source_chapter_id` is provided, it must identify a chapter in the same owned world. Invalid references return a clear API error and must not persist partial updates.

Hard deletes are allowed for both characters and foreshadows.

## Frontend design

Keep `CharacterManager.tsx` and `ForeshadowManager.tsx` as focused tab components.

Fix the shared API client so `204 No Content` responses do not attempt JSON parsing. Improve error formatting so component errors are readable rather than raw response text when the backend returns JSON detail payloads.

Character forms continue to expose the existing minimal fields and send trimmed values.

Foreshadow forms should reduce invalid related-character input by deriving choices from the provided `characters` prop instead of requiring free-text IDs. Quick status-toggle failures should be surfaced to the user instead of silently ignored.

The world page should avoid stale character data after CRUD changes, either by reloading the overview after manager mutations or by passing a refresh callback into the managers.

## Testing and verification

Add backend tests under `backend/tests/` using the existing `TestClient` fixtures.

Coverage should include authentication requirements, owner-only access, character create/list/get/update/delete, foreshadow create/list/get/update/delete, invalid `urgency_level`, invalid or foreign `related_character_ids`, and invalid or foreign `source_chapter_id`.

Implementation should follow test-driven development: add failing tests first, then make the smallest code changes needed to pass.

Verify with:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v'
cd /opt/WorldSim-Writer/frontend && npm run build
```

Before final completion, request code review and then commit relevant changes with a descriptive message and the required co-author trailer.
