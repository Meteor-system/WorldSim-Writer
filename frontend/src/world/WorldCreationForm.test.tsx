import '@testing-library/jest-dom/vitest';
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { StyleHandbookReference, WorldCreateRequest, WorldCreationDraftResponse, WorldCreationMaterialReference, WorldSeedSummary } from '../api/types';
import { WorldCreationForm } from './WorldCreationForm';
import { GENRE_PRESETS, starterGuidanceFromPayload } from './genrePresets';

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

const materialReferences: WorldCreationMaterialReference[] = [
  {
    source: 'import_node',
    asset_id: 42,
    title: '雾港钟楼候选素材',
    summary: '一座每天倒敲十三次的钟楼引发城内记忆错位。',
    asset_pool: 'inspiration',
    source_rights: 'general_reference',
  },
  {
    source: 'import_node',
    asset_id: 43,
    title: '失踪灯塔守望人',
    summary: '守望人留下只写了半页的航线日志。',
    asset_pool: 'character',
    source_rights: 'general_reference',
  },
];

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

    expect(screen.getByLabelText('奇幻 初始故事提示')).toHaveTextContent('首章目标');
    expect(screen.getByLabelText('奇幻 初始故事提示')).toHaveTextContent('伏笔压力');
    expect(screen.getByLabelText('题材')).toHaveValue('fantasy');
    expect(screen.getByRole('option', { name: '奇幻' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'fantasy' })).not.toBeInTheDocument();

    await user.clear(screen.getByLabelText('世界标题'));
    await user.type(screen.getByLabelText('世界标题'), '自定义群星边境');
    await user.click(screen.getByRole('button', { name: '添加关系' }));
    await user.click(screen.getByRole('button', { name: '添加伏笔' }));
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    expect(onCreate).toHaveBeenCalledOnce();
    const [submittedPayload, submittedContext] = onCreate.mock.calls[0];
    expect(submittedPayload).toEqual(expect.objectContaining({
      title: '自定义群星边境',
      starter_assets: expect.objectContaining({
        characters: expect.arrayContaining([expect.objectContaining({ name: expect.any(String), role_type: expect.any(String) })]),
        relations: expect.arrayContaining([expect.objectContaining({ source_index: 0, target_index: 1 })]),
        foreshadows: expect.arrayContaining([expect.objectContaining({ status: 'planted', urgency_level: expect.any(Number) })]),
      }),
    }));
    expect(submittedContext).toEqual({
      firstChapterGoal: starterGuidanceFromPayload(submittedPayload).first_chapter_goal,
    });
    expect(submittedContext.firstChapterGoal).toContain('艾琳·雾冠');
    expect(submittedContext.firstChapterGoal).toContain('查明古塔失衡真相');
  });

  it('derives the selected preset goal from the current form instead of a stale preset', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: /科幻/ }));
    await user.clear(screen.getByLabelText('世界标题'));
    await user.type(screen.getByLabelText('世界标题'), '修改后的群星边境');
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    const [submittedPayload, submittedContext] = onCreate.mock.calls[0];
    expect(submittedPayload.title).toBe('修改后的群星边境');
    expect(submittedContext).toEqual({
      firstChapterGoal: starterGuidanceFromPayload(submittedPayload).first_chapter_goal,
    });
    expect(submittedContext.firstChapterGoal).toContain('许砚');
    expect(submittedContext.firstChapterGoal).toContain('黑匣子脉冲');
    expect(submittedContext.firstChapterGoal).not.toBe(starterGuidanceFromPayload(GENRE_PRESETS[0]).first_chapter_goal);
  });

  it('restores the complete sci-fi preset when selecting its template card', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} />);

    await user.clear(screen.getByLabelText('世界标题'));
    await user.type(screen.getByLabelText('世界标题'), '临时标题');
    await user.clear(screen.getByLabelText('真理库 / 世界底层设定'));
    await user.type(screen.getByLabelText('真理库 / 世界底层设定'), '临时设定');
    await user.clear(screen.getByLabelText('叙事风格'));
    await user.type(screen.getByLabelText('叙事风格'), '临时风格');
    await user.click(screen.getByRole('button', { name: /科幻/ }));
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    const [submittedPayload] = onCreate.mock.calls[0];
    expect(submittedPayload).toEqual(expect.objectContaining({
      title: '群星边境',
      genre_template: 'sci_fi',
      truth_canon: expect.stringContaining('跃迁灯塔'),
      tone_profile: expect.objectContaining({ style: '冷峻太空歌剧' }),
      starter_assets: expect.objectContaining({
        characters: expect.arrayContaining([expect.objectContaining({ name: '许砚' })]),
        relations: expect.arrayContaining([expect.objectContaining({ relation_type: 'mutual_suspicion' })]),
        foreshadows: expect.arrayContaining([expect.objectContaining({ title: '黑匣子脉冲' })]),
      }),
    }));
  });

  it('changes only the genre when selecting a built-in genre', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} />);

    await user.clear(screen.getByLabelText('世界标题'));
    await user.type(screen.getByLabelText('世界标题'), '保留的自定义标题');
    await user.clear(screen.getByLabelText('真理库 / 世界底层设定'));
    await user.type(screen.getByLabelText('真理库 / 世界底层设定'), '自定义世界真理仍须保留。');
    await user.clear(screen.getByLabelText('叙事风格'));
    await user.type(screen.getByLabelText('叙事风格'), '克制悬疑');
    await user.clear(screen.getAllByLabelText('姓名')[0]);
    await user.type(screen.getAllByLabelText('姓名')[0], '自定义主角');
    await user.selectOptions(screen.getByLabelText('题材'), 'sci_fi');
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    const [submittedPayload] = onCreate.mock.calls[0];
    expect(submittedPayload).toEqual(expect.objectContaining({
      title: '保留的自定义标题',
      genre_template: 'sci_fi',
      truth_canon: '自定义世界真理仍须保留。',
      tone_profile: expect.objectContaining({ style: '克制悬疑' }),
      starter_assets: expect.objectContaining({
        characters: expect.arrayContaining([expect.objectContaining({ name: '自定义主角' })]),
        relations: expect.arrayContaining([expect.objectContaining({ source_index: 0, target_index: 1, relation_type: 'strained_alliance' })]),
        foreshadows: expect.arrayContaining([expect.objectContaining({ title: '裂开的塔心石', status: 'planted' })]),
      }),
    }));
  });

  it('blocks submission when the selected custom genre is empty', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText('题材'), 'custom');
    const customGenre = screen.getByLabelText('自定义题材名称') as HTMLInputElement;
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    expect(onCreate).not.toHaveBeenCalled();
    expect(customGenre.validity.valueMissing).toBe(true);
  });

  it('accepts and submits a custom Chinese genre without retaining an old internal value', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText('题材'), 'custom');
    const customGenre = screen.getByLabelText('自定义题材名称');
    expect(customGenre).toHaveFocus();
    expect(customGenre).toHaveValue('');
    await user.type(customGenre, '玄幻修真');
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ genre_template: '玄幻修真' }),
      expect.anything(),
    );
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

    expect(onDraftFromBrief).toHaveBeenCalledOnce();
    expect(onDraftFromBrief).toHaveBeenCalledWith('一个所有人出生时都会被分配死因的王国', null, 1);
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

  it('disables every world creation entry while a brief draft is pending', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onCreateSample = vi.fn().mockResolvedValue(undefined);
    const onCreateSeed = vi.fn().mockResolvedValue(undefined);
    const onDraftFromBrief = vi.fn().mockImplementation(() => new Promise<WorldCreationDraftResponse>(() => {}));
    const secondSeed: WorldSeedSummary = {
      ...seedSummary,
      key: 'ember-station',
      label: '余烬站',
    };
    render(
      <WorldCreationForm
        creating={false}
        onCreate={onCreate}
        onCreateSample={onCreateSample}
        onDraftFromBrief={onDraftFromBrief}
        seeds={[seedSummary, secondSeed]}
        selectedSeedKey={null}
        onLoadSeed={vi.fn()}
        onCreateSeed={onCreateSeed}
      />,
    );

    await user.type(screen.getByLabelText('一句话故事想法'), '一个等待生成的世界脑洞');
    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));

    const customCreateButton = screen.getByRole('button', { name: '创建自定义世界' });
    const sampleCreateButton = screen.getByRole('button', { name: '创建内置示例世界' });
    const seedCreateButton = screen.getAllByRole('button', { name: '直接创建此模板' })[0];
    expect(customCreateButton).toBeDisabled();
    expect(sampleCreateButton).toBeDisabled();
    for (const button of screen.getAllByRole('button', { name: '直接创建此模板' })) {
      expect(button).toBeDisabled();
    }

    fireEvent.submit(customCreateButton.closest('form')!);
    sampleCreateButton.removeAttribute('disabled');
    fireEvent.click(sampleCreateButton);
    seedCreateButton.removeAttribute('disabled');
    fireEvent.click(seedCreateButton);

    expect(onCreate).not.toHaveBeenCalled();
    expect(onCreateSample).not.toHaveBeenCalled();
    expect(onCreateSeed).not.toHaveBeenCalled();
  });

  it('keeps waiting for a delayed draft response, prevents synchronous duplicate generation, and releases the lock afterwards', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onCreateSample = vi.fn().mockResolvedValue(undefined);
    const onCreateSeed = vi.fn().mockResolvedValue(undefined);
    const draftResponse: WorldCreationDraftResponse = {
      source_brief: '一个所有人出生时都会被分配死因的王国',
      draft: draftPayload,
      first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      generation_notes: ['已生成可编辑草稿。'],
      safety_notes: ['确认前不会创建世界、写入正史或推进世界进度。'],
    };
    const secondDraftResponse: WorldCreationDraftResponse = {
      ...draftResponse,
      draft: { ...draftPayload, title: '第二次死因王国' },
    };
    let resolveDraft: ((value: WorldCreationDraftResponse) => void) | undefined;
    const onDraftFromBrief = vi.fn()
      .mockImplementationOnce(() => new Promise<WorldCreationDraftResponse>((resolve) => {
        resolveDraft = resolve;
      }))
      .mockResolvedValueOnce(secondDraftResponse);
    render(
      <WorldCreationForm
        creating={false}
        onCreate={onCreate}
        onCreateSample={onCreateSample}
        onDraftFromBrief={onDraftFromBrief}
        seeds={[seedSummary]}
        selectedSeedKey={null}
        onLoadSeed={vi.fn()}
        onCreateSeed={onCreateSeed}
      />,
    );

    await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配死因的王国');
    const draftButton = screen.getByRole('button', { name: '生成世界创建草稿' });
    act(() => {
      draftButton.click();
      draftButton.click();
    });

    const generatingButton = screen.getByRole('button', { name: '正在生成创建草稿...' });
    expect(generatingButton).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('模型正在生成，可能需要数分钟；请保持页面打开，系统会持续等待模型返回。');
    expect(onDraftFromBrief).toHaveBeenCalledOnce();
    expect(onCreate).not.toHaveBeenCalled();

    await act(async () => {
      resolveDraft?.(draftResponse);
    });

    expect(await screen.findByText('世界创建草稿已填入下方表单')).toBeInTheDocument();
    expect(screen.queryByText('模型正在生成，可能需要数分钟；请保持页面打开，系统会持续等待模型返回。')).not.toBeInTheDocument();
    expect(screen.getByLabelText('世界标题')).toHaveValue('死因王国');
    expect(screen.getByRole('button', { name: '创建自定义世界' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '创建内置示例世界' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '直接创建此模板' })).toBeEnabled();
    expect(onCreate).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));
    expect(onDraftFromBrief).toHaveBeenCalledTimes(2);
    expect(await screen.findByDisplayValue('第二次死因王国')).toBeInTheDocument();
    expect(onCreate).not.toHaveBeenCalled();
  });

  it('preserves an unknown brief genre through the custom genre input and submission', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const unknownGenreDraft = { ...draftPayload, genre_template: '架空蒸汽幻想' };
    const onDraftFromBrief = vi.fn().mockResolvedValue({
      source_brief: '蒸汽与魔法共存的架空都市',
      draft: unknownGenreDraft,
      first_chapter_goal: '让伊莱发现蒸汽核心被篡改。',
      generation_notes: [],
      safety_notes: [],
    });
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} onDraftFromBrief={onDraftFromBrief} />);

    await user.type(screen.getByLabelText('一句话故事想法'), '蒸汽与魔法共存的架空都市');
    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));

    expect(await screen.findByLabelText('自定义题材名称')).toHaveValue('架空蒸汽幻想');
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));
    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ genre_template: '架空蒸汽幻想' }),
      { firstChapterGoal: '让伊莱发现蒸汽核心被篡改。' },
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

    expect(onDraftFromBrief).toHaveBeenCalledWith('一个所有人出生时都会被分配死因的王国', null, 1);
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

    expect(onDraftFromBrief).toHaveBeenCalledWith('一个边境殖民地依赖濒临失控的跃迁灯塔', styleHandbookReference, 1);
  });

  it('passes selected import node material references when generating a brief draft', async () => {
    const user = userEvent.setup();
    const onDraftFromBrief = vi.fn().mockResolvedValue({
      source_brief: '一个边境殖民地依赖濒临失控的跃迁灯塔',
      draft: draftPayload,
      first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      generation_notes: ['已参考候选素材提炼原创方向。'],
      safety_notes: ['候选素材只读，不会写入 canon/正史或 EventLog。'],
      material_references: [materialReferences[1]],
    });
    render(
      <WorldCreationForm
        creating={false}
        onCreate={vi.fn()}
        onCreateSample={vi.fn()}
        onDraftFromBrief={onDraftFromBrief}
        materialReferences={materialReferences}
      />,
    );

    expect(screen.getByLabelText('Import Node 候选素材参考')).toHaveTextContent('只会发送标题、摘要、素材池和来源权利，不发送原文');
    expect(screen.getByLabelText('Import Node 候选素材参考')).toHaveTextContent('不会创建世界、不会写入 canon/正史，也不会写入 EventLog');
    await user.click(screen.getByLabelText(/雾港钟楼候选素材/));
    await user.type(screen.getByLabelText('一句话故事想法'), '一个边境殖民地依赖濒临失控的跃迁灯塔');
    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));

    expect(onDraftFromBrief).toHaveBeenCalledWith(
      '一个边境殖民地依赖濒临失控的跃迁灯塔',
      null,
      1,
      [materialReferences[1]],
    );
    expect(await screen.findByLabelText('本次草稿引用的候选素材')).toHaveTextContent('失踪灯塔守望人');
    expect(screen.getByLabelText('本次草稿引用的候选素材')).toHaveTextContent('只使用标题、摘要、素材池和来源权利，不使用原文');
    expect(screen.getByLabelText('本次草稿引用的候选素材')).toHaveTextContent('不会创建世界、写入 canon/正史或写入 EventLog');
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
    expect(screen.getByLabelText('题材')).toHaveValue('weird_fantasy');
    expect(screen.getByRole('option', { name: '诡秘奇幻' })).toBeInTheDocument();
    const [submittedPayload, submittedContext] = onCreate.mock.calls[0];
    expect(submittedPayload).toEqual(expect.objectContaining({ title: '无日城', genre_template: 'weird_fantasy' }));
    expect(submittedContext).toEqual({
      firstChapterGoal: starterGuidanceFromPayload(submittedPayload).first_chapter_goal,
    });
    expect(submittedContext.firstChapterGoal).toBe('让沈昼围绕“空白日晷”展开第一次主动行动，并推进目标：查明钟声。');
  });

  it('keeps seed cards scoped while applying Seed A then creating Seed B from the current key', async () => {
    const user = userEvent.setup();
    const seedB: WorldSeedSummary = {
      ...seedSummary,
      key: 'ember-station',
      label: '余烬站',
      genre_template: 'sci_fi',
      hook: '一座失联空间站正在向过去发送求救讯号。',
      starter_summary: { character_count: 1, relation_count: 0, foreshadow_count: 1, character_names: ['乔岚'], foreshadow_titles: ['回声舱门'] },
      starter_guidance: {
        first_chapter_goal: '让乔岚在回声舱门前截获第一段来自过去的求救讯号。',
        protagonist_relationships: ['乔岚 ↔ 舰桥 AI：互相试探。'],
        foreshadow_pressure: ['回声舱门在开篇就要产生倒计时压力。'],
        story_health_hints: ['确认前不写入正史。'],
      },
    };
    const seedBPayload: WorldCreateRequest = {
      ...seedPayload,
      title: '余烬站',
      genre_template: 'sci_fi',
      truth_canon: '余烬站被困在重复的一小时里。',
      starter_assets: {
        characters: [{ name: '乔岚', role_type: 'protagonist', current_goals: ['截获过去的求救讯号'] }],
        relations: [],
        foreshadows: [{ title: '回声舱门', description: '舱门在每小时归零时开启。', foreshadow_type: 'signal_clue', status: 'planted', urgency_level: 5, related_character_indexes: [0] }],
      },
    };
    const onLoadSeed = vi.fn().mockImplementation(async (key: string) => ({ payload: key === seedSummary.key ? seedPayload : seedBPayload }));
    const onCreateSeed = vi.fn().mockResolvedValue(undefined);
    render(
      <WorldCreationForm
        creating={false}
        onCreate={vi.fn()}
        onCreateSample={vi.fn()}
        seeds={[seedSummary, seedB]}
        selectedSeedKey={null}
        onLoadSeed={onLoadSeed}
        onCreateSeed={onCreateSeed}
      />,
    );

    const seedACard = screen.getByRole('heading', { name: '无日城' }).closest('article');
    const seedBCard = screen.getByRole('heading', { name: '余烬站' }).closest('article');
    expect(seedACard).not.toBeNull();
    expect(seedBCard).not.toBeNull();

    await user.click(within(seedACard!).getByRole('button', { name: '套用到表单' }));
    expect(onLoadSeed).toHaveBeenCalledWith('forgotten-sun-city');
    await user.click(within(seedBCard!).getByRole('button', { name: '直接创建此模板' }));

    expect(onCreateSeed).toHaveBeenCalledWith('ember-station');
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
