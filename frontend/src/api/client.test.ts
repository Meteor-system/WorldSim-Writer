import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createRelation,
  deleteCharacter,
  deleteForeshadow,
  deleteRelation,
  generateCriticReport,
  getApprovalPreview,
  getCriticReport,
  getDraftDiff,
  getRelations,
  reviseParagraph,
  stashDraft,
  updateRelation,
} from './client';

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
}

describe('relation API helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('creates and updates relations with edit_reason payloads', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 9, source_character_id: 1, target_character_id: 2, relation_type: 'ally', intensity: 4, visibility: 'private' }))
      .mockResolvedValueOnce(jsonResponse({ id: 9, source_character_id: 1, target_character_id: 2, relation_type: 'rival', intensity: 5, visibility: 'public' }));
    vi.stubGlobal('fetch', fetchMock);

    await createRelation(7, {
      source_character_id: 1,
      target_character_id: 2,
      relation_type: 'ally',
      intensity: 4,
      visibility: 'private',
      edit_reason: '新增关系备注',
    });
    await updateRelation(9, {
      relation_type: 'rival',
      intensity: 5,
      visibility: 'public',
      edit_reason: '关系转折备注',
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/worlds/7/relations',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          source_character_id: 1,
          target_character_id: 2,
          relation_type: 'ally',
          intensity: 4,
          visibility: 'private',
          edit_reason: '新增关系备注',
        }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/relations/9',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({
          relation_type: 'rival',
          intensity: 5,
          visibility: 'public',
          edit_reason: '关系转折备注',
        }),
      }),
    );
  });

  it('lists relations and sends delete edit reasons as query parameters', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);

    await getRelations(7);
    await deleteRelation(9, '删除关系备注');
    await deleteCharacter(3, '删除角色备注');
    await deleteForeshadow(4, '删除伏笔备注');

    expect(fetchMock).toHaveBeenNthCalledWith(1, 'http://localhost:8000/worlds/7/relations', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://localhost:8000/relations/9?edit_reason=%E5%88%A0%E9%99%A4%E5%85%B3%E7%B3%BB%E5%A4%87%E6%B3%A8', expect.objectContaining({ method: 'DELETE' }));
    expect(fetchMock).toHaveBeenNthCalledWith(3, 'http://localhost:8000/characters/3?edit_reason=%E5%88%A0%E9%99%A4%E8%A7%92%E8%89%B2%E5%A4%87%E6%B3%A8', expect.objectContaining({ method: 'DELETE' }));
    expect(fetchMock).toHaveBeenNthCalledWith(4, 'http://localhost:8000/foreshadows/4?edit_reason=%E5%88%A0%E9%99%A4%E4%BC%8F%E7%AC%94%E5%A4%87%E6%B3%A8', expect.objectContaining({ method: 'DELETE' }));
  });
});

describe('draft versioning API helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls draft stash, paragraph revision, diff, and approval preview endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ draft_version: 2 }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 3 }))
      .mockResolvedValueOnce(jsonResponse({ diff_lines: [] }))
      .mockResolvedValueOnce(jsonResponse({ version_conflict: false }));
    vi.stubGlobal('fetch', fetchMock);

    await stashDraft(11, { note: '暂存当前草稿' });
    await reviseParagraph(11, { paragraph_index: 1, mode: 'rewrite', instruction: '增强悬念' });
    await getDraftDiff(11, 1, 3);
    await getApprovalPreview(11);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/chapters/11/draft/stash',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ note: '暂存当前草稿' }) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/chapters/11/draft/paragraph',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ paragraph_index: 1, mode: 'rewrite', instruction: '增强悬念' }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(3, 'http://localhost:8000/chapters/11/drafts/diff?from=1&to=3', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(4, 'http://localhost:8000/chapters/11/approval-preview', expect.any(Object));
  });

  it('calls critic report generate and fetch endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ overall_score: 78 }))
      .mockResolvedValueOnce(jsonResponse({ overall_score: 78 }));
    vi.stubGlobal('fetch', fetchMock);

    await generateCriticReport(11);
    await getCriticReport(11);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/chapters/11/critic-report',
      expect.objectContaining({ method: 'POST', body: '{}' }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://localhost:8000/chapters/11/critic-report', expect.any(Object));
  });
});
