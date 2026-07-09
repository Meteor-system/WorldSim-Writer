import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { StyleHandbookReference, WorldCreateRequest, WorldSeedSummary } from '../api/types';
import { WorldCreationForm } from './WorldCreationForm';

afterEach(() => cleanup());

const seedSummary: WorldSeedSummary = {
  key: 'forgotten-sun-city',
  label: '无日城',
  genre_template: 'weird_fantasy',
  hook: '所有人都忘记太阳存在过。',
  tension_profile: ['集体失忆'],
  starter_summary: { character_count: 1, relation_count: 0, foreshadow_count: 1, character_names: ['沈昼'], foreshadow_titles: ['空白日晷'] },
  starter_guidance: {
    first_chapter_goal: '让沈昼围绕“空白日晷”展开第一次主动行动。',
    protagonist_relationships: ['沈昼 ↔ 陆鸦：相互猜疑，张力 4/5。'],
    foreshadow_pressure: ['空白日晷：紧迫度 4/5，建议在第3-6章前持续制造压力。'],
    story_health_hints: ['首章优先让世界规则通过沈昼的选择显影。', '这些提示只是创建前参考；确认前不写入正史。'],
  },
};

const draftPayload: WorldCreateRequest = {
  title: '死因王国',
  genre_template: 'fantasy',
  truth_canon: '每个人出生时都会获得一个未来死因，死因记录支撑王国秩序。',
  tone_profile: { style: '黑暗奇幻悬疑', pacing: '高张力冷启动' },
  starter_assets: {
    characters: [
      { name: '伊莱', role_type: 'protagonist', public_profile: { identity: '命运抄写员' }, current_goals: ['查明死因被篡改的原因'] },
      { name: '维拉', role_type: 'rival', public_profile: { identity: '王国命运官' }, current_goals: ['封锁死因档案'] },
    ],
    relations: [{ source_index: 0, target_index: 1, relation_type: 'mutual_suspicion', intensity: 4, visibility: 'private' }],
    foreshadows: [{ title: '空白死因页', description: '伊莱的死因记录被银火烧穿。', foreshadow_type: 'fate_record_clue', status: 'planted', urgency_level: 4, related_character_indexes: [0, 1] }],
  },
};

const seedPayload: WorldCreateRequest = {
  title: '无日城',
  genre_template: 'weird_fantasy',
  truth_canon: '无日城没有太阳。',
  tone_profile: { style: '诡秘奇幻' },
  starter_assets: {
    characters: [{ name: '沈昼', role_type: 'protagonist', current_goals: ['查明钟声'] }],
    relations: [],
    foreshadows: [{ title: '空白日晷', description: '旧广场上的空白日晷。', foreshadow_type: 'world_rule_clue', status: 'planted', urgency_level: 4, related_character_indexes: [0] }],
  },
};

