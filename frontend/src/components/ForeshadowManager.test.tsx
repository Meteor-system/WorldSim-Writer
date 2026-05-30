import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createForeshadow,
  deleteForeshadow,
  getForeshadowTimeline,
  getForeshadows,
  getStaleForeshadows,
  updateForeshadow,
} from '../api/client';
import type { Character, Foreshadow, StaleForeshadow } from '../api/types';
import { ForeshadowManager } from './ForeshadowManager';

vi.mock('../api/client', () => ({
  createForeshadow: vi.fn(),
  deleteForeshadow: vi.fn(),
  getForeshadowTimeline: vi.fn(),
  getForeshadows: vi.fn(),
  getStaleForeshadows: vi.fn(),
  updateForeshadow: vi.fn(),
}));

const characters: Character[] = [
  { id: 1, name: '林砚', role_type: 'protagonist', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] },
  { id: 2, name: '沈微霜', role_type: 'ally', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] },
];

const foreshadows: Foreshadow[] = [
  {
    id: 1,
    source_chapter_id: null,
    title: '裂纹玉佩',
    description: '玉佩出现裂纹。',
    foreshadow_type: 'plot',
    status: 'advanced',
    urgency_level: 4,
    related_character_ids: [1],
    expected_resolution_window: '第2-4章',
  },
];

const staleForeshadows: StaleForeshadow[] = [
  { foreshadow: foreshadows[0], chapters_since_planted: 6, alert_level: 'critical' },
];

beforeEach(() => {
  vi.mocked(createForeshadow).mockReset().mockResolvedValue(foreshadows[0]);
  vi.mocked(deleteForeshadow).mockReset().mockResolvedValue(undefined);
  vi.mocked(getForeshadowTimeline).mockReset().mockResolvedValue([]);
  vi.mocked(getForeshadows).mockReset().mockResolvedValue(foreshadows);
  vi.mocked(getStaleForeshadows).mockReset().mockResolvedValue(staleForeshadows);
  vi.mocked(updateForeshadow).mockReset().mockResolvedValue(foreshadows[0]);
});

afterEach(() => cleanup());

describe('ForeshadowManager', () => {
  it('renders foreshadow cards, stale warning, and world version governance warning', async () => {
    render(<ForeshadowManager worldId={7} characters={characters} />);

    expect(await screen.findByText('裂纹玉佩')).toBeInTheDocument();
    expect(screen.getByText('这些编辑会正式写入世界状态，并使 world_version 增长。')).toBeInTheDocument();
    expect(screen.getByText('玉佩出现裂纹。')).toBeInTheDocument();
    expect(screen.getByText('⚠️ 有 1 条伏笔已超过 6 章未推进，建议尽快处理')).toBeInTheDocument();
  });

  it('creates a foreshadow and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<ForeshadowManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('裂纹玉佩');
    await user.click(screen.getByRole('button', { name: '+ 新增伏笔' }));
    await user.type(screen.getByLabelText('标题 *'), '湿信墨迹');
    await user.type(screen.getByLabelText('描述 *'), '信纸上的墨迹遇水显字。');
    await user.click(screen.getByLabelText('沈微霜'));
    await user.type(screen.getByLabelText('预期收束窗口'), '第3章');
    await user.type(screen.getByLabelText('修改原因（可选）'), '补充新线索');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(createForeshadow).toHaveBeenCalledWith(7, {
      title: '湿信墨迹',
      description: '信纸上的墨迹遇水显字。',
      foreshadow_type: 'plot',
      status: 'planted',
      urgency_level: 3,
      related_character_ids: [2],
      expected_resolution_window: '第3章',
      edit_reason: '补充新线索',
    }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('edits a foreshadow and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<ForeshadowManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('裂纹玉佩');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    const title = screen.getByLabelText('标题 *');
    await user.clear(title);
    await user.type(title, '裂纹玉佩与湿信');
    await user.type(screen.getByLabelText('修改原因（可选）'), '合并线索描述');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updateForeshadow).toHaveBeenCalledWith(1, expect.objectContaining({
      title: '裂纹玉佩与湿信',
      description: '玉佩出现裂纹。',
      foreshadow_type: 'plot',
      status: 'advanced',
      urgency_level: 4,
      related_character_ids: [1],
      expected_resolution_window: '第2-4章',
      edit_reason: '合并线索描述',
    })));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('advances foreshadow status and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<ForeshadowManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('裂纹玉佩');
    await user.click(screen.getByRole('button', { name: '已推进' }));

    await waitFor(() => expect(updateForeshadow).toHaveBeenCalledWith(1, { status: 'resolved' }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('deletes a foreshadow with an optional reason and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<ForeshadowManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('裂纹玉佩');
    await user.click(screen.getByRole('button', { name: '删除' }));
    await user.type(screen.getByPlaceholderText('删除原因（可选）'), '线索废弃');
    await user.click(screen.getByRole('button', { name: '确认删除' }));

    await waitFor(() => expect(deleteForeshadow).toHaveBeenCalledWith(1, '线索废弃'));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });
});
