# Import Node P0 Design Spec

**Goal:** Implement the P0/MVP “小说生成导入节点 / 素材接入节点” as a safe story-material ingestion layer, not a generic workflow system.

**Source:** `WorldSim-Writer.md` section `2.7.2 小说生成导入节点与素材接入编排`.

**User-approved scope:** Routine design decisions are self-approved for this 2-hour MVP development round. No dynamic workflows, no subagents, no push, no merge main.

---

## 1. Product Positioning

The import node is a **story-material digestion layer** between user-provided text and WorldSim story assets.

It must not behave as a general automation workflow, task runner, or low-code connector. Its responsibilities are limited to:

1. Accept a single pasted text payload or a single Markdown/txt-like text payload.
2. Parse, classify, clean, and lightly conflict-check that material.
3. Produce a structured preview that is safe for user review.
4. On explicit confirmation, write **candidate assets** and an auditable batch record.
5. Avoid directly mutating formal `truth_canon`, `world_version`, approved chapters, characters, foreshadows, or current projection state.

## 2. P0 Vertical Slice

### In scope

- Backend API for:
  - import preview
  - confirm import batch
  - list import batches for a world
- Basic deterministic parsing and classification, no external LLM required.
- Candidate asset pools:
  - `inspiration`
  - `character`
  - `canon`
- Source and audit structure:
  - import batch id
  - source title
  - source type
  - original text excerpt
  - cleaned text excerpt
  - created asset counts
  - event log entry for confirmation
- Frontend panel in the world workspace:
  - paste/import text area
  - Markdown/txt source metadata fields
  - structured preview grouped by asset pool
  - conflict notices
  - explicit confirm button
  - recent batch summary

### Out of scope for P0

- Real file upload transport. The UI may support pasted text and metadata that represents Markdown/txt source.
- Complex rich-text parsing.
- LLM-based extraction.
- Automatic canon mutation.
- Batch rollback endpoint. P0 records enough batch/source data for future rollback, but does not expose a destructive rollback action.
- P2/P3 cross-world migration or project-level import.

## 3. Backend Design

### Domain module

Add a focused backend domain module:

- `app/import_node/models.py`
- `app/import_node/schemas.py`
- `app/import_node/service.py`
- `app/import_node/router.py`

Register it in:

- `app/core/database.py#import_models`
- `app/api/router.py`

### Minimal data model

Use two tables.

#### `import_batches`

- `id`
- `world_id`
- `source_type`: `pasted_text`, `markdown`, or `txt`
- `source_title`
- `original_excerpt`
- `cleaned_excerpt`
- `status`: P0 uses `previewed` and `confirmed`
- `asset_counts`: JSON object, such as `{ "inspiration": 2, "character": 1, "canon": 1 }`
- `conflicts`: JSON list
- `created_at`
- `confirmed_at`

#### `import_candidate_assets`

- `id`
- `world_id`
- `batch_id`
- `asset_pool`: `inspiration`, `character`, or `canon`
- `title`
- `summary`
- `raw_text`
- `metadata`: JSON object with source line, confidence, extracted labels, conflict references
- `status`: P0 uses `candidate`
- `created_at`

### Preview endpoint

`POST /worlds/{world_id}/imports/preview`

Request:

```json
{
  "source_type": "markdown",
  "source_title": "旧设定.md",
  "content": "# 角色\n沈微霜：黑水城密探..."
}
```

Response:

```json
{
  "world_id": 1,
  "source_type": "markdown",
  "source_title": "旧设定.md",
  "cleaned_excerpt": "角色\n沈微霜：黑水城密探...",
  "assets": [
    {
      "asset_pool": "character",
      "title": "沈微霜",
      "summary": "黑水城密探",
      "raw_text": "沈微霜：黑水城密探...",
      "metadata": { "confidence": "medium" }
    }
  ],
  "conflicts": [
    {
      "severity": "warning",
      "category": "canon_overlap",
      "message": "导入内容提到已有 canon 关键词：黑水城",
      "matched_text": "黑水城"
    }
  ],
  "asset_counts": { "character": 1 }
}
```

Preview does not write to the database.

### Confirm endpoint

`POST /worlds/{world_id}/imports/confirm`

Request repeats source metadata and includes selected assets from preview. This avoids storing temporary previews in P0.

Behavior:

