import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  checkApprovalConsistency,
  compareWorldSnapshots,
  createRelation,
  createSampleWorld,
  createWorld,
  createWorldFromSeed,
  createWorldTag,
  draftWorldFromBrief,
  updateWorldTag,
  mergeWorldTag,
  assignWorldTag,
  bulkAssignWorldTag,
  deleteCharacter,
  deleteForeshadow,
  deleteRelation,
  deleteWorldTag,
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
  getOpenThreads,
  getWorldPulse,
  getArcPlan,
  exportWorldArchiveMarkdown,
  getDraftDiff,
  getWorldEvents,
  getDraftVersion,
  previewStyleHandbook,
  getWorldSeed,
  getWorldTag,
  listWorldSeeds,
  listWorldTags,
  searchWorld,
  unassignWorldTag,
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

  it('calls one-sentence world draft endpoint without creating a world', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      source_brief: '一个所有人出生时都会被分配死因的王国',
      draft: {
        title: '死因王国',
        genre_template: 'fantasy',
        truth_canon: '每个人出生时都会获得一个未来死因。',
        starter_assets: { characters: [{ name: '伊莱', role_type: 'protagonist' }] },
      },
      first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      generation_notes: ['已生成创建草稿。'],
      safety_notes: ['确认前不会创建世界。'],
    }));
    vi.stubGlobal('fetch', fetchMock);

    const result = await draftWorldFromBrief('一个所有人出生时都会被分配死因的王国');

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/draft-from-brief',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ brief: '一个所有人出生时都会被分配死因的王国' }) }),
    );
    expect(result.draft.title).toBe('死因王国');
  });

  it('passes a style handbook reference to one-sentence world draft generation', async () => {
    const styleHandbookReference = {
      source_title: '公版海洋小说片段',
      source_rights: 'public_domain' as const,
      handbook: {
        narrative_pacing: { label: '叙事节奏', value: '慢热铺陈', evidence: null },
        language_density: { label: '语言密度', value: '高密度意象', evidence: null },
        dialogue_ratio: { label: '对白比例', value: '对白较少', evidence: null },
        scene_progression: { label: '场景推进', value: '物件带动转场', evidence: null },
        suspense_structure: { label: '悬念结构', value: '延迟解释', evidence: null },
        relationship_tension: { label: '人物关系张力', value: '承诺与亏欠', evidence: null },
        foreshadowing_pattern: { label: '伏笔埋设/回收方式', value: '先给异常', evidence: null },
        do_guidelines: [],
        avoid_guidelines: ['不要复用原文句子。'],
        originality_guidelines: ['用原创角色承载抽象风格参数。'],
      },
      safety_notes: ['风格手册只是写作参考，不会写入 canon。'],
    };
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      source_brief: '一个边境殖民地依赖濒临失控的跃迁灯塔',
      draft: {
        title: '群星边境',
        genre_template: 'sci_fi',
        truth_canon: '跃迁灯塔正在失控。',
        starter_assets: { characters: [{ name: '许砚', role_type: 'protagonist' }] },
      },
      first_chapter_goal: '让许砚第一次听见跃迁灯塔低鸣。',
      generation_notes: [],
      safety_notes: ['确认前不会创建世界。'],
      style_handbook_reference: styleHandbookReference,
    }));
    vi.stubGlobal('fetch', fetchMock);

    await draftWorldFromBrief('一个边境殖民地依赖濒临失控的跃迁灯塔', styleHandbookReference);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/draft-from-brief',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          brief: '一个边境殖民地依赖濒临失控的跃迁灯塔',
          style_handbook_reference: styleHandbookReference,
        }),
      }),
    );
  });

  it('calls world seed library endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ seeds: [{ key: 'forgotten-sun-city', label: '无日城' }] }))
      .mockResolvedValueOnce(jsonResponse({
        key: 'forgotten-sun-city',
        label: '无日城',
        genre_template: 'weird_fantasy',
        hook: '所有人都忘记太阳存在过。',
        tension_profile: ['集体失忆'],
        starter_summary: { character_count: 2 },
        payload: {
          title: '无日城',
          genre_template: 'weird_fantasy',
          truth_canon: '无日城没有太阳。',
          starter_assets: { characters: [{ name: '沈昼', role_type: 'protagonist' }] },
        },
      }))
      .mockResolvedValueOnce(jsonResponse({ id: 9 }));
    vi.stubGlobal('fetch', fetchMock);

    const list = await listWorldSeeds();
    const detail = await getWorldSeed('forgotten-sun-city');
    const created = await createWorldFromSeed('forgotten-sun-city');

    expect(fetchMock).toHaveBeenNthCalledWith(1, 'http://localhost:8000/worlds/seeds', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://localhost:8000/worlds/seeds/forgotten-sun-city', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(3, 'http://localhost:8000/worlds/from-seed/forgotten-sun-city', expect.objectContaining({ method: 'POST', body: '{}' }));
    expect(list.seeds[0].key).toBe('forgotten-sun-city');
    expect(detail.payload.title).toBe('无日城');
    expect(created.id).toBe(9);
  });
});

