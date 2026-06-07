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

const briefFirstChapterGoal = '莉塔在命簿归档夜发现自己的死因栏是空白，并带走第一张空白命簿页。';

const briefDraftPayload: WorldCreateRequest = {
  title: '死因王国',
  genre_template: 'political_fantasy',
  truth_canon: '赫洛王国会在每个孩子出生时分配未来死因，命簿最近出现空白页。',
  tone_profile: { style: '政治奇幻', pacing: '制度压力与个人选择交替推进' },
  starter_assets: {
    characters: [
      { name: '莉塔', role_type: 'protagonist', status: '命簿抄录员', public_profile: { identity: '命簿抄录员', skill: '解读死因文书' }, hidden_traits: { secret: '她的死因栏是空白' }, destiny_flag: '空白死因持有者', current_goals: ['查清空白死因'] },
      { name: '维克托公爵', role_type: 'rival', status: '荣耀死因贵族', public_profile: { identity: '王国公爵', skill: '操控命簿审判' }, hidden_traits: { secret: '他的荣耀死因被篡改过' }, current_goals: ['夺回空白命簿页'] },
    ],
    relations: [{ source_index: 0, target_index: 1, relation_type: 'rival', intensity: 4, visibility: 'public' }],
    foreshadows: [{ title: '空白命簿页', description: '命簿中出现没有名字也没有死因的空白页。', foreshadow_type: 'fate_clue', status: 'planted', urgency_level: 4, related_character_indexes: [0, 1], expected_resolution_window: '第2-5章' }],
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
    expect(screen.getByRole('button', { name: '创建自定义世界' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '创建世界并生成第一章草稿' })).not.toBeInTheDocument();
    expect(screen.queryByText('确认创建后会进入第一章草稿审阅；第一章仍需在创作台点击“写入正史并更新世界”才会正式生效。')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    expect(onCreate).toHaveBeenCalledOnce();
    expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({
      title: '自定义群星边境',
      starter_assets: expect.objectContaining({
        characters: expect.arrayContaining([expect.objectContaining({ name: expect.any(String), role_type: expect.any(String) })]),
        relations: expect.arrayContaining([expect.objectContaining({ source_index: 0, target_index: 1 })]),
        foreshadows: expect.arrayContaining([expect.objectContaining({ status: 'planted', urgency_level: expect.any(Number) })]),
      }),
    }));
    expect(onCreate.mock.calls[0][1]).toBeUndefined();
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
    expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({ title: '无日城', genre_template: 'weird_fantasy' }));
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

    await user.click(screen.getByRole('button', { name: '直接创建此胚胎' }));

    expect(onCreateSeed).toHaveBeenCalledWith('forgotten-sun-city');
  });

  it('renders a one-sentence story entry with canon safety copy', () => {
    render(<WorldCreationForm creating={false} onCreate={vi.fn()} onCreateSample={vi.fn()} onExpandBrief={vi.fn()} />);

    expect(screen.getByRole('heading', { name: '一句话开书' })).toBeInTheDocument();
    expect(screen.getByLabelText('一句话故事想法')).toBeInTheDocument();
    expect(screen.getByText('生成草稿只会填入下方表单，不会创建世界，也不会写入正史。')).toBeInTheDocument();
  });

  it('fills the editable form from a one-sentence draft without creating a world', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onExpandBrief = vi.fn().mockResolvedValue({
      payload: briefDraftPayload,
      first_chapter_goal: briefFirstChapterGoal,
      rationale: '从死因制度补全政治奇幻世界。',
      assumptions: ['主角需要能接触命簿制度。'],
      safety_notes: ['这是原创世界创建草稿，不会自动创建世界或写入正史。'],
    });
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} onExpandBrief={onExpandBrief} />);

    await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配未来死因的王国');
    await user.click(screen.getByRole('button', { name: '生成创建草稿' }));

    expect(onExpandBrief).toHaveBeenCalledWith({ brief: '一个所有人出生时都会被分配未来死因的王国' });
    expect(screen.getByLabelText('世界标题')).toHaveValue('死因王国');
    expect(screen.getByLabelText('叙事风格')).toHaveValue('政治奇幻');
    expect(screen.getByLabelText('真理库 / 世界底层设定')).toHaveValue('赫洛王国会在每个孩子出生时分配未来死因，命簿最近出现空白页。');
    expect(screen.getAllByDisplayValue('莉塔').length).toBeGreaterThan(0);
    expect(screen.getByText('草稿已填入下方表单。请检查标题、设定、角色和伏笔，确认后再创建世界。')).toBeInTheDocument();
    expect(screen.getByText('现在还没有创建世界，也没有写入正史。只有点击“创建世界并生成第一章草稿”后才会创建。')).toBeInTheDocument();
    expect(screen.getByText('确认创建后会进入第一章草稿审阅；第一章仍需在创作台点击“写入正史并更新世界”才会正式生效。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建世界并生成第一章草稿' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '创建自定义世界' })).not.toBeInTheDocument();
    expect(screen.getByText('从死因制度补全政治奇幻世界。')).toBeInTheDocument();
    expect(screen.getByText('主角需要能接触命簿制度。')).toBeInTheDocument();
    expect(screen.getByText('这是原创世界创建草稿，不会自动创建世界或写入正史。')).toBeInTheDocument();
    expect(onCreate).not.toHaveBeenCalled();
  });

  it('starts a first-draft review path only after creating a brief-autofilled world', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onExpandBrief = vi.fn().mockResolvedValue({ payload: briefDraftPayload, first_chapter_goal: briefFirstChapterGoal });
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} onExpandBrief={onExpandBrief} />);

    await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配未来死因的王国');
    await user.click(screen.getByRole('button', { name: '生成创建草稿' }));
    await user.click(screen.getByRole('button', { name: '创建世界并生成第一章草稿' }));

    expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({ title: '死因王国' }), { autoStartFirstDraft: true, firstChapterGoal: briefFirstChapterGoal });
  });

  it('shows a friendly retry message when brief expansion fails and keeps current form data', async () => {
    const user = userEvent.setup();
    const onExpandBrief = vi.fn().mockRejectedValue(new Error('PROTECTED_REFERENCE_TERMS'));
    render(<WorldCreationForm creating={false} onCreate={vi.fn()} onCreateSample={vi.fn()} onExpandBrief={onExpandBrief} />);

    await user.clear(screen.getByLabelText('世界标题'));
    await user.type(screen.getByLabelText('世界标题'), '手动保留标题');
    await user.type(screen.getByLabelText('一句话故事想法'), '一个魔法学校里的少年冒险故事');
    await user.click(screen.getByRole('button', { name: '生成创建草稿' }));

    expect(screen.getByRole('alert')).toHaveTextContent('草稿里可能包含受保护作品的专有名称或设定，请换成更原创的一句话后重试。');
    expect(screen.getByLabelText('世界标题')).toHaveValue('手动保留标题');
  });

  it('can cancel a pending one-sentence draft request', async () => {
    const user = userEvent.setup();
    let resolveDraft: (value: { payload: WorldCreateRequest }) => void = () => undefined;
    const onExpandBrief = vi.fn().mockReturnValue(new Promise((resolve) => { resolveDraft = resolve; }));
    render(<WorldCreationForm creating={false} onCreate={vi.fn()} onCreateSample={vi.fn()} onExpandBrief={onExpandBrief} />);

    await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配未来死因的王国');
    await user.click(screen.getByRole('button', { name: '生成创建草稿' }));
    expect(screen.getByRole('button', { name: '取消生成' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '取消生成' }));
    resolveDraft({ payload: briefDraftPayload });

    expect(await screen.findByLabelText('世界标题')).not.toHaveValue('死因王国');
    expect(screen.getByText('已取消生成，可以修改一句话后重新尝试。')).toBeInTheDocument();
  });

  it('uses a layered responsive creation layout with motion classes', () => {
    render(<WorldCreationForm creating={false} onCreate={vi.fn()} onCreateSample={vi.fn()} />);

    const form = screen.getByTestId('world-creation-form');
    expect(form).toHaveClass('motion-page-enter');

    const loop = screen.getByTestId('newcomer-loop-panel');
    expect(loop).toHaveClass('surface-layer');

    const presetGrid = screen.getByTestId('genre-preset-grid');
    expect(presetGrid).toHaveClass('gap-4');
    expect(presetGrid).toHaveClass('md:grid-cols-3');
  });
});