1. Re-validates world ownership.
2. Creates an `ImportBatch` with status `confirmed`.
3. Inserts selected assets as `candidate` rows.
4. Writes an `EventLog` with:
   - `event_type`: `material_import_confirmed`
   - `source_type`: `import_node`
   - `world_version_before`: current world version
   - `world_version_after`: current world version
5. Does **not** increment `world_version`.
6. Does **not** mutate `world.truth_canon`.

### List endpoint

`GET /worlds/{world_id}/imports`

Returns recent import batches and their candidate assets so the frontend can show audit/source history.

## 4. Deterministic P0 Parsing Rules

The parser is intentionally conservative.

### Cleaning

- Normalize line endings.
- Strip surrounding whitespace.
- Drop empty lines beyond one separator.
- Remove Markdown heading markers, list bullets, blockquote markers, and fenced code markers from classification text.
- Enforce max content length at API schema level.

### Classification heuristics

- Character candidate:
  - line starts with `角色：`, `人物：`, `角色 -`, `人物 -`
  - or line contains Chinese name-like token followed by `：` and role keywords such as `主角`, `反派`, `密探`, `剑修`, `城主`, `弟子`
- Canon candidate:
  - line starts with `设定：`, `规则：`, `世界观：`, `canon：`, `真理：`
  - or contains strong world-rule keywords such as `所有`, `禁止`, `必须`, `世界规则`, `不可违背`
- Inspiration candidate:
  - line starts with `灵感：`, `脑洞：`, `片段：`, `桥段：`, `对白：`
  - fallback for meaningful lines that do not fit character/canon

### Conflict detection

P0 detects only lightweight conflicts and overlaps:

- `canon_overlap`: imported line shares notable keywords with `world.truth_canon`.
- `character_duplicate`: character candidate title matches an existing character name.
- `approved_chapter_overlap`: imported line mentions a title or excerpt term from an approved chapter.

All conflicts are warnings in P0. They block nothing, but they must appear in preview and batch records.

## 5. Frontend Design

Add a compact import panel to the world workspace tools area.

Component:

- `frontend/src/world/WorldImportPanel.tsx`

Responsibilities:

1. Explain in Chinese that imported material enters candidate pools first and will not rewrite canon automatically.
2. Let user choose source type: 粘贴文本 / Markdown / txt.
3. Let user enter source title and content.
4. Call preview endpoint.
5. Render grouped preview cards:
   - 灵感池候选
   - 角色池候选
   - canon 候选
6. Render conflict warnings.
7. Confirm selected preview assets. P0 can select all by default and confirm all returned assets.
8. Show recent import batches and audit summary.

Mount point:

- Add the panel to `WorldPage.tsx` in the existing tools/workspace area, near search/tags/timeline panels. Keep it secondary to the main chapter/world operations flow.

## 6. Safety and Canon Boundary

P0 must preserve these invariants:

- Preview does not write anything.
- Confirm only writes `ImportBatch`, `ImportCandidateAsset`, and an `EventLog` audit record.
- Confirm does not update `world.truth_canon`.
- Confirm does not increment `world.world_version`.
- Confirm does not mutate character tables or current projections.
- Candidate assets remain explicitly marked as `candidate`.

## 7. Testing Strategy

### Backend RED/GREEN tests

Create `backend/tests/test_import_node.py` covering:

1. Preview classifies pasted/Markdown-like material into canon, character, and inspiration candidates.
2. Preview reports conflicts with existing canon and duplicate character names.
3. Confirm writes candidate assets and an audit event without mutating `truth_canon` or incrementing `world_version`.
4. Non-owner cannot preview or confirm.

### Frontend RED/GREEN tests

Create `frontend/src/world/WorldImportPanel.test.tsx` covering:

1. Chinese safety copy says material enters candidate pools and does not automatically rewrite canon.
2. Preview renders grouped asset cards and conflict warnings.
3. Confirm calls the API with preview assets and shows batch/audit result.

Update API client/types tests only if the new client functions need explicit coverage.

## 8. Inline Self-Review Checklist

Before commit:

- The import node is not described or implemented as a generic workflow.
- No direct formal canon mutation exists.
- Preview and confirm are separate.
- Source/batch/audit records exist.
- Backend tests cover safety invariants.
- Frontend copy is Chinese and user-facing.
- No subagents or dynamic workflows were used.