describe('WorldCreationForm', () => {
  it('submits a custom world payload with starter assets', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onCreateSample = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={onCreateSample} />);

    expect(screen.getByLabelText('Fantasy 初始故事提示')).toHaveTextContent('首章目标');
    expect(screen.getByLabelText('Fantasy 初始故事提示')).toHaveTextContent('伏笔压力');

    await user.clear(screen.getByLabelText('世界标题'));
    await user.type(screen.getByLabelText('世界标题'), '自定义群星边境');
    await user.click(screen.getByRole('button', { name: '添加关系' }));
    await user.click(screen.getByRole('button', { name: '添加伏笔' }));
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    expect(onCreate).toHaveBeenCalledOnce();
    expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({
      title: '自定义群星边境',
      starter_assets: expect.objectContaining({
        characters: expect.arrayContaining([expect.objectContaining({ name: expect.any(String), role_type: expect.any(String) })]),
        relations: expect.arrayContaining([expect.objectContaining({ source_index: 0, target_index: 1 })]),
        foreshadows: expect.arrayContaining([expect.objectContaining({ status: 'planted', urgency_level: expect.any(Number) })]),
      }),
    }), { firstChapterGoal: undefined });
  });

  it('calls the sample world shortcut without submitting the custom form', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onCreateSample = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={onCreateSample} />);

    await user.click(screen.getByRole('button', { name: '创建内置示例世界' }));

    expect(onCreateSample).toHaveBeenCalledOnce();
    expect(onCreate).not.toHaveBeenCalled();
  });

  it('generates an editable world draft from a brief without creating the world', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onDraftFromBrief = vi.fn().mockResolvedValue({
      source_brief: '一个所有人出生时都会被分配死因的王国',
      draft: draftPayload,
      first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      generation_notes: ['已生成可编辑草稿。'],
      safety_notes: ['确认前不会创建世界、写入正史或推进世界进度。'],
      followup_questions: ['主角要先挑战死因制度，还是先救一个被错误判死的人？'],
    });
    render(
      <WorldCreationForm
        creating={false}
        onCreate={onCreate}
        onCreateSample={vi.fn()}
        onDraftFromBrief={onDraftFromBrief}
      />,
    );

    await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配死因的王国');
    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));

    expect(onDraftFromBrief).toHaveBeenCalledWith('一个所有人出生时都会被分配死因的王国', null, 3);
    expect(onCreate).not.toHaveBeenCalled();
    expect(await screen.findByText('世界创建草稿已填入下方表单')).toBeInTheDocument();
    expect(screen.getByText('确认前不会创建世界、写入正史或推进世界进度。')).toBeInTheDocument();
    expect(screen.getByLabelText('一句话草稿追问问题')).toHaveTextContent('主角要先挑战死因制度，还是先救一个被错误判死的人？');
    expect(screen.getByText('这些问题只辅助你修改脑洞或表单；不会自动创建世界、写入正史或生成章节。')).toBeInTheDocument();
    expect(screen.getByLabelText('世界标题')).toHaveValue('死因王国');

    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));
    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ title: '死因王国', genre_template: 'fantasy' }),
      { firstChapterGoal: '让伊莱发现自己的死因记录被烧穿。' },
    );
  });

  it('shows draft variants and switches the editable form without creating the world', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const relationDraft: WorldCreateRequest = {
      ...draftPayload,
      title: '命运同盟王国',
      truth_canon: '死因记录迫使两个敌对家族结盟。',
      starter_assets: {
        ...draftPayload.starter_assets,
        characters: draftPayload.starter_assets.characters.map((character) => ({ ...character })),
        relations: draftPayload.starter_assets.relations?.map((relation) => ({ ...relation })),
        foreshadows: draftPayload.starter_assets.foreshadows?.map((foreshadow) => ({ ...foreshadow })),
      },
    };
    const onDraftFromBrief = vi.fn().mockResolvedValue({
      source_brief: '一个所有人出生时都会被分配死因的王国',
      draft: draftPayload,
      first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      generation_notes: ['已生成可编辑草稿。'],
      safety_notes: ['确认前不会创建世界、写入正史或推进世界进度。'],
      variants: [
        {
          variant_id: 'variant-1',
          label: '主线高张力版',
          draft: draftPayload,
          first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
          generation_notes: ['高张力开局。'],
          safety_notes: ['确认创建前不会写入正史。'],
          followup_questions: ['开场要从公开审判进入，还是从档案室潜入进入？'],
        },
        {
          variant_id: 'variant-2',
          label: '角色关系驱动版',
          draft: relationDraft,
          first_chapter_goal: '让伊莱和维拉在死因档案前被迫结盟。',
          generation_notes: ['强调角色互相试探。'],
          safety_notes: ['确认创建前不会写入正史。'],
          followup_questions: ['两人结盟是源于共同敌人，还是彼此掌握对方把柄？'],
        },
      ],
    });
    render(
      <WorldCreationForm
        creating={false}
        onCreate={onCreate}
        onCreateSample={vi.fn()}
        onDraftFromBrief={onDraftFromBrief}
      />,
    );

    await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配死因的王国');
    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));

    expect(onDraftFromBrief).toHaveBeenCalledWith('一个所有人出生时都会被分配死因的王国', null, 3);
    const variants = await screen.findByLabelText('世界草稿候选方向');
    expect(within(variants).getByRole('button', { name: /主线高张力版/ })).toHaveTextContent('让伊莱发现自己的死因记录被烧穿。');
    expect(within(variants).getByRole('button', { name: /角色关系驱动版/ })).toHaveTextContent('确认创建前不会写入正史');
    expect(screen.getByLabelText('世界标题')).toHaveValue('死因王国');
    expect(screen.getAllByText('第一章目标：让伊莱发现自己的死因记录被烧穿。').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByLabelText('一句话草稿追问问题')).toHaveTextContent('开场要从公开审判进入，还是从档案室潜入进入？');

    await user.click(within(variants).getByRole('button', { name: /角色关系驱动版/ }));

    expect(screen.getByLabelText('世界标题')).toHaveValue('命运同盟王国');
    expect(screen.getByLabelText('一句话草稿追问问题')).toHaveTextContent('两人结盟是源于共同敌人，还是彼此掌握对方把柄？');
    expect(screen.getAllByText('第一章目标：让伊莱和维拉在死因档案前被迫结盟。').length).toBeGreaterThanOrEqual(1);
    expect(onCreate).not.toHaveBeenCalled();
  });

  it('passes the active style handbook when generating a world draft from a brief', async () => {
    const user = userEvent.setup();
    const styleHandbookReference: StyleHandbookReference = {
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
        do_guidelines: [],
        avoid_guidelines: ['不要复用原文句子。'],
        originality_guidelines: ['用原创角色承载抽象风格参数。'],
      },
      safety_notes: ['风格手册只是写作参考，不会写入 canon。'],
    };
    const onDraftFromBrief = vi.fn().mockResolvedValue({
      source_brief: '一个边境殖民地依赖濒临失控的跃迁灯塔',
      draft: draftPayload,
      first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      generation_notes: [],
      safety_notes: ['确认前不会创建世界、写入正史或推进世界进度。'],
      style_handbook_reference: styleHandbookReference,
    });
    render(
      <WorldCreationForm
        creating={false}
        onCreate={vi.fn()}
        onCreateSample={vi.fn()}
        onDraftFromBrief={onDraftFromBrief}
        activeStyleHandbook={styleHandbookReference}
      />,
    );

    expect(screen.getByTestId('brief-style-handbook')).toHaveTextContent('公版海洋小说片段');
    expect(screen.getByTestId('brief-style-handbook')).toHaveTextContent('不会写入正史');
    await user.type(screen.getByLabelText('一句话故事想法'), '一个边境殖民地依赖濒临失控的跃迁灯塔');
    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));

    expect(onDraftFromBrief).toHaveBeenCalledWith('一个边境殖民地依赖濒临失控的跃迁灯塔', styleHandbookReference, 3);
  });

  it('applies seed payloads to the editable form', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(
      <WorldCreationForm
        creating={false}
        onCreate={onCreate}
        onCreateSample={vi.fn()}
        seeds={[seedSummary]}
        selectedSeedKey={null}
        onLoadSeed={vi.fn().mockResolvedValue({ payload: seedPayload })}
        onCreateSeed={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('无日城 初始故事提示')).toHaveTextContent('让沈昼围绕“空白日晷”展开第一次主动行动。');
    expect(screen.getByLabelText('无日城 初始故事提示')).toHaveTextContent('确认前不写入正史');

    await user.click(screen.getByRole('button', { name: '套用到表单' }));
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    expect(screen.getByLabelText('世界标题')).toHaveValue('无日城');
    expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({ title: '无日城', genre_template: 'weird_fantasy' }), { firstChapterGoal: undefined });
  });

  it('calls direct seed creation callback from the seed library', async () => {
    const user = userEvent.setup();
    const onCreateSeed = vi.fn().mockResolvedValue(undefined);
    render(
      <WorldCreationForm
        creating={false}
        onCreate={vi.fn()}
        onCreateSample={vi.fn()}
        seeds={[seedSummary]}
        selectedSeedKey={null}
        onLoadSeed={vi.fn()}
        onCreateSeed={onCreateSeed}
      />,
    );

    await user.click(screen.getByRole('button', { name: '直接创建此模板' }));

    expect(onCreateSeed).toHaveBeenCalledWith('forgotten-sun-city');
  });
});
