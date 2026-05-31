import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ObjectTagResponse, TagDetailResponse, TagListResponse, TagResponse } from '../api/types';
import { WorldTagsPanel } from './WorldTagsPanel';

const tag: TagResponse = {
  id: 3,
  world_id: 7,
  name: '灯塔线',
  slug: '灯塔线',
  color: 'amber',
  created_at: '2026-05-31T00:00:00Z',
};

const listResponse: TagListResponse = {
  world_id: 7,
  tags: [{ ...tag, assignment_count: 1, object_type_counts: { character: 1 } }],
};

const detailResponse: TagDetailResponse = {
  tag: { ...tag, assignment_count: 1, object_type_counts: { character: 1 } },
  objects: [
    {
      object_type: 'character',
      object_id: 1,
      title: '许砚',
      subtitle: 'Character · protagonist · active',
      snippet: '查明灯塔异常',
      metadata: { status: 'active' },
    },
  ],
};

const assignment: ObjectTagResponse = {
  id: 9,
  world_id: 7,
  tag_id: 3,
  object_type: 'character',
  object_id: 1,
  created_at: '2026-05-31T00:00:00Z',
};

function renderPanel(overrides: Partial<React.ComponentProps<typeof WorldTagsPanel>> = {}) {
  return render(
    <WorldTagsPanel
      worldId={7}
      onListTags={vi.fn().mockResolvedValue(listResponse)}
      onCreateTag={vi.fn().mockResolvedValue(tag)}
      onLoadTag={vi.fn().mockResolvedValue(detailResponse)}
      onAssignTag={vi.fn().mockResolvedValue(assignment)}
      onUnassignTag={vi.fn().mockResolvedValue(undefined)}
      onDeleteTag={vi.fn().mockResolvedValue(undefined)}
      {...overrides}
    />,
  );
}

afterEach(() => cleanup());

describe('WorldTagsPanel', () => {
  it('loads tags and displays selected tag detail', async () => {
    const onListTags = vi.fn().mockResolvedValue(listResponse);
    const onLoadTag = vi.fn().mockResolvedValue(detailResponse);
    renderPanel({ onListTags, onLoadTag });

    expect(screen.getByText('Tags / Collections')).toBeInTheDocument();
    expect(screen.getByText('标签只用于资料归档，不会写入 canon 或推进世界版本。')).toBeInTheDocument();
    expect(await screen.findByText('灯塔线')).toBeInTheDocument();
    expect(screen.getByText('总数 1')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: '查看 灯塔线' }));

    await waitFor(() => expect(onLoadTag).toHaveBeenCalledWith(7, 3));
    expect(await screen.findByText('许砚')).toBeInTheDocument();
    expect(screen.getByText('查明灯塔异常')).toBeInTheDocument();
  });

  it('creates, assigns, unassigns, and deletes tags', async () => {
    const user = userEvent.setup();
    const onCreateTag = vi.fn().mockResolvedValue(tag);
    const onAssignTag = vi.fn().mockResolvedValue(assignment);
    const onUnassignTag = vi.fn().mockResolvedValue(undefined);
    const onDeleteTag = vi.fn().mockResolvedValue(undefined);
    renderPanel({ onCreateTag, onAssignTag, onUnassignTag, onDeleteTag });

    await screen.findByText('灯塔线');
    await user.type(screen.getByLabelText('新标签名称'), '主线压力');
    await user.type(screen.getByLabelText('标签颜色'), 'red');
    await user.click(screen.getByRole('button', { name: '创建标签' }));
    expect(onCreateTag).toHaveBeenCalledWith(7, { name: '主线压力', color: 'red' });

    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('许砚');
    await user.selectOptions(screen.getByLabelText('对象类型'), 'foreshadow');
    await user.clear(screen.getByLabelText('对象 ID'));
    await user.type(screen.getByLabelText('对象 ID'), '2');
    await user.click(screen.getByRole('button', { name: '添加对象标签' }));
    expect(onAssignTag).toHaveBeenCalledWith(7, 3, { object_type: 'foreshadow', object_id: 2 });

    await user.click(screen.getByRole('button', { name: '移除标签' }));
    expect(onUnassignTag).toHaveBeenCalledWith(7, 3, 'character', 1);

    await user.click(screen.getByRole('button', { name: '删除当前标签' }));
    expect(onDeleteTag).toHaveBeenCalledWith(7, 3);
  });

  it('shows empty and error states', async () => {
    const { unmount } = renderPanel({ onListTags: vi.fn().mockResolvedValue({ world_id: 7, tags: [] }) });
    expect(await screen.findByText('还没有标签。创建一个标签来整理角色、伏笔、章节或事件。')).toBeInTheDocument();
    unmount();

    renderPanel({ onListTags: vi.fn().mockRejectedValue(new Error('tags down')) });
    expect(await screen.findByRole('alert')).toHaveTextContent('tags down');
  });
});
