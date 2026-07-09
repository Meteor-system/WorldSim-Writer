import { beforeEach, describe, expect, it, vi } from 'vitest';
import type {
  ApproveRequest,
  ChapterExecutionContext,
  CharacterCreate,
  CharacterRelationCreate,
  CharacterRelationUpdate,
  CharacterUpdate,
  ForeshadowCreate,
  ForeshadowUpdate,
  StyleHandbookReference,
  WorldCreateRequest,
  WorldCreationMaterialReference,
} from './types';
import {
  approveChapter,
  checkApprovalConsistency,
  compareWorldSnapshots,
  createChapter,
  createCharacter,
  createForeshadow,
  createRelation,
  createSampleWorld,
  createWorld,
  createWorldFromSeed,
  createWorldTag,
  draftWorldFromBrief,
  updateWorldStatus,
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
  getSerialPlan,
  getWorldPulse,
  getArcPlan,
  exportWorldArchiveMarkdown,
  getDraftDiff,
  getWorldEvents,
  getDraftVersion,
  confirmWorldImport,
  previewStyleHandbook,
  previewWorldImport,
  getWorldSeed,
  getWorldTag,
  listWorldSeeds,
  listWorldTags,
  searchWorld,
  unassignWorldTag,
  generateOutline,
  getRelations,
  editDraft,
  rejectDraft,
  reviseDraft,
  reviseParagraph,
  stashDraft,
  updateCharacter,
  updateForeshadow,
  updateRelation,
  writeChapter,
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
      raw_text: '草稿原文不应进入正式开书请求。',
      first_chapter_goal: '草稿首章目标不应进入正式开书请求。',
      starter_assets: {
        raw_text: 'starter 原文不应进入正式开书请求。',
        characters: [
          {
            name: '许砚',
            role_type: 'protagonist',
            status: 'active',
            raw_text: '角色原文不应进入正式开书请求。',
          },
        ],
        relations: [
          {
            source_index: 0,
            target_index: 0,
            relation_type: 'self_doubt',
            intensity: 2,
            raw_text: '关系运行时备注不应进入正式开书请求。',
          },
        ],
        foreshadows: [
          {
            title: '黑匣子脉冲',
            description: '废弃黑匣子收到未来求救信号。',
            foreshadow_type: 'signal_clue',
            urgency_level: 4,
            internal_score: 0.88,
          },
        ],
      },
    } as unknown as WorldCreateRequest;
    const expectedPayload: WorldCreateRequest = {
      title: '群星边境',
      genre_template: 'sci_fi',
      truth_canon: '跃迁灯塔正在失控。',
      tone_profile: { style: '冷峻太空歌剧' },
      starter_assets: {
        characters: [{ name: '许砚', role_type: 'protagonist', status: 'active' }],
        relations: [{ source_index: 0, target_index: 0, relation_type: 'self_doubt', intensity: 2 }],
        foreshadows: [
          {
            title: '黑匣子脉冲',
            description: '废弃黑匣子收到未来求救信号。',
            foreshadow_type: 'signal_clue',
            urgency_level: 4,
          },
        ],
      },
    };

    await createWorld(payload);
    await createSampleWorld();

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/worlds',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(expectedPayload) }),
    );
    const requestBody = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    expect(requestBody.raw_text).toBeUndefined();
    expect(requestBody.first_chapter_goal).toBeUndefined();
    expect(requestBody.starter_assets.raw_text).toBeUndefined();
    expect(requestBody.starter_assets.characters[0].raw_text).toBeUndefined();
    expect(requestBody.starter_assets.relations[0].raw_text).toBeUndefined();
    expect(requestBody.starter_assets.foreshadows[0].internal_score).toBeUndefined();
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

  it('passes a variant count to one-sentence world draft generation when requested', async () => {
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
      variants: [],
    }));
    vi.stubGlobal('fetch', fetchMock);

    await draftWorldFromBrief('一个所有人出生时都会被分配死因的王国', null, 3);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/draft-from-brief',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ brief: '一个所有人出生时都会被分配死因的王国', variant_count: 3 }),
      }),
    );
  });

  it('passes import node material references to one-sentence world draft generation', async () => {
    const materialReferences: Array<WorldCreationMaterialReference & { raw_text: string }> = [
      {
        source: 'import_node' as const,
        asset_id: 42,
        title: '雾港钟楼候选素材',
        summary: '一座每天倒敲十三次的钟楼引发城内记忆错位。',
        asset_pool: 'inspiration' as const,
        source_rights: 'general_reference' as const,
        raw_text: '原文不应进入一句话开书请求。',
      },
    ];
    const expectedMaterialReferences = [
      {
        source: 'import_node' as const,
        asset_id: 42,
        title: '雾港钟楼候选素材',
        summary: '一座每天倒敲十三次的钟楼引发城内记忆错位。',
        asset_pool: 'inspiration' as const,
        source_rights: 'general_reference' as const,
      },
    ];
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
      material_references: expectedMaterialReferences,
      variants: [],
    }));
    vi.stubGlobal('fetch', fetchMock);

    const result = await draftWorldFromBrief('一个边境殖民地依赖濒临失控的跃迁灯塔', null, 3, materialReferences);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/draft-from-brief',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          brief: '一个边境殖民地依赖濒临失控的跃迁灯塔',
          variant_count: 3,
          material_references: expectedMaterialReferences,
        }),
      }),
    );
    const requestBody = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(Object.keys(requestBody).sort()).toEqual(['brief', 'material_references', 'variant_count']);
    expect(requestBody).not.toHaveProperty('raw_text');
    expect(requestBody).not.toHaveProperty('internal_score');
    expect(requestBody.material_references[0]).not.toHaveProperty('raw_text');
    expect(result.material_references).toEqual(expectedMaterialReferences);
  });

  it('sends only allowed style handbook reference fields to one-sentence world draft generation', async () => {
    const expectedStyleHandbookReference: StyleHandbookReference = {
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
    const styleHandbookReference = {
      ...expectedStyleHandbookReference,
      raw_text: '原文不应进入一句话开书请求。',
      handbook: {
        ...expectedStyleHandbookReference.handbook,
        narrative_pacing: {
          ...expectedStyleHandbookReference.handbook.narrative_pacing,
          raw_text: '维度原文不应进入请求。',
        },
        internal_score: 0.93,
      },
    } as StyleHandbookReference & { raw_text: string };
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
      style_handbook_reference: expectedStyleHandbookReference,
      variants: [],
    }));
    vi.stubGlobal('fetch', fetchMock);

    await draftWorldFromBrief('一个边境殖民地依赖濒临失控的跃迁灯塔', styleHandbookReference, 3);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/draft-from-brief',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          brief: '一个边境殖民地依赖濒临失控的跃迁灯塔',
          style_handbook_reference: expectedStyleHandbookReference,
          variant_count: 3,
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
        starter_guidance: {
          first_chapter_goal: '让沈昼围绕“空白日晷”展开第一次主动行动。',
          protagonist_relationships: ['沈昼 ↔ 陆鸦：相互猜疑，张力 4/5。'],
          foreshadow_pressure: ['空白日晷：紧迫度 4/5，建议在第3-6章前持续制造压力。'],
          story_health_hints: ['确认前不写入正史。'],
        },
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
    expect(detail.starter_guidance.first_chapter_goal).toContain('空白日晷');
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
          content: '雨夜里出现旧徽记。',
          source_rights: 'general_reference',
        }),
      }),
    );
    expect(result.handbook.narrative_pacing.label).toBe('叙事节奏');
  });

  it('sends only allowed import node fields in preview, style handbook, and confirm requests', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, source_type: 'txt', source_title: '灵感.txt', cleaned_excerpt: '', assets: [], conflicts: [], asset_counts: {} }))
      .mockResolvedValueOnce(jsonResponse({
        world_id: 7,
        source_type: 'pasted_text',
        source_title: '参考片段',
        source_rights: 'general_reference',
        cleaned_excerpt: '',
        handbook: {
          narrative_pacing: { label: '叙事节奏', value: '中速推进', evidence: null },
          language_density: { label: '语言密度', value: '中等', evidence: null },
          dialogue_ratio: { label: '对白比例', value: '适中', evidence: null },
          scene_progression: { label: '场景推进', value: '意象推进', evidence: null },
          suspense_structure: { label: '悬念结构', value: '显性悬念', evidence: null },
          relationship_tension: { label: '人物关系张力', value: '关系张力明显', evidence: null },
          foreshadowing_pattern: { label: '伏笔埋设/回收方式', value: '延迟解释', evidence: null },
          do_guidelines: [],
          avoid_guidelines: [],
          originality_guidelines: [],
        },
        safety_notes: [],
        generation_notes: [],
      }))
      .mockResolvedValueOnce(jsonResponse({ batch: {}, assets: [] }));
    vi.stubGlobal('fetch', fetchMock);

    await previewWorldImport(7, {
      source_type: 'txt',
      source_title: '灵感.txt',
      content: '灵感：雨夜出现第二个月亮。',
      raw_text: '不应进入 import preview 请求。',
    } as unknown as Parameters<typeof previewWorldImport>[1]);
    await previewStyleHandbook(7, {
      source_type: 'pasted_text',
      source_title: '参考片段',
      source_rights: 'general_reference',
      content: '雨夜里出现旧徽记。',
      style_prompt: '不应进入 style handbook 请求。',
    } as unknown as Parameters<typeof previewStyleHandbook>[1]);
    await confirmWorldImport(7, {
      source_type: 'txt',
      source_title: '灵感.txt',
      content: '灵感：雨夜出现第二个月亮。',
      write_to_canon: true,
      assets: [
        {
          asset_pool: 'inspiration',
          title: '第二个月亮',
          summary: '城门口出现第二个月亮。',
          raw_text: '城门口出现第二个月亮。',
          metadata: { source_line: 1 },
          canonical_status: 'approved',
        },
      ],
      conflicts: [
        {
          severity: 'warning',
          category: 'manual',
          message: '人工冲突',
          matched_text: null,
          details: {},
          resolution: 'auto_apply',
        },
      ],
    } as unknown as Parameters<typeof confirmWorldImport>[1]);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/worlds/7/imports/preview',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          source_type: 'txt',
          source_title: '灵感.txt',
          content: '灵感：雨夜出现第二个月亮。',
        }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/worlds/7/imports/style-handbook/preview',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          source_type: 'pasted_text',
          source_title: '参考片段',
          content: '雨夜里出现旧徽记。',
          source_rights: 'general_reference',
        }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      'http://localhost:8000/worlds/7/imports/confirm',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          source_type: 'txt',
          source_title: '灵感.txt',
          content: '灵感：雨夜出现第二个月亮。',
          assets: [
            {
              asset_pool: 'inspiration',
              title: '第二个月亮',
              summary: '城门口出现第二个月亮。',
              raw_text: '城门口出现第二个月亮。',
              metadata: { source_line: 1 },
            },
          ],
          conflicts: [
            {
              severity: 'warning',
              category: 'manual',
              message: '人工冲突',
              matched_text: null,
              details: {},
            },
          ],
        }),
      }),
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

  it('sends only allowed fields for world status and tag mutations', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 7, status: 'archived' }))
      .mockResolvedValueOnce(jsonResponse({ id: 3, world_id: 7, name: '主线', slug: '主线', color: 'amber', created_at: '2026-05-31T00:00:00Z' }))
      .mockResolvedValueOnce(jsonResponse({ id: 3, world_id: 7, name: '主线压力', slug: '主线压力', color: null, created_at: '2026-05-31T00:00:00Z' }))
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, source_tag_id: 3, target_tag_id: 4, moved_count: 0, already_assigned_count: 0, deleted_source_tag: true }))
      .mockResolvedValueOnce(jsonResponse({ id: 9, world_id: 7, tag_id: 3, object_type: 'character', object_id: 1, created_at: '2026-05-31T00:00:00Z' }))
      .mockResolvedValueOnce(jsonResponse({ world_id: 7, tag_id: 3, object_type: 'character', requested_count: 1, assigned_count: 1, already_assigned_count: 0, assigned_object_ids: [1], already_assigned_object_ids: [] }));
    vi.stubGlobal('fetch', fetchMock);

    await updateWorldStatus(7, { status: 'archived', raw_text: '运行时备注' } as unknown as Parameters<typeof updateWorldStatus>[1]);
    await createWorldTag(7, { name: '主线', color: 'amber', raw_text: '运行时备注' } as unknown as Parameters<typeof createWorldTag>[1]);
    await updateWorldTag(7, 3, { name: '主线压力', color: null, raw_text: '运行时备注' } as unknown as Parameters<typeof updateWorldTag>[2]);
    await mergeWorldTag(7, 3, { target_tag_id: 4, raw_text: '运行时备注' } as unknown as Parameters<typeof mergeWorldTag>[2]);
    await assignWorldTag(7, 3, { object_type: 'character', object_id: 1, raw_text: '运行时备注' } as unknown as Parameters<typeof assignWorldTag>[2]);
    await bulkAssignWorldTag(7, 3, { object_type: 'character', object_ids: [1], raw_text: '运行时备注' } as unknown as Parameters<typeof bulkAssignWorldTag>[2]);

    const bodies = fetchMock.mock.calls.map((call) => JSON.parse(call[1]?.body as string));
    expect(bodies).toEqual([
      { status: 'archived' },
      { name: '主线', color: 'amber' },
      { name: '主线压力', color: null },
      { target_tag_id: 4 },
      { object_type: 'character', object_id: 1 },
      { object_type: 'character', object_ids: [1] },
    ]);
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

