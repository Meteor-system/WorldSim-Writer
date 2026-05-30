# MVP #6 World Bible Editor 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the frontend World Bible Editor by hardening existing character, relation, and foreshadow managers with governance warnings and TDD coverage for create/edit/delete flows.

**Architecture:** Reuse existing backend CRUD endpoints and existing frontend manager components. Keep WorldPage tabs as the editor shell; each manager performs local CRUD calls and invokes `onChanged` so WorldPage refreshes world overview after formal world-state edits.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI, SQLAlchemy, pytest.

---

## File structure

- Modify `frontend/src/components/CharacterManager.tsx`: add world-version governance warning.
- Modify `frontend/src/components/RelationManager.tsx`: add world-version governance warning.
- Modify `frontend/src/components/ForeshadowManager.tsx`: add world-version governance warning.
- Create `frontend/src/components/CharacterManager.test.tsx`: cover character CRUD UI flows.
- Modify `frontend/src/components/RelationManager.test.tsx`: cover relation CRUD UI flows and invalid same-character guard.
- Create `frontend/src/components/ForeshadowManager.test.tsx`: cover foreshadow CRUD/status/stale flows.
- Modify `frontend/src/world/WorldPage.test.tsx`: ensure World Bible Editor tabs expose manager areas.
- No backend production files expected unless existing tests reveal a regression.

## Task 1: Character manager warning and CRUD tests

- [ ] Write failing tests in `frontend/src/components/CharacterManager.test.tsx` for:
  - warning text `这些编辑会正式写入世界状态，并使 world_version 增长。`;
  - create calls `createCharacter(7, payload)` and `onChanged`;
  - edit calls `updateCharacter(1, payload)` and `onChanged`;
  - delete calls `deleteCharacter(1, reason)` and `onChanged`.
- [ ] Run `cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/CharacterManager.test.tsx`; expected RED because the warning does not exist and the test file is new.
- [ ] Add the warning near the top of `CharacterManager` below the header buttons:

```tsx
<p className="mt-3 rounded-2xl border border-amber-700/25 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
  这些编辑会正式写入世界状态，并使 world_version 增长。
</p>
```

- [ ] Run the same test command; expected GREEN.

## Task 2: Relation manager warning and CRUD tests

- [ ] Extend `frontend/src/components/RelationManager.test.tsx` for:
  - warning text;
  - create calls `createRelation(7, payload)` and `onChanged`;
  - edit calls `updateRelation(1, payload)` and `onChanged`;
  - delete calls `deleteRelation(1, reason)` and `onChanged`;
  - same source/target shows `起点角色和目标角色不能相同。` and disables save.
- [ ] Run `cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/RelationManager.test.tsx`; expected RED because the warning does not exist and CRUD assertions are not yet satisfied if labels need adjustment.
- [ ] Add the same warning text near the top of `RelationManager` below the header buttons.
- [ ] Run the same test command; expected GREEN.

## Task 3: Foreshadow manager warning and CRUD tests

- [ ] Write failing tests in `frontend/src/components/ForeshadowManager.test.tsx` for:
  - warning text;
  - renders foreshadow cards and stale warning;
  - create calls `createForeshadow(7, payload)` and `onChanged`;
  - edit calls `updateForeshadow(1, payload)` and `onChanged`;
  - status advance calls `updateForeshadow(1, { status: 'resolved' })` for an advanced foreshadow and `onChanged`;
  - delete calls `deleteForeshadow(1, reason)` and `onChanged`.
- [ ] Run `cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/ForeshadowManager.test.tsx`; expected RED because the warning does not exist and the test file is new.
- [ ] Add the same warning text near the top of `ForeshadowManager` below the header buttons.
- [ ] Run the same test command; expected GREEN.

## Task 4: WorldPage editor shell test

- [ ] Extend `frontend/src/world/WorldPage.test.tsx` to assert the tabs expose `角色管理`, `关系管理`, and `伏笔账本` manager content and that the governance warning is visible after entering a manager tab.
- [ ] Run `cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx`; expected GREEN after manager warnings exist.

## Task 5: Verification, branch, commit, merge

- [ ] Create/switch to feature branch before committing implementation: `git switch -c feat/mvp6-world-bible-editor` if not already on it.
- [ ] Run backend CRUD targeted tests:
  - `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_character_crud.py tests/test_relation_crud.py tests/test_foreshadow_crud.py -v`
- [ ] Run backend full tests:
  - `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v`
- [ ] Run frontend targeted tests:
  - `cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/CharacterManager.test.tsx src/components/RelationManager.test.tsx src/components/ForeshadowManager.test.tsx src/world/WorldPage.test.tsx`
- [ ] Run frontend full tests:
  - `cd /opt/WorldSim-Writer/frontend && npm run test`
- [ ] Run frontend build:
  - `cd /opt/WorldSim-Writer/frontend && npm run build`
- [ ] Commit with message `feat: add world bible editor` and Co-Authored-By trailer.
- [ ] Merge `feat/mvp6-world-bible-editor` back to `main` locally.
- [ ] Do not push.
