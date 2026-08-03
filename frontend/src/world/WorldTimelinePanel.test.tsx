import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { EventLogListResponse } from '../api/types';
import { WorldTimelinePanel } from './WorldTimelinePanel';

afterEach(() => cleanup());

const timeline: EventLogListResponse = {
  items: [
    {
      id: 2,
      world_id: 7,
      chapter_id: null,
      event_type: 'character_change',
      source_type: 'manual_edit',
      commit_id: 'commit-character',
      payload: { change: { status: 'updated' }, object_type: 'character', object_id: 1, edit_reason: '推进角色线索' },
      world_version_before: 1,
      world_version_after: 2,
      created_at: '2026-05-31T10:00:00Z',
    },
    {
      id: 3,
      world_id: 7,
      chapter_id: null,
      event_type: 'foreshadow_change',
      source_type: 'chapter_approval',
      commit_id: 'commit-foreshadow',
      payload: { change: { status: 'advanced' }, object_type: 'foreshadow', object_id: 2 },
      world_version_before: 1,
      world_version_after: 2,
      created_at: '2026-05-31T10:30:00Z',
    },
    {
      id: 1,
      world_id: 7,
      chapter_id: null,
      event_type: 'WORLD_CREATED',
      source_type: 'world_creation',
      commit_id: 'commit-created',
      payload: { title: '群星边境', genre_template: 'sci_fi', starter_counts: { characters: 2, relations: 1, foreshadows: 1 } },
      world_version_before: 0,
      world_version_after: 1,
      created_at: '2026-05-31T09:00:00Z',
    },
  ],
  total: 3,
  limit: 20,
  offset: 0,
  summary: {
    total: 4,
    event_type_counts: { WORLD_CREATED: 1, character_change: 1, foreshadow_change: 1, world_version_increment: 1 },
    latest_world_version: 2,
  },
};

describe('WorldTimelinePanel', () => {
  it('renders timeline summary and user-readable event descriptions', async () => {
    render(<WorldTimelinePanel worldId={7} onLoadEvents={vi.fn().mockResolvedValue(timeline)} />);

    expect(await screen.findByText('世界历史记录')).toBeInTheDocument();
    expect(screen.getByText('总事件：4')).toBeInTheDocument();
    expect(screen.getByText('最新世界进度：第 2 版')).toBeInTheDocument();
    expect(screen.getByText('世界已创建 × 1')).toBeInTheDocument();
    expect(screen.getByText('角色变化 × 1')).toBeInTheDocument();
    expect(screen.getByText('悬念/伏笔变化 × 1')).toBeInTheDocument();
    expect(screen.getByText('世界「群星边境」创建，题材 科幻，初始角色 2、关系 1、伏笔 1。')).toBeInTheDocument();
    expect(screen.getByText('角色已更新：#1；原因：推进角色线索')).toBeInTheDocument();
    expect(screen.getByText('悬念/伏笔已推进中：#2')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('[object Object]');
    expect(document.body).not.toHaveTextContent('WORLD_CREATED');
    expect(document.body).not.toHaveTextContent('sci_fi');
    expect(document.body).not.toHaveTextContent('character_change');
  });

  it('reloads events when an event-type filter is selected', async () => {
    const user = userEvent.setup();
    const onLoadEvents = vi.fn().mockResolvedValue(timeline);
    render(<WorldTimelinePanel worldId={7} onLoadEvents={onLoadEvents} />);

    await screen.findByText('世界历史记录');
    await user.click(screen.getByRole('button', { name: '角色变化 × 1' }));

    await waitFor(() => expect(onLoadEvents).toHaveBeenLastCalledWith(7, { limit: 20, event_type: 'character_change' }));
  });

  it('shows a localized error if timeline loading fails', async () => {
    render(<WorldTimelinePanel worldId={7} onLoadEvents={vi.fn().mockRejectedValue(new Error('timeline down'))} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('timeline down');
  });
});
