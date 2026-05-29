import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createRelation,
  deleteCharacter,
  deleteForeshadow,
  deleteRelation,
  getRelations,
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
