import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  checkApprovalConsistency,
  createRelation,
  createSampleWorld,
  createWorld,
  deleteCharacter,
  deleteForeshadow,
  deleteRelation,
  generateCharacterArcReport,
  generateCriticReport,
  getApprovalPreview,
  getCharacterArcReport,
  getChapterHistory,
  getChapterHistoryDetail,
  getCriticReport,
  getNextChapterPrep,
  getForeshadowLedger,
  getNarrativeHealth,
  exportWorldArchiveMarkdown,
  getDraftDiff,
  getWorldEvents,
  getDraftVersion,
  searchWorld,
  getRelations,
  reviseDraft,
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

describe('world creation API helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls custom and sample world creation endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 7 }))
      .mockResolvedValueOnce(jsonResponse({ id: 8 }));
    vi.stubGlobal('fetch', fetchMock);
    const payload = {
      title: '群星边境',
      genre_template: 'sci_fi',
      truth_canon: '跃迁灯塔正在失控。',
      tone_profile: { style: '冷峻太空歌剧' },
      starter_assets: {
        characters: [{ name: '许砚', role_type: 'protagonist' }],
        relations: [],
        foreshadows: [],
      },
    };

    await createWorld(payload);
    await createSampleWorld();

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/worlds',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(payload) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/worlds/from-template',
      expect.objectContaining({ method: 'POST', body: '{}' }),
    );
  });
});

describe('world event API helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls event list endpoint with filters and pagination', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      items: [],
      total: 0,
      limit: 10,
      offset: 20,
      summary: { total: 0, event_type_counts: {}, latest_world_version: 1 },
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await getWorldEvents(7, { event_type: 'character_change', limit: 10, offset: 20 });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/7/events?event_type=character_change&limit=10&offset=20',
      expect.any(Object),
    );
    expect(response.summary.latest_world_version).toBe(1);
  });
});

describe('world search API helper', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls world search endpoint with query, object filters, and limit', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      world_id: 7,
      query: '灯塔',
      object_type_counts: { character: 1 },
      results: [],
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await searchWorld(7, { q: '灯塔', object_types: ['character', 'event'], limit: 10 });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/7/search?q=%E7%81%AF%E5%A1%94&object_types=character%2Cevent&limit=10',
      expect.any(Object),
    );
    expect(response.object_type_counts).toEqual({ character: 1 });
  });
});

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

  it('calls draft stash, paragraph revision, full revision, exact version, diff, approval preview, and approval consistency endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ draft_version: 2 }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 3 }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 4 }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 1 }))
      .mockResolvedValueOnce(jsonResponse({ diff_lines: [] }))
      .mockResolvedValueOnce(jsonResponse({ version_conflict: false }))
      .mockResolvedValueOnce(jsonResponse({ consistency_warnings: [] }));
    vi.stubGlobal('fetch', fetchMock);

    await stashDraft(11, { note: '暂存当前草稿' });
    await reviseParagraph(11, { paragraph_index: 1, mode: 'rewrite', instruction: '增强悬念' });
    await reviseDraft(11, { instruction: '补足试探过程' });
    await getDraftVersion(11, 1);
    await getDraftDiff(11, 1, 3);
    await getApprovalPreview(11);
    await checkApprovalConsistency(11, { draft_version: 1, selected_character_change_indexes: [0], selected_foreshadow_change_indexes: [] });

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
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      'http://localhost:8000/chapters/11/draft/revise',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ instruction: '补足试探过程' }) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(4, 'http://localhost:8000/chapters/11/drafts/1', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(5, 'http://localhost:8000/chapters/11/drafts/diff?from=1&to=3', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(6, 'http://localhost:8000/chapters/11/approval-preview', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(
      7,
      'http://localhost:8000/chapters/11/approval-consistency',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ draft_version: 1, selected_character_change_indexes: [0], selected_foreshadow_change_indexes: [] }),
      }),
    );
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

  it('falls back to the legacy critique endpoint when critic-report is not available', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Not Found' }), { status: 404, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(jsonResponse({
        chapter_id: 11,
        critique_report: {
          score: 84,
          issues: [{ category: 'character_voice', severity: 'medium', message: '沈微霜台词可以更克制。' }],
          suggestions: ['加强林砚担心牵连师门的内心压力。'],
          consistency_check: { world_rule_adherence: 'pass' },
        },
        status: 'reviewing',
      }));
    vi.stubGlobal('fetch', fetchMock);

    const report = await generateCriticReport(11);

    expect(fetchMock).toHaveBeenNthCalledWith(1, 'http://localhost:8000/chapters/11/critic-report', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/chapters/11/critique',
      expect.objectContaining({ method: 'POST', body: '{}' }),
    );
    expect(report.overall_score).toBe(84);
    expect(report.issues[0]).toMatchObject({ severity: 'medium', dimension: 'character_voice', message: '沈微霜台词可以更克制。' });
  });

  it('calls character arc report generate and fetch endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ summary: '角色弧线推进清晰。' }))
      .mockResolvedValueOnce(jsonResponse({ summary: '角色弧线推进清晰。' }));
    vi.stubGlobal('fetch', fetchMock);

    await generateCharacterArcReport(11);
    await getCharacterArcReport(11);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/chapters/11/character-arc-report',
      expect.objectContaining({ method: 'POST', body: '{}' }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://localhost:8000/chapters/11/character-arc-report', expect.any(Object));
  });

  it('calls narrative control center chapter history, prep, foreshadow ledger, and markdown export endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, chapters: [] }))
      .mockResolvedValueOnce(jsonResponse({ id: 11, events: [] }))
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, suggested_goal: '推进湿信线索' }))
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, summary: { total: 0 } }))
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, files: [] }));
    vi.stubGlobal('fetch', fetchMock);

    await getChapterHistory(7);
    await getChapterHistoryDetail(11);
    await getNextChapterPrep(7);
    await getForeshadowLedger(7);
    await exportWorldArchiveMarkdown(7);

    expect(fetchMock).toHaveBeenNthCalledWith(1, 'http://localhost:8000/worlds/7/chapters/history', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://localhost:8000/chapters/11/history', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(3, 'http://localhost:8000/worlds/7/next-chapter-prep', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(4, 'http://localhost:8000/worlds/7/foreshadows/ledger', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(5, 'http://localhost:8000/worlds/7/export/markdown', expect.objectContaining({ method: 'POST', body: '{}' }));
  });

  it('calls narrative health endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      world_id: 7,
      world_version: 2,
      health_score: 84,
      status: 'watch',
      summary: {},
      metrics: [],
      risks: [],
      suggested_actions: [],
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await getNarrativeHealth(7);

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/worlds/7/narrative-health', expect.any(Object));
    expect(response.health_score).toBe(84);
  });
});
