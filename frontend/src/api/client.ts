import type {
  ApprovalPreviewResponse,
  BeatCard,
  ChapterPipelineResponse,
  Character,
  CharacterCreate,
  CharacterRelation,
  CharacterRelationCreate,
  CharacterRelationUpdate,
  CharacterUpdate,
  CritiqueResponse,
  DraftDiffResponse,
  DraftResponse,
  EventLog,
  Foreshadow,
  ForeshadowCreate,
  ForeshadowEvent,
  ForeshadowStatus,
  ForeshadowUpdate,
  OutlineResponse,
  ParagraphReviseRequest,
  StaleForeshadow,
  StoryArcResponse,
  WorldCreateRequest,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

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
  if (!response.ok) throw new Error(formatApiError(await response.text()));
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

/* ── Worlds ── */

export function createWorld(data: WorldCreateRequest) {
  return apiRequest<{ id: number }>('/worlds', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getWorldEvents(worldId: number, params: { event_type?: string; limit?: number; offset?: number } = {}) {
  const search = new URLSearchParams();
  if (params.event_type) search.set('event_type', params.event_type);
  if (params.limit !== undefined) search.set('limit', String(params.limit));
  if (params.offset !== undefined) search.set('offset', String(params.offset));
  const query = search.toString();
  return apiRequest<{ items: EventLog[]; total: number; limit: number; offset: number }>(`/worlds/${worldId}/events${query ? `?${query}` : ''}`);
}

export function generateStoryArc(worldId: number) {
  return apiRequest<StoryArcResponse>(`/worlds/${worldId}/story-arc`, {
    method: 'POST',
    body: '{}',
  });
}

export function suggestGoal(worldId: number) {
  return apiRequest<{ goal: string }>(`/worlds/${worldId}/suggest-goal`, {
    method: 'POST',
    body: '{}',
  });
}

/* ── Narrative pipeline ── */

export function createChapter(worldId: number, data: { chapter_goal: string; title?: string }) {
  return apiRequest<ChapterPipelineResponse>(`/worlds/${worldId}/chapters`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function generateOutline(chapterId: number, data: { chapter_context?: string } = {}) {
  return apiRequest<OutlineResponse>(`/chapters/${chapterId}/outline`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function writeChapter(chapterId: number, data: { outline_beats?: BeatCard[] } = {}) {
  return apiRequest<DraftResponse>(`/chapters/${chapterId}/write`, {
    method: 'POST',
    body: JSON.stringify(data),
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
    body: JSON.stringify(data),
  });
}

export function getDraftDiff(chapterId: number, fromVersion: number, toVersion: number) {
  const search = new URLSearchParams({ from: String(fromVersion), to: String(toVersion) });
  return apiRequest<DraftDiffResponse>(`/chapters/${chapterId}/drafts/diff?${search.toString()}`);
}

export function getApprovalPreview(chapterId: number) {
  return apiRequest<ApprovalPreviewResponse>(`/chapters/${chapterId}/approval-preview`);
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
