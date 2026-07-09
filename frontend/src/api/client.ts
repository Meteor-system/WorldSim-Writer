import type {
  ApprovalConsistencyResponse,
  ApprovalPreviewResponse,
  ApprovalReadinessResponse,
  ApproveRequest,
  ArcPlanResponse,
  BeatCard,
  ChapterHistoryDetailResponse,
  ChapterExecutionContext,
  ChapterHistoryResponse,
  ChapterMaterialReference,
  ChapterPipelineResponse,
  Character,
  CharacterArcReportResponse,
  CharacterCreate,
  CharacterRelation,
  CharacterRelationCreate,
  CharacterRelationUpdate,
  CharacterUpdate,
  CriticIssue,
  CriticReportResponse,
  CritiqueResponse,
  DraftDiffResponse,
  DraftResponse,
  EventLogListResponse,
  Foreshadow,
  ForeshadowCreate,
  ForeshadowEvent,
  ForeshadowLedgerResponse,
  ForeshadowStatus,
  ForeshadowUpdate,
  ImportBatchListResponse,
  ImportConfirmRequest,
  ImportConfirmResponse,
  ImportPreviewRequest,
  ImportPreviewResponse,
  NarrativeHealthResponse,
  NextChapterPrepResponse,
  OpenThreadsResponse,
  OutlineResponse,
  ParagraphReviseRequest,
  ReviseDraftRequest,
  SerialPlanResponse,
  StaleForeshadow,
  StoryArcResponse,
  StyleHandbookPreviewRequest,
  StyleHandbookPreviewResponse,
  StyleHandbookReference,
  ObjectTagBulkAssignResponse,
  ObjectTagResponse,
  TagDetailResponse,
  TagListResponse,
  TagMergeRequest,
  TagMergeResponse,
  TagResponse,
  TagUpdateRequest,
  WorldCreateRequest,
  WorldCreationDraftResponse,
  WorldCreationMaterialReference,
  WorldMarkdownExportResponse,
  WorldPulseResponse,
  WorldStatusUpdateRequest,
  WorldSummary,
  WorldSearchResponse,
  WorldSeedDetail,
  WorldSeedListResponse,
  WorldSnapshotCompareResponse,
  WorldSnapshotDetailResponse,
  WorldSnapshotListResponse,
  WorldSnapshotSummary,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

type ApiError = Error & { status?: number };

function formatApiError(body: string): string {
  if (!body) return '请求失败';
  try {
    const parsed = JSON.parse(body) as { detail?: unknown };
    if (typeof parsed.detail === 'string') return parsed.detail;
    if (Array.isArray(parsed.detail)) {
      return parsed.detail
        .map((item) => {
          if (typeof item === 'object' && item && 'msg' in item) {
            return String((item as { msg: unknown }).msg);
          }
          return String(item);
        })
        .join('；');
    }
  } catch {
    return body;
  }
  return body;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('worldsim_token');
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = new Error(formatApiError(await response.text())) as ApiError;
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

/* ── Worlds ── */

function cleanWorldCreateRequest(data: WorldCreateRequest): WorldCreateRequest {
  return {
    title: data.title,
    genre_template: data.genre_template,
    truth_canon: data.truth_canon,
    ...(data.tone_profile !== undefined ? { tone_profile: data.tone_profile } : {}),
    starter_assets: {
      characters: data.starter_assets.characters.map((character) => ({
        name: character.name,
        role_type: character.role_type,
        ...(character.status !== undefined ? { status: character.status } : {}),
        ...(character.public_profile !== undefined ? { public_profile: character.public_profile } : {}),
        ...(character.hidden_traits !== undefined ? { hidden_traits: character.hidden_traits } : {}),
        ...(character.destiny_flag !== undefined ? { destiny_flag: character.destiny_flag } : {}),
        ...(character.current_goals !== undefined ? { current_goals: [...character.current_goals] } : {}),
      })),
      ...(data.starter_assets.relations !== undefined
        ? {
            relations: data.starter_assets.relations.map((relation) => ({
              source_index: relation.source_index,
              target_index: relation.target_index,
              relation_type: relation.relation_type,
              ...(relation.intensity !== undefined ? { intensity: relation.intensity } : {}),
              ...(relation.visibility !== undefined ? { visibility: relation.visibility } : {}),
            })),
          }
        : {}),
      ...(data.starter_assets.foreshadows !== undefined
        ? {
            foreshadows: data.starter_assets.foreshadows.map((foreshadow) => ({
              title: foreshadow.title,
              description: foreshadow.description,
              foreshadow_type: foreshadow.foreshadow_type,
              ...(foreshadow.status !== undefined ? { status: foreshadow.status } : {}),
              ...(foreshadow.urgency_level !== undefined ? { urgency_level: foreshadow.urgency_level } : {}),
              ...(foreshadow.related_character_indexes !== undefined
                ? { related_character_indexes: [...foreshadow.related_character_indexes] }
                : {}),
              ...(foreshadow.expected_resolution_window !== undefined
                ? { expected_resolution_window: foreshadow.expected_resolution_window }
                : {}),
            })),
          }
        : {}),
    },
  };
}

export function createWorld(data: WorldCreateRequest) {
  return apiRequest<{ id: number }>('/worlds', {
    method: 'POST',
    body: JSON.stringify(cleanWorldCreateRequest(data)),
  });
}

function cleanWorldCreationMaterialReferences(
  materialReferences?: WorldCreationMaterialReference[],
): WorldCreationMaterialReference[] {
  return (materialReferences ?? [])
    .slice(0, 3)
    .map((reference) => ({
      source: 'import_node' as const,
      ...(reference.asset_id !== undefined ? { asset_id: reference.asset_id ?? null } : {}),
      title: reference.title,
      summary: reference.summary,
      ...(reference.asset_pool !== undefined ? { asset_pool: reference.asset_pool ?? null } : {}),
      ...(reference.source_rights !== undefined ? { source_rights: reference.source_rights ?? null } : {}),
    }))
    .filter((reference) => reference.title.trim() && reference.summary.trim());
}

function cleanChapterMaterialReference(reference: ChapterMaterialReference): ChapterMaterialReference {
  return {
    asset_id: reference.asset_id,
    batch_id: reference.batch_id,
    asset_pool: reference.asset_pool,
    title: reference.title,
    summary: reference.summary,
    source_title: reference.source_title,
    source_type: reference.source_type,
    created_at: reference.created_at,
    safety_note: reference.safety_note,
  };
}

function cleanStyleHandbookDimension(
  dimension: StyleHandbookReference['handbook']['narrative_pacing'],
): StyleHandbookReference['handbook']['narrative_pacing'] {
  return {
    label: dimension.label,
    value: dimension.value,
    evidence: dimension.evidence ?? null,
  };
}

function cleanStyleHandbookReference(reference: StyleHandbookReference): StyleHandbookReference {
  const { handbook } = reference;
  return {
    source_title: reference.source_title,
    source_rights: reference.source_rights,
    handbook: {
      narrative_pacing: cleanStyleHandbookDimension(handbook.narrative_pacing),
      language_density: cleanStyleHandbookDimension(handbook.language_density),
      dialogue_ratio: cleanStyleHandbookDimension(handbook.dialogue_ratio),
      scene_progression: cleanStyleHandbookDimension(handbook.scene_progression),
      suspense_structure: cleanStyleHandbookDimension(handbook.suspense_structure),
      relationship_tension: cleanStyleHandbookDimension(handbook.relationship_tension),
      foreshadowing_pattern: cleanStyleHandbookDimension(handbook.foreshadowing_pattern),
      do_guidelines: [...(handbook.do_guidelines ?? [])],
      avoid_guidelines: [...(handbook.avoid_guidelines ?? [])],
      originality_guidelines: [...(handbook.originality_guidelines ?? [])],
    },
    safety_notes: [...(reference.safety_notes ?? [])],
  };
}

function cleanChapterExecutionContext(context: ChapterExecutionContext): ChapterExecutionContext {
  return {
    source: context.source,
    source_world_version: context.source_world_version,
    next_chapter_number: context.next_chapter_number,
    goal: context.goal,
    recommended_pov: {
      character_id: context.recommended_pov.character_id,
      name: context.recommended_pov.name,
    },
    source_signals: [...(context.source_signals ?? [])],
    priority_characters: (context.priority_characters ?? []).map((character) => ({
      character_id: character.character_id,
      name: character.name,
      role_type: character.role_type,
      status: character.status,
      reason: character.reason,
    })),
    priority_foreshadows: (context.priority_foreshadows ?? []).map((foreshadow) => ({
      foreshadow_id: foreshadow.foreshadow_id,
      title: foreshadow.title,
      status: foreshadow.status,
      urgency_level: foreshadow.urgency_level,
      reason: foreshadow.reason,
    })),
    progression_hints: (context.progression_hints ?? []).map((hint) => ({
      hint_type: hint.hint_type,
      priority: hint.priority,
      title: hint.title,
      rationale: hint.rationale,
      suggested_next_beat: hint.suggested_next_beat,
      related_character_ids: [...(hint.related_character_ids ?? [])],
      related_foreshadow_ids: [...(hint.related_foreshadow_ids ?? [])],
      can_seed_next_chapter_goal: hint.can_seed_next_chapter_goal,
    })),
    continuity_warnings: (context.continuity_warnings ?? []).map((warning) => ({
      severity: warning.severity,
      category: warning.category,
      message: warning.message,
      related_character_ids: [...(warning.related_character_ids ?? [])],
      related_foreshadow_ids: [...(warning.related_foreshadow_ids ?? [])],
    })),
    recent_events: (context.recent_events ?? []).map((event) => ({
      id: event.id,
      event_type: event.event_type,
      world_version_before: event.world_version_before,
      world_version_after: event.world_version_after,
      created_at: event.created_at,
    })),
    material_references: (context.material_references ?? []).map(cleanChapterMaterialReference),
    ...(context.style_handbook_reference !== undefined
      ? {
          style_handbook_reference: context.style_handbook_reference
            ? cleanStyleHandbookReference(context.style_handbook_reference)
            : null,
        }
      : {}),
  };
}

export function draftWorldFromBrief(
  brief: string,
  styleHandbookReference?: StyleHandbookReference | null,
  variantCount?: number,
  materialReferences?: WorldCreationMaterialReference[],
) {
  const cleanedMaterialReferences = cleanWorldCreationMaterialReferences(materialReferences);
  const cleanedStyleHandbookReference = styleHandbookReference ? cleanStyleHandbookReference(styleHandbookReference) : null;
  return apiRequest<WorldCreationDraftResponse>('/worlds/draft-from-brief', {
    method: 'POST',
    body: JSON.stringify({
      brief,
      ...(cleanedStyleHandbookReference ? { style_handbook_reference: cleanedStyleHandbookReference } : {}),
      ...(variantCount ? { variant_count: variantCount } : {}),
      ...(cleanedMaterialReferences.length ? { material_references: cleanedMaterialReferences } : {}),
    }),
  });
}

export function createSampleWorld() {
  return apiRequest<{ id: number }>('/worlds/from-template', {
    method: 'POST',
    body: '{}',
  });
}

export function listWorldSeeds() {
  return apiRequest<WorldSeedListResponse>('/worlds/seeds');
}

export function getWorldSeed(seedKey: string) {
  return apiRequest<WorldSeedDetail>(`/worlds/seeds/${seedKey}`);
}

export function createWorldFromSeed(seedKey: string) {
  return apiRequest<{ id: number }>(`/worlds/from-seed/${seedKey}`, {
    method: 'POST',
    body: '{}',
  });
}

export function updateWorldStatus(worldId: number, data: WorldStatusUpdateRequest) {
  return apiRequest<WorldSummary>(`/worlds/${worldId}/status`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function getWorldEvents(worldId: number, params: { event_type?: string; limit?: number; offset?: number } = {}) {
  const search = new URLSearchParams();
  if (params.event_type) search.set('event_type', params.event_type);
  if (params.limit !== undefined) search.set('limit', String(params.limit));
  if (params.offset !== undefined) search.set('offset', String(params.offset));
  const query = search.toString();
  return apiRequest<EventLogListResponse>(`/worlds/${worldId}/events${query ? `?${query}` : ''}`);
}

export function searchWorld(worldId: number, params: { q: string; object_types?: string[]; tags?: string[]; limit?: number }) {
  const search = new URLSearchParams({ q: params.q });
  if (params.object_types?.length) search.set('object_types', params.object_types.join(','));
  if (params.tags?.length) search.set('tags', params.tags.join(','));
  if (params.limit !== undefined) search.set('limit', String(params.limit));
  return apiRequest<WorldSearchResponse>(`/worlds/${worldId}/search?${search.toString()}`);
}

export function listWorldTags(worldId: number) {
  return apiRequest<TagListResponse>(`/worlds/${worldId}/tags`);
}

export function createWorldTag(worldId: number, data: { name: string; color?: string }) {
  return apiRequest<TagResponse>(`/worlds/${worldId}/tags`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updateWorldTag(worldId: number, tagId: number, data: TagUpdateRequest) {
  return apiRequest<TagResponse>(`/worlds/${worldId}/tags/${tagId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function mergeWorldTag(worldId: number, sourceTagId: number, data: TagMergeRequest) {
  return apiRequest<TagMergeResponse>(`/worlds/${worldId}/tags/${sourceTagId}/merge`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getWorldTag(worldId: number, tagId: number) {
  return apiRequest<TagDetailResponse>(`/worlds/${worldId}/tags/${tagId}`);
}

export function assignWorldTag(worldId: number, tagId: number, data: { object_type: string; object_id: number }) {
  return apiRequest<ObjectTagResponse>(`/worlds/${worldId}/tags/${tagId}/objects`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function bulkAssignWorldTag(worldId: number, tagId: number, data: { object_type: string; object_ids: number[] }) {
  return apiRequest<ObjectTagBulkAssignResponse>(`/worlds/${worldId}/tags/${tagId}/objects/bulk`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function unassignWorldTag(worldId: number, tagId: number, objectType: string, objectId: number) {
  return apiRequest<unknown>(`/worlds/${worldId}/tags/${tagId}/objects/${objectType}/${objectId}`, { method: 'DELETE' });
}

export function deleteWorldTag(worldId: number, tagId: number) {
  return apiRequest<unknown>(`/worlds/${worldId}/tags/${tagId}`, { method: 'DELETE' });
}

export function generateStoryArc(worldId: number) {
  return apiRequest<StoryArcResponse>(`/worlds/${worldId}/story-arc`, {
    method: 'POST',
    body: '{}',
  });
}

export function getSerialPlan(worldId: number, limit = 3) {
  return apiRequest<SerialPlanResponse>(`/worlds/${worldId}/serial-plan?limit=${limit}`);
}

export function suggestGoal(worldId: number) {
  return apiRequest<{ goal: string }>(`/worlds/${worldId}/suggest-goal`, {
    method: 'POST',
    body: '{}',
  });
}

export function previewWorldImport(worldId: number, data: ImportPreviewRequest) {
  return apiRequest<ImportPreviewResponse>(`/worlds/${worldId}/imports/preview`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function previewStyleHandbook(worldId: number, data: StyleHandbookPreviewRequest) {
  return apiRequest<StyleHandbookPreviewResponse>(`/worlds/${worldId}/imports/style-handbook/preview`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function confirmWorldImport(worldId: number, data: ImportConfirmRequest) {
  return apiRequest<ImportConfirmResponse>(`/worlds/${worldId}/imports/confirm`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function listWorldImports(worldId: number) {
  return apiRequest<ImportBatchListResponse>(`/worlds/${worldId}/imports`);
}

/* ── Narrative pipeline ── */

export function createChapter(worldId: number, data: { chapter_goal: string; title?: string; execution_context?: ChapterExecutionContext }) {
  const executionContext = data.execution_context ? cleanChapterExecutionContext(data.execution_context) : undefined;
  return apiRequest<ChapterPipelineResponse>(`/worlds/${worldId}/chapters`, {
    method: 'POST',
    body: JSON.stringify({
      chapter_goal: data.chapter_goal,
      ...(data.title !== undefined ? { title: data.title } : {}),
      ...(executionContext ? { execution_context: executionContext } : {}),
    }),
  });
}

export function generateOutline(chapterId: number, data: { chapter_context?: string } = {}) {
  return apiRequest<OutlineResponse>(`/chapters/${chapterId}/outline`, {
    method: 'POST',
    body: JSON.stringify({
      ...(data.chapter_context !== undefined ? { chapter_context: data.chapter_context } : {}),
    }),
  });
}

export function writeChapter(chapterId: number, data: { outline_beats?: BeatCard[] } = {}) {
  return apiRequest<DraftResponse>(`/chapters/${chapterId}/write`, {
    method: 'POST',
    body: JSON.stringify({
      ...(data.outline_beats !== undefined ? { outline_beats: data.outline_beats } : {}),
    }),
  });
}

export function stashDraft(chapterId: number, data: { note?: string } = {}) {
  return apiRequest<DraftResponse>(`/chapters/${chapterId}/draft/stash`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function reviseParagraph(chapterId: number, data: ParagraphReviseRequest) {
  return apiRequest<DraftResponse>(`/chapters/${chapterId}/draft/paragraph`, {
    method: 'POST',
    body: JSON.stringify({
      paragraph_index: data.paragraph_index,
      mode: data.mode,
      ...(data.instruction !== undefined ? { instruction: data.instruction } : {}),
    }),
  });
}

export function reviseDraft(chapterId: number, data: ReviseDraftRequest) {
  return apiRequest<DraftResponse>(`/chapters/${chapterId}/draft/revise`, {
    method: 'POST',
    body: JSON.stringify({ instruction: data.instruction }),
  });
}

export function getDraftVersion(chapterId: number, draftVersion: number) {
  return apiRequest<DraftResponse>(`/chapters/${chapterId}/drafts/${draftVersion}`);
}

export function getDraftDiff(chapterId: number, fromVersion: number, toVersion: number) {
  const search = new URLSearchParams({ from: String(fromVersion), to: String(toVersion) });
  return apiRequest<DraftDiffResponse>(`/chapters/${chapterId}/drafts/diff?${search.toString()}`);
}

export function getApprovalPreview(chapterId: number) {
  return apiRequest<ApprovalPreviewResponse>(`/chapters/${chapterId}/approval-preview`);
}

function cleanApproveRequest(data: ApproveRequest = {}): ApproveRequest {
  return {
    ...(data.draft_version !== undefined ? { draft_version: data.draft_version } : {}),
    ...(data.selected_character_change_indexes !== undefined
      ? { selected_character_change_indexes: [...data.selected_character_change_indexes] }
      : {}),
    ...(data.selected_foreshadow_change_indexes !== undefined
      ? { selected_foreshadow_change_indexes: [...data.selected_foreshadow_change_indexes] }
      : {}),
  };
}

export function checkApprovalConsistency(chapterId: number, data: ApproveRequest = {}) {
  return apiRequest<ApprovalConsistencyResponse>(`/chapters/${chapterId}/approval-consistency`, {
    method: 'POST',
    body: JSON.stringify(cleanApproveRequest(data)),
  });
}

export function getApprovalReadiness(chapterId: number) {
  return apiRequest<ApprovalReadinessResponse>(`/chapters/${chapterId}/approval-readiness`);
}

export function approveChapter(chapterId: number, data: ApproveRequest = {}) {
  return apiRequest<ChapterPipelineResponse>(`/chapters/${chapterId}/approve`, {
    method: 'POST',
    body: JSON.stringify(cleanApproveRequest(data)),
  });
}

function legacyCritiqueToCriticReport(chapterId: number, response: CritiqueResponse): CriticReportResponse {
  const issues: CriticIssue[] = response.critique_report.issues.map((issue) => {
    const severity: CriticIssue['severity'] = issue.severity === 'high' || issue.severity === 'medium' || issue.severity === 'low' ? issue.severity : 'medium';
    return {
      severity,
      dimension: issue.category,
      message: issue.message,
      paragraph_index: null,
      suggested_action: null,
    };
  });
  return {
    chapter_id: chapterId,
    draft_version: 0,
    current_draft_version: 0,
    is_stale: false,
    overall_score: response.critique_report.score,
    summary: response.critique_report.suggestions[0] ?? 'Critic 报告已生成。',
    dimensions: {
      legacy_critique: {
        score: response.critique_report.score,
        summary: '来自兼容 critique endpoint 的报告。',
        issues,
        suggestions: response.critique_report.suggestions,
      },
    },
    issues,
    suggestions: response.critique_report.suggestions,
    created_at: new Date().toISOString(),
  };
}

export async function generateCriticReport(chapterId: number) {
  try {
    return await apiRequest<CriticReportResponse>(`/chapters/${chapterId}/critic-report`, {
      method: 'POST',
      body: '{}',
    });
  } catch (error) {
    if ((error as ApiError).status !== 404) throw error;
    const legacy = await critiqueChapter(chapterId);
    return legacyCritiqueToCriticReport(chapterId, legacy);
  }
}

export function getCriticReport(chapterId: number) {
  return apiRequest<CriticReportResponse>(`/chapters/${chapterId}/critic-report`);
}

export function generateCharacterArcReport(chapterId: number) {
  return apiRequest<CharacterArcReportResponse>(`/chapters/${chapterId}/character-arc-report`, {
    method: 'POST',
    body: '{}',
  });
}

export function getCharacterArcReport(chapterId: number) {
  return apiRequest<CharacterArcReportResponse>(`/chapters/${chapterId}/character-arc-report`);
}

export function getChapterHistory(worldId: number) {
  return apiRequest<ChapterHistoryResponse>(`/worlds/${worldId}/chapters/history`);
}

export function getChapterHistoryDetail(chapterId: number) {
  return apiRequest<ChapterHistoryDetailResponse>(`/chapters/${chapterId}/history`);
}

export function getNextChapterPrep(worldId: number) {
  return apiRequest<NextChapterPrepResponse>(`/worlds/${worldId}/next-chapter-prep`);
}

export function getNarrativeHealth(worldId: number) {
  return apiRequest<NarrativeHealthResponse>(`/worlds/${worldId}/narrative-health`);
}

export function getOpenThreads(worldId: number) {
  return apiRequest<OpenThreadsResponse>(`/worlds/${worldId}/open-threads`);
}

export function getWorldPulse(worldId: number) {
  return apiRequest<WorldPulseResponse>(`/worlds/${worldId}/pulse`);
}

export function getArcPlan(worldId: number) {
  return apiRequest<ArcPlanResponse>(`/worlds/${worldId}/arc-plan`);
}

export function createWorldSnapshot(worldId: number, data: { label?: string; note?: string } = {}) {
  return apiRequest<WorldSnapshotSummary>(`/worlds/${worldId}/snapshots`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function listWorldSnapshots(worldId: number) {
  return apiRequest<WorldSnapshotListResponse>(`/worlds/${worldId}/snapshots`);
}

export function getWorldSnapshot(snapshotId: number) {
  return apiRequest<WorldSnapshotDetailResponse>(`/snapshots/${snapshotId}`);
}

export function compareWorldSnapshots(baseSnapshotId: number, targetSnapshotId: number) {
  return apiRequest<WorldSnapshotCompareResponse>(`/snapshots/${baseSnapshotId}/compare/${targetSnapshotId}`);
}

export function exportWorldArchiveMarkdown(worldId: number) {
  return apiRequest<WorldMarkdownExportResponse>(`/worlds/${worldId}/export/markdown`, {
    method: 'POST',
    body: '{}',
  });
}

export function critiqueChapter(chapterId: number) {
  return apiRequest<CritiqueResponse>(`/chapters/${chapterId}/critique`, {
    method: 'POST',
    body: '{}',
  });
}

/* ── Characters ── */

export function createCharacter(worldId: number, data: CharacterCreate) {
  return apiRequest<Character>(`/worlds/${worldId}/characters`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getCharacters(worldId: number) {
  return apiRequest<Character[]>(`/worlds/${worldId}/characters`);
}

export function getCharacter(characterId: number) {
  return apiRequest<Character>(`/characters/${characterId}`);
}

export function updateCharacter(characterId: number, data: CharacterUpdate) {
  return apiRequest<Character>(`/characters/${characterId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export function deleteCharacter(characterId: number, editReason?: string) {
  const query = editReason ? `?${new URLSearchParams({ edit_reason: editReason }).toString()}` : '';
  return apiRequest<unknown>(`/characters/${characterId}${query}`, { method: 'DELETE' });
}

/* ── Relations ── */

export function createRelation(worldId: number, data: CharacterRelationCreate) {
  return apiRequest<CharacterRelation>(`/worlds/${worldId}/relations`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getRelations(worldId: number) {
  return apiRequest<CharacterRelation[]>(`/worlds/${worldId}/relations`);
}

export function getRelation(relationId: number) {
  return apiRequest<CharacterRelation>(`/relations/${relationId}`);
}

export function updateRelation(relationId: number, data: CharacterRelationUpdate) {
  return apiRequest<CharacterRelation>(`/relations/${relationId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export function deleteRelation(relationId: number, editReason?: string) {
  const query = editReason ? `?${new URLSearchParams({ edit_reason: editReason }).toString()}` : '';
  return apiRequest<unknown>(`/relations/${relationId}${query}`, { method: 'DELETE' });
}

/* ── Foreshadows ── */

export function createForeshadow(worldId: number, data: ForeshadowCreate) {
  return apiRequest<Foreshadow>(`/worlds/${worldId}/foreshadows`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getForeshadows(worldId: number, params: { status?: ForeshadowStatus[] } = {}) {
  const search = new URLSearchParams();
  if (params.status?.length) search.set('status', params.status.join(','));
  const query = search.toString();
  return apiRequest<Foreshadow[]>(`/worlds/${worldId}/foreshadows${query ? `?${query}` : ''}`);
}

export function getForeshadowTimeline(foreshadowId: number) {
  return apiRequest<ForeshadowEvent[]>(`/foreshadows/${foreshadowId}/timeline`);
}

export function getForeshadowLedger(worldId: number) {
  return apiRequest<ForeshadowLedgerResponse>(`/worlds/${worldId}/foreshadows/ledger`);
}

export function getStaleForeshadows(worldId: number) {
  return apiRequest<StaleForeshadow[]>(`/worlds/${worldId}/foreshadows/stale`);
}

export function getForeshadow(foreshadowId: number) {
  return apiRequest<Foreshadow>(`/foreshadows/${foreshadowId}`);
}

export function updateForeshadow(foreshadowId: number, data: ForeshadowUpdate) {
  return apiRequest<Foreshadow>(`/foreshadows/${foreshadowId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export function deleteForeshadow(foreshadowId: number, editReason?: string) {
  const query = editReason ? `?${new URLSearchParams({ edit_reason: editReason }).toString()}` : '';
  return apiRequest<unknown>(`/foreshadows/${foreshadowId}${query}`, { method: 'DELETE' });
}