describe('serial plan API helper', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls serial plan preview endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      world_id: 7,
      world_version: 3,
      approved_chapter_count: 1,
      queue: [
        {
          chapter_number: 2,
          title: '第2章 暗潮',
          goal: '第2章 暗潮：推进灵脉危机。',
          summary: '推进灵脉危机。',
          core_conflict: '必须抉择。',
          pov_suggestion: '林砚',
          foreshadow_hints: ['裂纹玉佩'],
          source: 'story_arc',
        },
      ],
      safety_notes: ['不会自动写正文、不会写入正史或推进世界进度。'],
      review_guardrails: ['每章仍需 Studio 审稿确认。'],
      convergence_guidance: {
        mode: 'balanced',
        mode_label: '平衡推进',
        open_foreshadow_count: 1,
        high_pressure_count: 0,
        stale_count: 0,
        overdue_count: 0,
        priority_foreshadows: [],
        recommendation: '避免只铺设新线索。',
        guidance_notes: [],
      },
    }));
    vi.stubGlobal('fetch', fetchMock);

    const result = await getSerialPlan(7, 2);

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/worlds/7/serial-plan?limit=2', expect.any(Object));
    expect(result.queue[0].chapter_number).toBe(2);
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

describe('character API helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('sends only allowed fields in create and update payloads', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({
        id: 3,
        name: '林七',
        role_type: 'supporting',
        status: 'active',
        public_profile: { visible: true },
        hidden_traits: { secret: '守门' },
        destiny_flag: '守门人',
        current_goals: ['保护青岚城'],
      }))
      .mockResolvedValueOnce(jsonResponse({
        id: 3,
        name: '林七改',
        role_type: 'lead',
        status: 'active',
        public_profile: { visible: false },
        hidden_traits: { secret: '追查旧案' },
        destiny_flag: '追查者',
        current_goals: ['追查旧案'],
      }));
    vi.stubGlobal('fetch', fetchMock);

    await createCharacter(7, {
      name: '林七',
      role_type: 'supporting',
      status: 'active',
      public_profile: { visible: true },
      hidden_traits: { secret: '守门' },
      destiny_flag: '守门人',
      current_goals: ['保护青岚城'],
      edit_reason: '新增角色备注',
      raw_text: '运行时原文不应进入角色创建请求。',
    } as unknown as CharacterCreate);
    await updateCharacter(3, {
      name: '林七改',
      role_type: 'lead',
      status: 'active',
      public_profile: { visible: false },
      hidden_traits: { secret: '追查旧案' },
      destiny_flag: '追查者',
      current_goals: ['追查旧案'],
      edit_reason: '更新角色备注',
      raw_text: '运行时原文不应进入角色更新请求。',
    } as unknown as CharacterUpdate);

    const createBody = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    const updateBody = JSON.parse(fetchMock.mock.calls[1][1]?.body as string);
    expect(createBody).toEqual({
      name: '林七',
      role_type: 'supporting',
      status: 'active',
      public_profile: { visible: true },
      hidden_traits: { secret: '守门' },
      destiny_flag: '守门人',
      current_goals: ['保护青岚城'],
      edit_reason: '新增角色备注',
    });
    expect(updateBody).toEqual({
      name: '林七改',
      role_type: 'lead',
      status: 'active',
      public_profile: { visible: false },
      hidden_traits: { secret: '追查旧案' },
      destiny_flag: '追查者',
      current_goals: ['追查旧案'],
      edit_reason: '更新角色备注',
    });
    expect(createBody.raw_text).toBeUndefined();
    expect(updateBody.raw_text).toBeUndefined();
  });
});

