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
    }));
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