describe('style handbook API helper', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls preview-only style handbook endpoint without confirming material', async () => {
    const payload = {
      world_id: 7,
      source_type: 'pasted_text',
      source_title: '参考片段',
      source_rights: 'general_reference',
      cleaned_excerpt: '雨夜里出现旧徽记。',
      handbook: {
        narrative_pacing: { label: '叙事节奏', value: '中速推进', evidence: null },
        language_density: { label: '语言密度', value: '中等', evidence: null },
        dialogue_ratio: { label: '对白比例', value: '适中', evidence: null },
        scene_progression: { label: '场景推进', value: '意象推进', evidence: null },
        suspense_structure: { label: '悬念结构', value: '显性悬念', evidence: null },
        relationship_tension: { label: '人物关系张力', value: '关系张力明显', evidence: null },
        foreshadowing_pattern: { label: '伏笔埋设/回收方式', value: '先给异常，再延迟解释', evidence: null },
        do_guidelines: [],
        avoid_guidelines: [],
        originality_guidelines: [],
      },
      safety_notes: ['不会写入 canon。'],
      generation_notes: ['已生成草稿。'],
    };
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse(payload));
    vi.stubGlobal('fetch', fetchMock);

    const result = await previewStyleHandbook(7, {
      source_type: 'pasted_text',
      source_title: '参考片段',
      source_rights: 'general_reference',
      content: '雨夜里出现旧徽记。',
    });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/7/imports/style-handbook/preview',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          source_type: 'pasted_text',
          source_title: '参考片段',
          source_rights: 'general_reference',
          content: '雨夜里出现旧徽记。',
        }),
      }),
    );
    expect(result.handbook.narrative_pacing.label).toBe('叙事节奏');
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

    const response = await searchWorld(7, { q: '灯塔', object_types: ['character', 'event'], tags: ['灯塔线', '3'], limit: 10 });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/7/search?q=%E7%81%AF%E5%A1%94&object_types=character%2Cevent&tags=%E7%81%AF%E5%A1%94%E7%BA%BF%2C3&limit=10',
      expect.any(Object),
    );
    expect(response.object_type_counts).toEqual({ character: 1 });
  });
});

