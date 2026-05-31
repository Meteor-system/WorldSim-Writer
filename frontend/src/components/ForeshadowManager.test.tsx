import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createForeshadow,
  deleteForeshadow,
  getForeshadowLedger,
  getForeshadowTimeline,
  getForeshadows,
  getStaleForeshadows,
  updateForeshadow,
} from '../api/client';
import type { Character, Foreshadow, ForeshadowLedgerResponse, StaleForeshadow } from '../api/types';
import { ForeshadowManager } from './ForeshadowManager';

vi.mock('../api/client', () => ({
  createForeshadow: vi.fn(),
  deleteForeshadow: vi.fn(),
  getForeshadowLedger: vi.fn(),
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
    source_chapter_id: 3,
    title: '裂纹玉佩',
    description: '玉佩出现裂纹。',
    foreshadow_type: 'plot',
    status: 'advanced',
    urgency_level: 4,
    related_character_ids: [1],
    expected_resolution_window: '第2-4章',
  },
  {
    id: 2,
    source_chapter_id: 1,
    title: '井中红光',
    description: '井底有红光。',
    foreshadow_type: 'world',
    status: 'planted',
    urgency_level: 5,
    related_character_ids: [2],
    expected_resolution_window: null,
  },
  {
    id: 3,
    source_chapter_id: 2,
    title: '旧盟约',
    description: '旧盟约已经兑现。',
    foreshadow_type: 'character',
    status: 'resolved',
    urgency_level: 2,
    related_character_ids: [],
    expected_resolution_window: '第5章',
  },
  {
    id: 4,
    source_chapter_id: null,
    title: '废弃暗门',
    description: '暗门线已放弃。',
    foreshadow_type: 'plot',
    status: 'expired',
    urgency_level: 1,
    related_character_ids: [],
    expected_resolution_window: null,
  },
];

const staleForeshadows: StaleForeshadow[] = [
  { foreshadow: foreshadows[1], chapters_since_planted: 6, alert_level: 'critical' },
];

const ledgerResponse: ForeshadowLedgerResponse = {
  world_id: 7,
  world_version: 3,
  summary: {
    total: 4,
    open_count: 2,
    planted_count: 1,
    advanced_count: 1,
    resolved_count: 1,
    expired_count: 1,
    high_urgency_count: 2,
    stale_count: 1,
    overdue_count: 1,
  },
  groups: {
    planted: [
      {
        foreshadow: foreshadows[1],
        status_group: 'planted',
        is_open: true,
        is_high_urgency: true,
        is_stale: true,
        is_overdue: true,
        chapters_since_planted: 6,
        pressure_level: 'critical',
        pressure_reasons: ['高紧迫度：5', '已埋设 6 章未推进', '超过建议回收窗口，请优先推进或收束'],
        related_characters: [{ id: 2, name: '沈微霜', role_type: 'ally' }],
        recent_events: [{ event_type: 'planted', chapter_id: 1, chapter_title: '第一章', note: '井底红光首次出现', created_at: '2026-05-31T00:00:00Z' }],
      },
    ],
    advanced: [
      {
        foreshadow: foreshadows[0],
        status_group: 'advanced',
        is_open: true,
        is_high_urgency: true,
        is_stale: false,
        is_overdue: false,
        chapters_since_planted: 0,
        pressure_level: 'high',
        pressure_reasons: ['高紧迫度：4', '预期收束窗口：第2-4章'],
        related_characters: [{ id: 1, name: '林砚', role_type: 'protagonist' }],
        recent_events: [{ event_type: 'advanced', chapter_id: 3, chapter_title: '第三章', note: '玉佩裂纹扩大', created_at: '2026-05-31T00:00:00Z' }],
      },
    ],
    resolved: [
      {
        foreshadow: foreshadows[2],
        status_group: 'resolved',
        is_open: false,
        is_high_urgency: false,
        is_stale: false,
        is_overdue: false,
        chapters_since_planted: 0,
        pressure_level: 'resolved',
        pressure_reasons: ['预期收束窗口：第5章'],
        related_characters: [],
        recent_events: [],
      },
    ],
    expired: [
      {
        foreshadow: foreshadows[3],
        status_group: 'expired',
        is_open: false,
        is_high_urgency: false,
        is_stale: false,
        is_overdue: false,
        chapters_since_planted: 0,
        pressure_level: 'expired',
        pressure_reasons: [],
        related_characters: [],
        recent_events: [],
      },
    ],
  },
  high_pressure: [],
};
ledgerResponse.high_pressure = [ledgerResponse.groups.planted[0], ledgerResponse.groups.advanced[0]];

beforeEach(() => {
  vi.mocked(createForeshadow).mockReset().mockResolvedValue(foreshadows[0]);
  vi.mocked(deleteForeshadow).mockReset().mockResolvedValue(undefined);
  vi.mocked(getForeshadowLedger).mockReset().mockResolvedValue(ledgerResponse);
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

  it('renders ledger summary counts and governance metadata', async () => {
    render(<ForeshadowManager worldId={7} characters={characters} />);

    expect(await screen.findByText('Foreshadow Ledger')).toBeInTheDocument();
    expect(getForeshadowLedger).toHaveBeenCalledWith(7);
    expect(screen.getByText('总数：4')).toBeInTheDocument();
    expect(screen.getByText('未收束：2')).toBeInTheDocument();
    expect(screen.getByText('Stale：1')).toBeInTheDocument();
    expect(screen.getByText('Overdue：1')).toBeInTheDocument();
    expect(screen.getByText('高紧迫：2')).toBeInTheDocument();
    expect(screen.getByText('高压力：2')).toBeInTheDocument();
    expect(screen.getByText('优先处理：井中红光、裂纹玉佩')).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent === '来源章节：#3')).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent === '收束窗口：第2-4章')).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent === '关联角色：林砚')).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent === '生命周期：活跃推进')).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent === '状态：advanced')).toBeInTheDocument();
    expect(screen.getByText('压力：高紧迫度：4；预期收束窗口：第2-4章')).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent === '最近轨迹：advanced · 第三章 · 玉佩裂纹扩大')).toBeInTheDocument();
  });

  it('filters unresolved stale overdue resolved and dropped foreshadows', async () => {
    const user = userEvent.setup();
    render(<ForeshadowManager worldId={7} characters={characters} />);

    expect(await screen.findByText('裂纹玉佩')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '未收束 2' }));
    expect(screen.getByText('裂纹玉佩')).toBeInTheDocument();
    expect(screen.getByText('井中红光')).toBeInTheDocument();
    expect(screen.queryByText('旧盟约')).not.toBeInTheDocument();
    expect(screen.queryByText('废弃暗门')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Stale 1' }));
    expect(screen.getByText('井中红光')).toBeInTheDocument();
    expect(screen.getByText('Overdue')).toBeInTheDocument();
    expect(screen.queryByText('裂纹玉佩')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Overdue 1' }));
    expect(screen.getByText('井中红光')).toBeInTheDocument();
    expect(screen.queryByText('裂纹玉佩')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '已收束 1' }));
    expect(screen.getByText('旧盟约')).toBeInTheDocument();
    expect(screen.queryByText('井中红光')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '已放弃 1' }));
    expect(screen.getByText('废弃暗门')).toBeInTheDocument();
    expect(screen.queryByText('旧盟约')).not.toBeInTheDocument();
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
    await user.click(screen.getAllByRole('button', { name: '编辑' })[0]);
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

  it('drops an unresolved foreshadow and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<ForeshadowManager worldId={7} characters={characters} onChanged={onChanged} />);

    expect(await screen.findByText('裂纹玉佩')).toBeInTheDocument();
    await user.click(screen.getAllByRole('button', { name: '放弃伏笔' })[0]);

    await waitFor(() => expect(updateForeshadow).toHaveBeenCalledWith(1, { status: 'expired' }));
    expect(getForeshadowLedger).toHaveBeenCalledTimes(2);
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('deletes a foreshadow with an optional reason and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<ForeshadowManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('裂纹玉佩');
    await user.click(screen.getAllByRole('button', { name: '删除' })[0]);
    await user.type(screen.getByPlaceholderText('删除原因（可选）'), '线索废弃');
    await user.click(screen.getByRole('button', { name: '确认删除' }));

    await waitFor(() => expect(deleteForeshadow).toHaveBeenCalledWith(1, '线索废弃'));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });
});
