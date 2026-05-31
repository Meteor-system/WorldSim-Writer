import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ObjectTagBulkAssignResponse, ObjectTagResponse, TagDetailResponse, TagListResponse, TagResponse } from '../api/types';
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

const bulkAssignment: ObjectTagBulkAssignResponse = {
  world_id: 7,
  tag_id: 3,
  object_type: 'foreshadow',
  requested_count: 3,
  assigned_count: 2,
  already_assigned_count: 1,
  assigned_object_ids: [2, 3],
  already_assigned_object_ids: [1],
};

function renderPanel(overrides: Partial<React.ComponentProps<typeof WorldTagsPanel>> = {}) {
  return render(
    <WorldTagsPanel
      worldId={7}
      onListTags={vi.fn().mockResolvedValue(listResponse)}
      onCreateTag={vi.fn().mockResolvedValue(tag)}
      onLoadTag={vi.fn().mockResolvedValue(detailResponse)}
      onUpdateTag={vi.fn().mockResolvedValue(tag)}
      onAssignTag={vi.fn().mockResolvedValue(assignment)}
      onBulkAssignTag={vi.fn().mockResolvedValue(bulkAssignment)}
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

  it('creates, assigns, bulk assigns, unassigns, and deletes tags', async () => {
    const user = userEvent.setup();
    const onCreateTag = vi.fn().mockResolvedValue(tag);
    const onAssignTag = vi.fn().mockResolvedValue(assignment);
    const onBulkAssignTag = vi.fn().mockResolvedValue(bulkAssignment);
    const onUnassignTag = vi.fn().mockResolvedValue(undefined);
    const onDeleteTag = vi.fn().mockResolvedValue(undefined);
    renderPanel({ onCreateTag, onAssignTag, onBulkAssignTag, onUnassignTag, onDeleteTag });

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

    await user.type(screen.getByLabelText('批量对象 ID'), '1, 2\n3');
    await user.click(screen.getByRole('button', { name: '批量添加对象标签' }));
    expect(onBulkAssignTag).toHaveBeenCalledWith(7, 3, { object_type: 'foreshadow', object_ids: [1, 2, 3] });
    expect(await screen.findByText('批量打标完成：新增 2，已存在 1。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '移除标签' }));
    expect(onUnassignTag).toHaveBeenCalledWith(7, 3, 'character', 1);

    await user.click(screen.getByRole('button', { name: '删除当前标签' }));
    expect(onDeleteTag).toHaveBeenCalledWith(7, 3);
  });

  it('rejects invalid bulk object ID lists', async () => {
    const user = userEvent.setup();
    const onBulkAssignTag = vi.fn().mockResolvedValue(bulkAssignment);
    renderPanel({ onBulkAssignTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('批量对象 ID');
    await user.type(screen.getByLabelText('批量对象 ID'), '1, abc');
    await user.click(screen.getByRole('button', { name: '批量添加对象标签' }));

    expect(onBulkAssignTag).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent('请输入有效对象 ID 列表');
  });

  it('edits the selected tag name and clears color', async () => {
    const user = userEvent.setup();
    const updatedTag: TagResponse = { ...tag, name: '主线压力', slug: '主线压力', color: null };
    const updatedDetail: TagDetailResponse = {
      ...detailResponse,
      tag: { ...detailResponse.tag, name: '主线压力', slug: '主线压力', color: null },
    };
    const onUpdateTag = vi.fn().mockResolvedValue(updatedTag);
    const onLoadTag = vi.fn()
      .mockResolvedValueOnce(detailResponse)
      .mockResolvedValueOnce(updatedDetail);
    renderPanel({ onUpdateTag, onLoadTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    expect(await screen.findByText('编辑标签')).toBeInTheDocument();

    await user.clear(screen.getByLabelText('编辑标签名称'));
    await user.type(screen.getByLabelText('编辑标签名称'), ' 主线压力 ');
    await user.clear(screen.getByLabelText('编辑标签颜色'));
    await user.click(screen.getByRole('button', { name: '保存标签修改' }));

    expect(onUpdateTag).toHaveBeenCalledWith(7, 3, { name: '主线压力', color: null });
    expect(await screen.findByText('标签已更新。')).toBeInTheDocument();
    await waitFor(() => expect(onLoadTag).toHaveBeenLastCalledWith(7, 3));
  });

  it('requires a name before updating a tag', async () => {
    const user = userEvent.setup();
    const onUpdateTag = vi.fn().mockResolvedValue(tag);
    renderPanel({ onUpdateTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('编辑标签');
    await user.clear(screen.getByLabelText('编辑标签名称'));
    await user.click(screen.getByRole('button', { name: '保存标签修改' }));

    expect(onUpdateTag).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent('请输入标签名称');
  });

  it('shows empty and error states', async () => {
    const { unmount } = renderPanel({ onListTags: vi.fn().mockResolvedValue({ world_id: 7, tags: [] }) });
    expect(await screen.findByText('还没有标签。创建一个标签来整理角色、伏笔、章节或事件。')).toBeInTheDocument();
    unmount();

    renderPanel({ onListTags: vi.fn().mockRejectedValue(new Error('tags down')) });
    expect(await screen.findByRole('alert')).toHaveTextContent('tags down');
  });
});