describe('foreshadow API helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('sends only allowed fields in create and update payloads', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({
        id: 4,
        source_chapter_id: 2,
        title: '铜铃异响',
        description: '夜半铜铃无人自鸣。',
        foreshadow_type: 'plot',
        status: 'planted',
        urgency_level: 4,
        related_character_ids: [3],
        expected_resolution_window: '第三幕',
      }))
      .mockResolvedValueOnce(jsonResponse({
        id: 4,
        source_chapter_id: 2,
        title: '铜铃异响改',
        description: '夜半铜铃在城门倒响。',
        foreshadow_type: 'plot',
        status: 'advanced',
        urgency_level: 5,
        related_character_ids: [],
        expected_resolution_window: '第二幕末',
      }));
    vi.stubGlobal('fetch', fetchMock);

    await createForeshadow(7, {
      source_chapter_id: 2,
      title: '铜铃异响',
      description: '夜半铜铃无人自鸣。',
      foreshadow_type: 'plot',
      status: 'planted',
      urgency_level: 4,
      related_character_ids: [3],
      expected_resolution_window: '第三幕',
      edit_reason: '新增伏笔备注',
      raw_text: '运行时原文不应进入伏笔创建请求。',
    } as unknown as ForeshadowCreate);
    await updateForeshadow(4, {
      source_chapter_id: 2,
      title: '铜铃异响改',
      description: '夜半铜铃在城门倒响。',
      foreshadow_type: 'plot',
      status: 'advanced',
      urgency_level: 5,
      related_character_ids: [],
      expected_resolution_window: '第二幕末',
      edit_reason: '推进伏笔备注',
      raw_text: '运行时原文不应进入伏笔更新请求。',
    } as unknown as ForeshadowUpdate);

    const createBody = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    const updateBody = JSON.parse(fetchMock.mock.calls[1][1]?.body as string);
    expect(createBody).toEqual({
      source_chapter_id: 2,
      title: '铜铃异响',
      description: '夜半铜铃无人自鸣。',
      foreshadow_type: 'plot',
      status: 'planted',
      urgency_level: 4,
      related_character_ids: [3],
      expected_resolution_window: '第三幕',
      edit_reason: '新增伏笔备注',
    });
    expect(updateBody).toEqual({
      source_chapter_id: 2,
      title: '铜铃异响改',
      description: '夜半铜铃在城门倒响。',
      foreshadow_type: 'plot',
      status: 'advanced',
      urgency_level: 5,
      related_character_ids: [],
      expected_resolution_window: '第二幕末',
      edit_reason: '推进伏笔备注',
    });
    expect(createBody.raw_text).toBeUndefined();
    expect(updateBody.raw_text).toBeUndefined();
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

  it('sends only allowed fields in relation create and update payloads', async () => {
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
      raw_text: '运行时原文不应进入关系创建请求。',
    } as unknown as CharacterRelationCreate);
    await updateRelation(9, {
      source_character_id: 1,
      target_character_id: 2,
      relation_type: 'rival',
      intensity: 5,
      visibility: 'public',
      edit_reason: '关系转折备注',
      raw_text: '运行时原文不应进入关系更新请求。',
    } as unknown as CharacterRelationUpdate);

    const createBody = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    const updateBody = JSON.parse(fetchMock.mock.calls[1][1]?.body as string);
    expect(createBody).toEqual({
      source_character_id: 1,
      target_character_id: 2,
      relation_type: 'ally',
      intensity: 4,
      visibility: 'private',
      edit_reason: '新增关系备注',
    });
    expect(updateBody).toEqual({
      source_character_id: 1,
      target_character_id: 2,
      relation_type: 'rival',
      intensity: 5,
      visibility: 'public',
      edit_reason: '关系转折备注',
    });
    expect(createBody.raw_text).toBeUndefined();
    expect(updateBody.raw_text).toBeUndefined();
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

  it('sends only allowed material reference fields in chapter execution context', async () => {
    const expectedMaterialReferences: ChapterExecutionContext['material_references'] = [
      {
        asset_id: 42,
        batch_id: 7,
        asset_pool: 'inspiration',
        title: '雾港钟楼候选素材',
        summary: '钟楼倒敲十三次后，城内记忆出现错位。',
        source_title: '导入片段',
        source_type: 'pasted_text',
        created_at: '2026-05-30T00:00:00Z',
        safety_note: '导入素材参考只用于创作提示，不会自动改写正式 canon。',
      },
    ];
    const executionContext: ChapterExecutionContext = {
      source: 'manual',
      source_world_version: 1,
      next_chapter_number: 1,
      goal: '让许砚第一次听见跃迁灯塔低鸣。',
      recommended_pov: { character_id: null, name: '许砚' },
      source_signals: ['首章目标'],
      priority_characters: [],
      priority_foreshadows: [],
      progression_hints: [],
      continuity_warnings: [],
      recent_events: [],
      material_references: [
        {
          ...expectedMaterialReferences[0],
          raw_text: '原文不应进入章节上下文请求。',
          internal_score: 0.9,
        },
      ] as unknown as ChapterExecutionContext['material_references'],
      style_handbook_reference: null,
    };
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({ id: 11, execution_context: null }));
    vi.stubGlobal('fetch', fetchMock);

    await createChapter(7, { chapter_goal: '生成第一章草稿', execution_context: executionContext });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/7/chapters',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          chapter_goal: '生成第一章草稿',
          execution_context: {
            ...executionContext,
            material_references: expectedMaterialReferences,
          },
        }),
      }),
    );
  });

  it('sends only allowed style handbook reference fields in chapter execution context', async () => {
    const expectedStyleHandbookReference: StyleHandbookReference = {
      source_title: '公版海洋小说片段',
      source_rights: 'public_domain',
      handbook: {
        narrative_pacing: { label: '叙事节奏', value: '慢热铺陈', evidence: null },
        language_density: { label: '语言密度', value: '高密度意象', evidence: null },
        dialogue_ratio: { label: '对白比例', value: '对白较少', evidence: null },
        scene_progression: { label: '场景推进', value: '物件带动转场', evidence: null },
        suspense_structure: { label: '悬念结构', value: '延迟解释', evidence: null },
        relationship_tension: { label: '人物关系张力', value: '承诺与亏欠', evidence: null },
        foreshadowing_pattern: { label: '伏笔埋设/回收方式', value: '先给异常', evidence: null },
        do_guidelines: ['保留海潮般的递进感。'],
        avoid_guidelines: ['不要复用原文句子。'],
        originality_guidelines: ['用原创角色承载抽象风格参数。'],
      },
      safety_notes: ['风格手册只是写作参考，不会写入 canon。'],
    };
    const executionContext: ChapterExecutionContext = {
      source: 'manual',
      source_world_version: 1,
      next_chapter_number: 1,
      goal: '让许砚第一次听见跃迁灯塔低鸣。',
      recommended_pov: { character_id: null, name: '许砚' },
      source_signals: ['首章目标'],
      priority_characters: [],
      priority_foreshadows: [],
      progression_hints: [],
      continuity_warnings: [],
      recent_events: [],
      material_references: [],
      style_handbook_reference: {
        ...expectedStyleHandbookReference,
        raw_text: '原文不应进入章节上下文请求。',
        handbook: {
          ...expectedStyleHandbookReference.handbook,
          narrative_pacing: {
            ...expectedStyleHandbookReference.handbook.narrative_pacing,
            raw_text: '维度原文不应进入章节上下文请求。',
          },
          internal_score: 0.93,
        },
      } as StyleHandbookReference,
    };
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({ id: 11, execution_context: null }));
    vi.stubGlobal('fetch', fetchMock);

    await createChapter(7, { chapter_goal: '生成第一章草稿', execution_context: executionContext });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/7/chapters',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          chapter_goal: '生成第一章草稿',
          execution_context: {
            ...executionContext,
            style_handbook_reference: expectedStyleHandbookReference,
          },
        }),
      }),
    );
  });

  it('sends only allowed execution context root and nested fields in chapter creation requests', async () => {
    const expectedMaterialReferences: ChapterExecutionContext['material_references'] = [
      {
        asset_id: 42,
        batch_id: 7,
        asset_pool: 'inspiration',
        title: '雾港钟楼候选素材',
        summary: '钟楼倒敲十三次后，城内记忆出现错位。',
        source_title: '导入片段',
        source_type: 'pasted_text',
        created_at: '2026-05-30T00:00:00Z',
        safety_note: '导入素材参考只用于创作提示，不会自动改写正式 canon。',
      },
    ];
    const executionContext = {
      source: 'next_chapter_prep',
      source_world_version: 3,
      next_chapter_number: 4,
      goal: '让许砚第一次听见跃迁灯塔低鸣。',
      recommended_pov: { character_id: 9, name: '许砚', raw_text: 'POV 原文不应发送。' },
      source_signals: ['首章目标'],
      priority_characters: [
        {
          character_id: 9,
          name: '许砚',
          role_type: 'protagonist',
          status: '接近灯塔',
          reason: '主线推进。',
          internal_score: 0.94,
        },
      ],
      priority_foreshadows: [
        {
          foreshadow_id: 5,
          title: '灯塔低鸣',
          status: 'advanced',
          urgency_level: 4,
          reason: '需要推进。',
          raw_text: '伏笔原文不应发送。',
        },
      ],
      progression_hints: [
        {
          hint_type: 'foreshadow',
          priority: 'high',
          title: '推进灯塔低鸣',
          rationale: '上一章已经铺垫。',
          suggested_next_beat: '许砚靠近灯塔。',
          related_character_ids: [9],
          related_foreshadow_ids: [5],
          can_seed_next_chapter_goal: true,
          internal_score: 0.88,
        },
      ],
      continuity_warnings: [
        {
          severity: 'medium',
          category: 'foreshadow',
          message: '不能提前解释灯塔真相。',
          related_character_ids: [9],
          related_foreshadow_ids: [5],
          raw_text: '警告原文不应发送。',
        },
      ],
      recent_events: [
        {
          id: 12,
          event_type: 'chapter_approved',
          world_version_before: 2,
          world_version_after: 3,
          payload: { raw_text: '事件 payload 不应发送。' },
          created_at: '2026-05-30T00:00:00Z',
        },
      ],
      material_references: [
        {
          ...expectedMaterialReferences[0],
          raw_text: '素材原文不应发送。',
          internal_score: 0.9,
        },
      ],
      style_handbook_reference: null,
      raw_text: '根对象原文不应发送。',
      internal_score: 0.99,
    } as unknown as ChapterExecutionContext;
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({ id: 11, execution_context: null }));
    vi.stubGlobal('fetch', fetchMock);

    await createChapter(7, {
      chapter_goal: '生成第一章草稿',
      title: '第一章 灯塔低鸣',
      execution_context: executionContext,
      raw_text: '根请求原文不应发送。',
      internal_score: 0.9,
      first_chapter_goal: '运行时首章目标不应发送。',
    } as unknown as Parameters<typeof createChapter>[1]);

    const requestBody = JSON.parse(fetchMock.mock.calls[0][1].body as string) as {
      raw_text?: string;
      internal_score?: number;
      first_chapter_goal?: string;
      execution_context: ChapterExecutionContext;
    };
    expect(requestBody).toEqual({
      chapter_goal: '生成第一章草稿',
      title: '第一章 灯塔低鸣',
      execution_context: {
        source: 'next_chapter_prep',
        source_world_version: 3,
        next_chapter_number: 4,
        goal: '让许砚第一次听见跃迁灯塔低鸣。',
        recommended_pov: { character_id: 9, name: '许砚' },
        source_signals: ['首章目标'],
        priority_characters: [
          {
            character_id: 9,
            name: '许砚',
            role_type: 'protagonist',
            status: '接近灯塔',
            reason: '主线推进。',
          },
        ],
        priority_foreshadows: [
          {
            foreshadow_id: 5,
            title: '灯塔低鸣',
            status: 'advanced',
            urgency_level: 4,
            reason: '需要推进。',
          },
        ],
        progression_hints: [
          {
            hint_type: 'foreshadow',
            priority: 'high',
            title: '推进灯塔低鸣',
            rationale: '上一章已经铺垫。',
            suggested_next_beat: '许砚靠近灯塔。',
            related_character_ids: [9],
            related_foreshadow_ids: [5],
            can_seed_next_chapter_goal: true,
          },
        ],
        continuity_warnings: [
          {
            severity: 'medium',
            category: 'foreshadow',
            message: '不能提前解释灯塔真相。',
            related_character_ids: [9],
            related_foreshadow_ids: [5],
          },
        ],
        recent_events: [
          {
            id: 12,
            event_type: 'chapter_approved',
            world_version_before: 2,
            world_version_after: 3,
            created_at: '2026-05-30T00:00:00Z',
          },
        ],
        material_references: expectedMaterialReferences,
        style_handbook_reference: null,
      },
    });
    expect(requestBody.raw_text).toBeUndefined();
    expect(requestBody.internal_score).toBeUndefined();
    expect(requestBody.first_chapter_goal).toBeUndefined();
  });

  it('sends only allowed root fields in outline and write requests', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ chapter_id: 11, outline_beats: [], outline_context: {}, status: 'outlined' }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 1 }));
    vi.stubGlobal('fetch', fetchMock);
    const outlineBeats = [
      {
        beat_id: 'beat-1',
        summary: '林砚抵达灵井。',
        pov_character: '林砚',
        location: '灵井',
        emotional_arc: '疑惑到警觉',
        key_dialogue_hints: ['湿信是谁留下的？'],
      },
    ];

    await generateOutline(11, {
      chapter_context: '强调灵井裂纹与湿信。',
      raw_text: '提纲请求不应发送原文。',
      internal_score: 0.91,
    } as unknown as Parameters<typeof generateOutline>[1]);
    await writeChapter(11, {
      outline_beats: outlineBeats,
      raw_text: '按提纲写作请求不应发送原文。',
      internal_score: 0.92,
      first_chapter_goal: '运行时首章目标不应发送。',
    } as unknown as Parameters<typeof writeChapter>[1]);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/chapters/11/outline',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ chapter_context: '强调灵井裂纹与湿信。' }) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/chapters/11/write',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ outline_beats: outlineBeats }) }),
    );
    const outlineBody = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    const writeBody = JSON.parse(fetchMock.mock.calls[1][1]?.body as string);
    expect(outlineBody.raw_text).toBeUndefined();
    expect(outlineBody.internal_score).toBeUndefined();
    expect(writeBody.raw_text).toBeUndefined();
    expect(writeBody.internal_score).toBeUndefined();
    expect(writeBody.first_chapter_goal).toBeUndefined();
  });

  it('cleans studio draft operation request bodies', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ status: 'rejected' }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 2 }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 3 }));
    vi.stubGlobal('fetch', fetchMock);

    await rejectDraft(11, {
      feedback: '需要补足动机',
      raw_text: '驳回请求不应发送草稿原文',
      internal_score: 0.87,
    } as unknown as Parameters<typeof rejectDraft>[1]);
    await editDraft(11, {
      content: '林砚在灵井旁听见了第二个人的脚步声。',
      change_summary: '补足动机',
      raw_text: '编辑请求不应发送草稿原文',
      internal_score: 0.9,
    } as unknown as Parameters<typeof editDraft>[1]);
    await stashDraft(11, {
      note: '暂存当前草稿',
      raw_text: '暂存请求不应发送草稿原文',
      internal_score: 0.91,
    } as unknown as Parameters<typeof stashDraft>[1]);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/chapters/11/reject',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ feedback: '需要补足动机' }) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/chapters/11/draft',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ content: '林砚在灵井旁听见了第二个人的脚步声。', change_summary: '补足动机' }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      'http://localhost:8000/chapters/11/draft/stash',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ note: '暂存当前草稿' }) }),
    );
    for (const call of fetchMock.mock.calls) {
      const body = JSON.parse(call[1]?.body as string);
      expect(body.raw_text).toBeUndefined();
      expect(body.internal_score).toBeUndefined();
    }
  });

  it('calls draft stash, paragraph revision, full revision, exact version, diff, approval preview, approval consistency, and approve endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ draft_version: 2 }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 3 }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 4 }))
      .mockResolvedValueOnce(jsonResponse({ draft_version: 1 }))
      .mockResolvedValueOnce(jsonResponse({ diff_lines: [] }))
      .mockResolvedValueOnce(jsonResponse({ version_conflict: false }))
      .mockResolvedValueOnce(jsonResponse({ consistency_warnings: [] }))
      .mockResolvedValueOnce(jsonResponse({ status: 'approved' }));
    vi.stubGlobal('fetch', fetchMock);
    const approvalPayload = {
      draft_version: 1,
      selected_character_change_indexes: [0],
      selected_foreshadow_change_indexes: [],
      raw_text: '审核请求不应发送草稿原文',
      internal_score: 0.93,
    } as unknown as ApproveRequest;
    const expectedApprovalPayload: ApproveRequest = {
      draft_version: 1,
      selected_character_change_indexes: [0],
      selected_foreshadow_change_indexes: [],
    };

    await stashDraft(11, { note: '暂存当前草稿' });
    await reviseParagraph(11, {
      paragraph_index: 1,
      mode: 'rewrite',
      instruction: '增强悬念',
      raw_text: '段落修订请求不应发送草稿原文',
      internal_score: 0.88,
    } as unknown as Parameters<typeof reviseParagraph>[1]);
    await reviseDraft(11, {
      instruction: '补足试探过程',
      raw_text: '整章修订请求不应发送草稿原文',
      internal_score: 0.93,
    } as unknown as Parameters<typeof reviseDraft>[1]);
    await getDraftVersion(11, 1);
    await getDraftDiff(11, 1, 3);
    await getApprovalPreview(11);
    await checkApprovalConsistency(11, approvalPayload);
    await approveChapter(11, approvalPayload);

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
        body: JSON.stringify(expectedApprovalPayload),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      8,
      'http://localhost:8000/chapters/11/approve',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(expectedApprovalPayload),
      }),
    );
    const consistencyBody = JSON.parse(fetchMock.mock.calls[6][1]?.body as string);
    const approveBody = JSON.parse(fetchMock.mock.calls[7][1]?.body as string);
    expect(consistencyBody.raw_text).toBeUndefined();
    expect(consistencyBody.internal_score).toBeUndefined();
    expect(approveBody.raw_text).toBeUndefined();
    expect(approveBody.internal_score).toBeUndefined();
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
