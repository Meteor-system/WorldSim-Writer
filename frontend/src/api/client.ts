import type {
  BeatCard,
  ChapterPipelineResponse,
  Character,
  CharacterCreate,
  CharacterUpdate,
  CritiqueResponse,
  DraftResponse,
  EventLog,
  Foreshadow,
  ForeshadowCreate,
  ForeshadowUpdate,
  OutlineResponse,
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

export function deleteCharacter(characterId: number) {
  return apiRequest<unknown>(`/characters/${characterId}`, { method: 'DELETE' });
}

/* ── Foreshadows ── */

export function createForeshadow(worldId: number, data: ForeshadowCreate) {
  return apiRequest<Foreshadow>(`/worlds/${worldId}/foreshadows`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getForeshadows(worldId: number) {
  return apiRequest<Foreshadow[]>(`/worlds/${worldId}/foreshadows`);
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

export function deleteForeshadow(foreshadowId: number) {
  return apiRequest<unknown>(`/foreshadows/${foreshadowId}`, { method: 'DELETE' });
}
