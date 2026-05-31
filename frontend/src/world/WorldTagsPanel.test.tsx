import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ObjectTagBulkAssignResponse, ObjectTagResponse, TagDetailResponse, TagListResponse, TagMergeResponse, TagResponse } from '../api/types';
import { WorldTagsPanel } from './WorldTagsPanel';

const tag: TagResponse = {
  id: 3,
  world_id: 7,
  name: '灯塔线',
  slug: '灯塔线',
  color: 'amber',
  created_at: '2026-05-31T00:00:00Z',
};

const targetTag: TagResponse = {
  id: 4,
  world_id: 7,
  name: '主线归档',
  slug: '主线归档',
  color: 'blue',
  created_at: '2026-05-31T00:00:00Z',
};

const olderTag: TagResponse = {
  id: 5,
  world_id: 7,
  name: '阿尔法档案',
  slug: '阿尔法档案',
  color: 'green',
  created_at: '2026-05-30T00:00:00Z',
};

const listResponse: TagListResponse = {
  world_id: 7,
  tags: [
    { ...tag, assignment_count: 1, object_type_counts: { character: 1 } },
    { ...targetTag, assignment_count: 0, object_type_counts: {} },
  ],
};

const sortableListResponse: TagListResponse = {
  world_id: 7,
  tags: [
    { ...targetTag, assignment_count: 0, object_type_counts: {} },
    { ...tag, assignment_count: 3, object_type_counts: { character: 1, chapter: 2 } },
    { ...olderTag, assignment_count: 1, object_type_counts: { foreshadow: 1 } },
  ],
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

const mixedDetailResponse: TagDetailResponse = {
  tag: { ...tag, assignment_count: 3, object_type_counts: { character: 1, foreshadow: 1, chapter: 1 } },
  objects: [
    detailResponse.objects[0],
    {
      object_type: 'foreshadow',
      object_id: 2,
      title: '黑匣子脉冲',
      subtitle: 'Foreshadow · planted · urgency 4',
      snippet: '废弃黑匣子收到来自未来的求救信号。',
      metadata: { status: 'planted' },
    },
    {
      object_type: 'chapter',
      object_id: 11,
      title: '第一章 灯塔低鸣',
      subtitle: 'Chapter · approved · world v1',
      snippet: '许砚调查灯塔异常。',
      metadata: { status: 'approved' },
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

const mergeResponse: TagMergeResponse = {
  world_id: 7,
  source_tag_id: 3,
  target_tag_id: 4,
  moved_count: 1,
  already_assigned_count: 1,
  deleted_source_tag: true,
};

function renderPanel(overrides: Partial<React.ComponentProps<typeof WorldTagsPanel>> = {}) {
  return render(
    <WorldTagsPanel
      worldId={7}
      onListTags={vi.fn().mockResolvedValue(listResponse)}
      onCreateTag={vi.fn().mockResolvedValue(tag)}
      onLoadTag={vi.fn().mockResolvedValue(detailResponse)}
      onUpdateTag={vi.fn().mockResolvedValue(tag)}
      onMergeTag={vi.fn().mockResolvedValue(mergeResponse)}
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
    expect(onDeleteTag).not.toHaveBeenCalled();
    expect(await screen.findByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '确认删除标签' }));
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

  it('merges the selected tag into another tag and loads the target detail', async () => {
    const user = userEvent.setup();
    const targetDetail: TagDetailResponse = {
      ...detailResponse,
      tag: { ...targetTag, assignment_count: 2, object_type_counts: { character: 1, foreshadow: 1 } },
    };
    const onMergeTag = vi.fn().mockResolvedValue(mergeResponse);
    const onLoadTag = vi.fn()
      .mockResolvedValueOnce(detailResponse)
      .mockResolvedValueOnce(targetDetail);
    renderPanel({ onMergeTag, onLoadTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    expect(await screen.findByText('合并标签')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('合并到标签'), '4');
    await user.click(screen.getByRole('button', { name: '合并当前标签' }));

    expect(onMergeTag).toHaveBeenCalledWith(7, 3, { target_tag_id: 4 });
    expect(await screen.findByText('标签已合并：移动 1，跳过重复 1。')).toBeInTheDocument();
    await waitFor(() => expect(onLoadTag).toHaveBeenLastCalledWith(7, 4));
  });

  it('explains that another tag is required before merging', async () => {
    renderPanel({ onListTags: vi.fn().mockResolvedValue({ world_id: 7, tags: [{ ...tag, assignment_count: 1, object_type_counts: { character: 1 } }] }) });

    await screen.findByText('灯塔线');
    await userEvent.click(screen.getByRole('button', { name: '查看 灯塔线' }));

    expect(await screen.findByText('需要至少另一个标签才能合并当前标签。')).toBeInTheDocument();
  });

  it('filters selected tag objects by object type', async () => {
    const user = userEvent.setup();
    renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    expect(await screen.findByText('许砚')).toBeInTheDocument();
    expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
    expect(screen.getByText('第一章 灯塔低鸣')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '只看伏笔 1' }));

    expect(screen.queryByText('许砚')).not.toBeInTheDocument();
    expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
    expect(screen.queryByText('第一章 灯塔低鸣')).not.toBeInTheDocument();
  });

  it('shows a targeted empty state for filters with no objects', async () => {
    const user = userEvent.setup();
    renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('许砚');
    await user.click(screen.getByRole('button', { name: '只看事件 0' }));

    expect(await screen.findByText('当前筛选下没有对象。')).toBeInTheDocument();
  });

  it('resets the object type filter when loading another tag', async () => {
    const user = userEvent.setup();
    const targetDetail: TagDetailResponse = {
      tag: { ...targetTag, assignment_count: 1, object_type_counts: { character: 1 } },
      objects: [detailResponse.objects[0]],
    };
    const onLoadTag = vi.fn()
      .mockResolvedValueOnce(mixedDetailResponse)
      .mockResolvedValueOnce(targetDetail);
    renderPanel({ onLoadTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('黑匣子脉冲');
    await user.click(screen.getByRole('button', { name: '只看伏笔 1' }));
    expect(screen.queryByText('许砚')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '查看 主线归档' }));

    expect(await screen.findByText('许砚')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '查看全部对象 1' })).toHaveClass('ring-2');
  });

  it('searches selected tag objects by text', async () => {
    const user = userEvent.setup();
    renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    expect(await screen.findByText('许砚')).toBeInTheDocument();
    expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
    expect(screen.getByText('第一章 灯塔低鸣')).toBeInTheDocument();

    await user.type(screen.getByLabelText('搜索当前标签对象'), '未来');

    expect(screen.queryByText('许砚')).not.toBeInTheDocument();
    expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
    expect(screen.queryByText('第一章 灯塔低鸣')).not.toBeInTheDocument();
    expect(screen.getByText('显示 1 / 3 个对象')).toBeInTheDocument();
  });

  it('combines tag object text search with object type filters', async () => {
    const user = userEvent.setup();
    renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('黑匣子脉冲');

    await user.click(screen.getByRole('button', { name: '只看章节 1' }));
    await user.type(screen.getByLabelText('搜索当前标签对象'), '许砚');

    expect(screen.queryByText('黑匣子脉冲')).not.toBeInTheDocument();
    expect(screen.getByText('第一章 灯塔低鸣')).toBeInTheDocument();
    expect(screen.getByText('显示 1 / 3 个对象')).toBeInTheDocument();
  });

  it('resets tag object text search when loading another tag', async () => {
    const user = userEvent.setup();
    const targetDetail: TagDetailResponse = {
      tag: { ...targetTag, assignment_count: 1, object_type_counts: { character: 1 } },
      objects: [detailResponse.objects[0]],
    };
    const onLoadTag = vi.fn()
      .mockResolvedValueOnce(mixedDetailResponse)
      .mockResolvedValueOnce(targetDetail);
    renderPanel({ onLoadTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('黑匣子脉冲');
    await user.type(screen.getByLabelText('搜索当前标签对象'), '未来');
    expect(screen.queryByText('许砚')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '查看 主线归档' }));

    expect(await screen.findByText('许砚')).toBeInTheDocument();
    expect(screen.getByLabelText('搜索当前标签对象')).toHaveValue('');
  });

  it('cancels selected tag deletion before calling the API', async () => {
    const user = userEvent.setup();
    const onDeleteTag = vi.fn().mockResolvedValue(undefined);
    renderPanel({ onDeleteTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('许砚');
    await user.click(screen.getByRole('button', { name: '删除当前标签' }));
    expect(await screen.findByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '取消删除' }));

    expect(onDeleteTag).not.toHaveBeenCalled();
    expect(screen.queryByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).not.toBeInTheDocument();
  });

  it('resets pending tag deletion when loading another tag', async () => {
    const user = userEvent.setup();
    const targetDetail: TagDetailResponse = {
      tag: { ...targetTag, assignment_count: 0, object_type_counts: {} },
      objects: [],
    };
    const onLoadTag = vi.fn()
      .mockResolvedValueOnce(detailResponse)
      .mockResolvedValueOnce(targetDetail);
    const onDeleteTag = vi.fn().mockResolvedValue(undefined);
    renderPanel({ onLoadTag, onDeleteTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('许砚');
    await user.click(screen.getByRole('button', { name: '删除当前标签' }));
    expect(await screen.findByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '查看 主线归档' }));

    expect(await screen.findByText('这个标签还没有关联对象。')).toBeInTheDocument();
    expect(screen.queryByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).not.toBeInTheDocument();
    expect(onDeleteTag).not.toHaveBeenCalled();
  });

  it('searches visible tags by name', async () => {
    const user = userEvent.setup();
    renderPanel();

    await screen.findByText('灯塔线');
    expect(screen.getByText('主线归档')).toBeInTheDocument();

    await user.type(screen.getByLabelText('搜索标签'), '归档');

    expect(screen.queryByText('灯塔线')).not.toBeInTheDocument();
    expect(screen.getByText('主线归档')).toBeInTheDocument();
    expect(screen.getByText('显示 1 / 2 个标签')).toBeInTheDocument();
  });

  it('searches visible tags by object summary', async () => {
    const user = userEvent.setup();
    renderPanel();

    await screen.findByText('灯塔线');
    await user.type(screen.getByLabelText('搜索标签'), 'character 1');

    expect(screen.getByText('灯塔线')).toBeInTheDocument();
    expect(screen.queryByText('主线归档')).not.toBeInTheDocument();
  });

  it('shows an empty state when tag search has no matches', async () => {
    const user = userEvent.setup();
    renderPanel();

    await screen.findByText('灯塔线');
    await user.type(screen.getByLabelText('搜索标签'), '不存在的标签');

    expect(await screen.findByText('当前搜索没有匹配标签。')).toBeInTheDocument();
    expect(screen.getByText('显示 0 / 2 个标签')).toBeInTheDocument();
  });

  it('clears selected tag detail when tag search hides it', async () => {
    const user = userEvent.setup();
    renderPanel({ onLoadTag: vi.fn().mockResolvedValue(detailResponse) });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    expect(await screen.findByText('许砚')).toBeInTheDocument();

    await user.type(screen.getByLabelText('搜索标签'), '归档');

    expect(screen.queryByText('许砚')).not.toBeInTheDocument();
    expect(screen.queryByText('当前标签')).not.toBeInTheDocument();
  });

  it('sorts selected tag objects by title', async () => {
    const user = userEvent.setup();
    renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('许砚');

    await user.selectOptions(screen.getByLabelText('对象排序'), 'title');

    const objectCards = screen.getAllByRole('article');
    expect(objectCards.map((card) => within(card).getByRole('heading', { level: 4 }).textContent)).toEqual([
      '第一章 灯塔低鸣',
      '黑匣子脉冲',
      '许砚',
    ]);
  });

  it('sorts searched selected tag objects by id', async () => {
    const user = userEvent.setup();
    renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('黑匣子脉冲');

    await user.type(screen.getByLabelText('搜索当前标签对象'), '许');
    await user.selectOptions(screen.getByLabelText('对象排序'), 'id');

    const objectCards = screen.getAllByRole('article');
    expect(objectCards.map((card) => within(card).getByRole('heading', { level: 4 }).textContent)).toEqual([
      '许砚',
      '第一章 灯塔低鸣',
    ]);
    expect(screen.getByText('显示 2 / 3 个对象')).toBeInTheDocument();
  });

  it('resets selected tag object sort when loading another tag', async () => {
    const user = userEvent.setup();
    const targetDetail: TagDetailResponse = {
      tag: { ...targetTag, assignment_count: 1, object_type_counts: { character: 1 } },
      objects: [detailResponse.objects[0]],
    };
    const onLoadTag = vi.fn()
      .mockResolvedValueOnce(mixedDetailResponse)
      .mockResolvedValueOnce(targetDetail);
    renderPanel({ onLoadTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('黑匣子脉冲');
    await user.selectOptions(screen.getByLabelText('对象排序'), 'title');
    expect(screen.getByLabelText('对象排序')).toHaveValue('title');

    await user.click(screen.getByRole('button', { name: '查看 主线归档' }));

    expect(await screen.findByText('许砚')).toBeInTheDocument();
    expect(screen.getByLabelText('对象排序')).toHaveValue('default');
  });

  it('sorts visible tags by assignment count', async () => {
    const user = userEvent.setup();
    renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

    await screen.findByText('灯塔线');
    await user.selectOptions(screen.getByLabelText('标签排序'), 'count');

    const tagButtons = screen.getAllByRole('button', { name: /查看 / });
    expect(tagButtons.map((button) => button.textContent)).toEqual([
      '灯塔线总数 3character 1 · chapter 2',
      '阿尔法档案总数 1foreshadow 1',
      '主线归档总数 0无对象',
    ]);
  });

  it('sorts searched tags by name', async () => {
    const user = userEvent.setup();
    renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

    await screen.findByText('灯塔线');
    await user.type(screen.getByLabelText('搜索标签'), '档');
    await user.selectOptions(screen.getByLabelText('标签排序'), 'name');

    const tagButtons = screen.getAllByRole('button', { name: /查看 / });
    expect(tagButtons.map((button) => button.textContent)).toEqual([
      '阿尔法档案总数 1foreshadow 1',
      '主线归档总数 0无对象',
    ]);
    expect(screen.getByText('显示 2 / 3 个标签')).toBeInTheDocument();
  });

  it('keeps selected tag detail when only sorting changes', async () => {
    const user = userEvent.setup();
    renderPanel({
      onListTags: vi.fn().mockResolvedValue(sortableListResponse),
      onLoadTag: vi.fn().mockResolvedValue(detailResponse),
    });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    expect(await screen.findByText('许砚')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('标签排序'), 'name');

    expect(screen.getByText('当前标签')).toBeInTheDocument();
    expect(screen.getByText('许砚')).toBeInTheDocument();
  });

  it('shows empty and error states', async () => {
    const { unmount } = renderPanel({ onListTags: vi.fn().mockResolvedValue({ world_id: 7, tags: [] }) });
    expect(await screen.findByText('还没有标签。创建一个标签来整理角色、伏笔、章节或事件。')).toBeInTheDocument();
    unmount();

    renderPanel({ onListTags: vi.fn().mockRejectedValue(new Error('tags down')) });
    expect(await screen.findByRole('alert')).toHaveTextContent('tags down');
  });
});