describe('world tag API helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls world tag endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, tags: [] }))
      .mockResolvedValueOnce(jsonResponse({ id: 3, world_id: 7, name: '主线', slug: '主线', color: 'amber', created_at: '2026-05-31T00:00:00Z' }))
      .mockResolvedValueOnce(jsonResponse({ id: 3, world_id: 7, name: '主线压力', slug: '主线压力', color: null, created_at: '2026-05-31T00:00:00Z' }))
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, source_tag_id: 3, target_tag_id: 4, moved_count: 1, already_assigned_count: 1, deleted_source_tag: true }))
      .mockResolvedValueOnce(jsonResponse({ tag: { id: 3, world_id: 7, name: '主线', slug: '主线', color: 'amber', created_at: '2026-05-31T00:00:00Z', assignment_count: 1, object_type_counts: { character: 1 } }, objects: [] }))
      .mockResolvedValueOnce(jsonResponse({ id: 9, world_id: 7, tag_id: 3, object_type: 'character', object_id: 1, created_at: '2026-05-31T00:00:00Z' }))
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, tag_id: 3, object_type: 'character', requested_count: 3, assigned_count: 2, already_assigned_count: 1, assigned_object_ids: [2, 3], already_assigned_object_ids: [1] }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);

    await listWorldTags(7);
    await createWorldTag(7, { name: '主线', color: 'amber' });
    await updateWorldTag(7, 3, { name: '主线压力', color: null });
    await mergeWorldTag(7, 3, { target_tag_id: 4 });
    await getWorldTag(7, 3);
    await assignWorldTag(7, 3, { object_type: 'character', object_id: 1 });
    const bulk = await bulkAssignWorldTag(7, 3, { object_type: 'character', object_ids: [1, 2, 3] });
    await unassignWorldTag(7, 3, 'character', 1);
    await deleteWorldTag(7, 3);

    expect(fetchMock).toHaveBeenNthCalledWith(1, 'http://localhost:8000/worlds/7/tags', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://localhost:8000/worlds/7/tags', expect.objectContaining({ method: 'POST', body: JSON.stringify({ name: '主线', color: 'amber' }) }));
    expect(fetchMock).toHaveBeenNthCalledWith(3, 'http://localhost:8000/worlds/7/tags/3', expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ name: '主线压力', color: null }) }));
    expect(fetchMock).toHaveBeenNthCalledWith(4, 'http://localhost:8000/worlds/7/tags/3/merge', expect.objectContaining({ method: 'POST', body: JSON.stringify({ target_tag_id: 4 }) }));
    expect(fetchMock).toHaveBeenNthCalledWith(5, 'http://localhost:8000/worlds/7/tags/3', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(6, 'http://localhost:8000/worlds/7/tags/3/objects', expect.objectContaining({ method: 'POST', body: JSON.stringify({ object_type: 'character', object_id: 1 }) }));
    expect(fetchMock).toHaveBeenNthCalledWith(7, 'http://localhost:8000/worlds/7/tags/3/objects/bulk', expect.objectContaining({ method: 'POST', body: JSON.stringify({ object_type: 'character', object_ids: [1, 2, 3] }) }));
    expect(fetchMock).toHaveBeenNthCalledWith(8, 'http://localhost:8000/worlds/7/tags/3/objects/character/1', expect.objectContaining({ method: 'DELETE' }));
    expect(fetchMock).toHaveBeenNthCalledWith(9, 'http://localhost:8000/worlds/7/tags/3', expect.objectContaining({ method: 'DELETE' }));
    expect(bulk.assigned_count).toBe(2);
  });
});

describe('world snapshot compare API helper', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls snapshot compare endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      world_id: 7,
      base_snapshot: { id: 12, world_id: 7, world_version: 2, label: null, note: null, created_at: '2026-05-31T00:00:00Z' },
      target_snapshot: { id: 13, world_id: 7, world_version: 3, label: null, note: null, created_at: '2026-05-31T00:00:00Z' },
      summary: { total_changes: 1, object_type_counts: { character: 1 } },
      changes: { world: [], characters: [], relations: [], foreshadows: [], chapters: [], events: [] },
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await compareWorldSnapshots(12, 13);

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/snapshots/12/compare/13', expect.any(Object));
    expect(response.summary.total_changes).toBe(1);
  });
});

describe('open threads API helper', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls open threads endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      world_id: 7,
      world_version: 3,
      summary: {
        total_open_threads: 1,
        must_close_count: 0,
        should_advance_count: 1,
        can_delay_count: 0,
        can_leave_open_count: 0,
        convergence_ratio: 0.25,
        narrative_entropy_level: 'medium',
        recent_event_count: 4,
      },
      threads: [],
      suggested_next_actions: [],
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await getOpenThreads(7);

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/worlds/7/open-threads', expect.any(Object));
    expect(response.summary.narrative_entropy_level).toBe('medium');
  });
});

describe('world pulse API helper', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls world pulse endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      world_id: 7,
      world_version: 3,
      pulse_status: 'watch',
      primary_mode: 'converge',
      headline: '世界近况：建议先处理开放线索。',
      indicators: [],
      focus: [],
      next_actions: [],
      source_summary: { approved_chapter_count: 2 },
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await getWorldPulse(7);

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/worlds/7/pulse', expect.any(Object));
    expect(response.primary_mode).toBe('converge');
  });
});

describe('arc plan API helper', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls arc plan endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      world_id: 7,
      world_version: 3,
      arc_mode: 'converge',
      mode_reason: '开放线索压力过高。',
      expansion_budget: 'locked',
      next_chapter_number: 4,
      recommended_goal: '回收黑匣子脉冲。',
      closure_items: [],
      guidance: [],
      source_summary: { must_close_count: 1 },
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await getArcPlan(7);

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/worlds/7/arc-plan', expect.any(Object));
    expect(response.arc_mode).toBe('converge');
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
