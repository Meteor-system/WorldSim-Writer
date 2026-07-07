import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { WorldCreateRequest, WorldSeedSummary } from '../api/types';
import { WorldCreationForm } from './WorldCreationForm';

afterEach(() => cleanup());

const seedSummary: WorldSeedSummary = {
  key: 'forgotten-sun-city',
  label: '无日城',
  genre_template: 'weird_fantasy',
  hook: '所有人都忘记太阳存在过。',
  tension_profile: ['集体失忆'],
  starter_summary: { character_count: 1, relation_count: 0, foreshadow_count: 1, character_names: ['沈昼'], foreshadow_titles: ['空白日晷'] },
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

    expect(onDraftFromBrief).toHaveBeenCalledWith('一个所有人出生时都会被分配死因的王国');
    expect(onCreate).not.toHaveBeenCalled();
    expect(await screen.findByText('世界创建草稿已填入下方表单')).toBeInTheDocument();
    expect(screen.getByText('确认前不会创建世界、写入正史或推进世界进度。')).toBeInTheDocument();
    expect(screen.getByLabelText('世界标题')).toHaveValue('死因王国');

    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));
    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ title: '死因王国', genre_template: 'fantasy' }),
      { firstChapterGoal: '让伊莱发现自己的死因记录被烧穿。' },
    );
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
