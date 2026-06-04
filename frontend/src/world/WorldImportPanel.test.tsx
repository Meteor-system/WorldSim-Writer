import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ImportBatchListResponse, ImportConfirmResponse, ImportPreviewResponse } from '../api/types';
import { WorldImportPanel } from './WorldImportPanel';

const previewResponse: ImportPreviewResponse = {
  world_id: 7,
  source_type: 'markdown',
  source_title: '旧设定.md',
  cleaned_excerpt: '规则：青岚城密探必须隐藏真实姓名。',
  asset_counts: { canon: 1, character: 1, inspiration: 1 },
  conflicts: [
    {
      severity: 'warning',
      category: 'canon_overlap',
      message: '导入内容提到已有 canon 关键词：青岚城',
      matched_text: '青岚城',
      details: {},
    },
  ],
  assets: [
    {
      asset_pool: 'canon',
      title: '青岚城密探规则',
      summary: '密探必须隐藏真实姓名。',
      raw_text: '规则：青岚城密探必须隐藏真实姓名。',
      metadata: { source_line: 1, confidence: 'medium' },
    },
    {
      asset_pool: 'character',
      title: '沈微霜',
      summary: '密探，擅长伪装。',
      raw_text: '角色：沈微霜：密探，擅长伪装。',
      metadata: { source_line: 2, confidence: 'medium' },
    },
    {
      asset_pool: 'inspiration',
      title: '雨夜审讯',
      summary: '雨夜审讯从一盏坏灯开始。',
      raw_text: '灵感：雨夜审讯从一盏坏灯开始。',
      metadata: { source_line: 3, confidence: 'medium' },
    },
  ],
};

const confirmResponse: ImportConfirmResponse = {
  batch: {
    id: 12,
    world_id: 7,
    source_type: 'markdown',
    source_title: '旧设定.md',
    original_excerpt: '旧设定原文',
    cleaned_excerpt: '清洗后的旧设定',
    status: 'confirmed',
    asset_counts: { canon: 1, character: 1, inspiration: 1 },
    conflicts: previewResponse.conflicts,
    created_at: '2026-06-03T00:00:00Z',
    confirmed_at: '2026-06-03T00:00:01Z',
  },
  assets: previewResponse.assets.map((asset, index) => ({
    id: index + 1,
    world_id: 7,
    batch_id: 12,
    status: 'candidate',
    created_at: '2026-06-03T00:00:01Z',
    ...asset,
  })),
};

const emptyBatches: ImportBatchListResponse = { world_id: 7, batches: [] };

afterEach(() => cleanup());

describe('WorldImportPanel', () => {
  it('shows empty import history as safe reference guidance', async () => {
    render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    expect(await screen.findByText('还没有导入素材参考。导入后会先作为候选素材出现在下一章准备区，不会自动改写正式设定。')).toBeInTheDocument();
    expect(screen.getByText('当前一次只处理一份素材来源，粘贴正文后会先生成候选预览。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('当前只处理单份 Markdown/txt 或粘贴文本。');
    expect(document.body).not.toHaveTextContent('还没有导入批次。');
  });

  it('shows readable empty-content validation copy', async () => {
    const user = userEvent.setup();
    render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    await user.clear(screen.getByLabelText('素材正文'));
    await user.click(screen.getByRole('button', { name: '生成结构化预览' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('请先粘贴一段素材正文。');
    expect(document.body).not.toHaveTextContent('请先粘贴 Markdown、txt 或文本素材。');
  });

  it('previews imported material as grouped candidate assets with canon safety copy', async () => {
    const user = userEvent.setup();
    const onPreview = vi.fn().mockResolvedValue(previewResponse);
    render(<WorldImportPanel worldId={7} onPreview={onPreview} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    expect(screen.getByText('素材导入')).toBeInTheDocument();
    expect(screen.queryByText('Material Import')).not.toBeInTheDocument();
    expect(screen.queryByText(/P0/)).not.toBeInTheDocument();
    expect(screen.getByText('导入素材会先进入候选资产池，不会自动改写正式设定。')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Markdown 文档' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '纯文本文件' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'txt' })).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('素材类型'), 'markdown');
    await user.clear(screen.getByLabelText('来源标题'));
    await user.type(screen.getByLabelText('来源标题'), '旧设定.md');
    await user.type(screen.getByLabelText('素材正文'), '规则：青岚城密探必须隐藏真实姓名。\n角色：沈微霜：密探，擅长伪装。\n灵感：雨夜审讯从一盏坏灯开始。');
    await user.click(screen.getByRole('button', { name: '生成结构化预览' }));

    await waitFor(() => expect(onPreview).toHaveBeenCalledWith(7, {
      source_type: 'markdown',
      source_title: '旧设定.md',
      content: '规则：青岚城密探必须隐藏真实姓名。\n角色：沈微霜：密探，擅长伪装。\n灵感：雨夜审讯从一盏坏灯开始。',
    }));

    expect(await screen.findByText('正式设定候选')).toBeInTheDocument();
    expect(screen.getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1，需确认后才写入候选资产。')).toBeInTheDocument();
    expect(screen.getByText('角色候选')).toBeInTheDocument();
    expect(screen.getByText('灵感候选')).toBeInTheDocument();
    expect(screen.getByText('青岚城密探规则')).toBeInTheDocument();
    expect(screen.getByText('这份素材可能和已有正式设定重叠：青岚城')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('正式设定 1 · 角色 1 · 灵感 1，需确认后才写入候选资产。');
    expect(document.body).not.toHaveTextContent('canon 候选');
    expect(document.body).not.toHaveTextContent('canon 1');
    expect(document.body).not.toHaveTextContent('canon_overlap');
    expect(document.body).not.toHaveTextContent('导入内容提到已有 canon 关键词');
  });

  it('confirms preview assets and shows audit batch result', async () => {
    const user = userEvent.setup();
    const onPreview = vi.fn().mockResolvedValue(previewResponse);
    const onConfirm = vi.fn().mockResolvedValue(confirmResponse);
    const onConfirmed = vi.fn();
    render(
      <WorldImportPanel
        worldId={7}
        onPreview={onPreview}
        onConfirm={onConfirm}
        onListBatches={vi.fn().mockResolvedValue(emptyBatches)}
        onConfirmed={onConfirmed}
      />,
    );

    await user.clear(screen.getByLabelText('来源标题'));
    await user.type(screen.getByLabelText('来源标题'), '旧设定.md');
    await user.type(screen.getByLabelText('素材正文'), '规则：青岚城密探必须隐藏真实姓名。');
    await user.click(screen.getByRole('button', { name: '生成结构化预览' }));
    await screen.findByText('正式设定候选');
    await user.click(screen.getByRole('button', { name: '确认写入候选资产' }));

    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith(7, {
      source_type: 'pasted_text',
      source_title: '旧设定.md',
      content: '规则：青岚城密探必须隐藏真实姓名。',
      assets: previewResponse.assets,
      conflicts: previewResponse.conflicts,
    }));
    expect(onConfirmed).toHaveBeenCalledWith(confirmResponse);
    expect(await screen.findByRole('status')).toHaveTextContent('已写入候选素材。');
    expect(screen.getByText('这些候选素材会作为写作参考出现在下一章准备区，不会自动改写正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('这些素材会作为创作参考出现在下一章准备区，不会自动改写正式设定。');
    expect(screen.queryByText(/批次 #12/)).not.toBeInTheDocument();
    const audit = screen.getByTestId('import-confirmed-batch');
    expect(within(audit).getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1')).toBeInTheDocument();
    expect(within(audit).queryByText('正式设定 1 · 角色 1 · 灵感 1')).not.toBeInTheDocument();
    expect(within(audit).queryByText('canon 1 · 角色 1 · 灵感 1')).not.toBeInTheDocument();
  });

  it('loads recent import batches as source audit history', async () => {
    const onListBatches = vi.fn().mockResolvedValue({
      world_id: 7,
      batches: [{ ...confirmResponse.batch, assets: confirmResponse.assets }],
    } satisfies ImportBatchListResponse);

    render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={onListBatches} />);

    expect(await screen.findByText('最近导入批次')).toBeInTheDocument();
    expect(screen.getByText('旧设定.md')).toBeInTheDocument();
    expect(screen.getByText('候选资产 3 项')).toBeInTheDocument();
    expect(screen.getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1')).toBeInTheDocument();
    expect(screen.getByText('可用创作参考')).toBeInTheDocument();
    expect(screen.getByText('正式设定候选：青岚城密探规则')).toBeInTheDocument();
    expect(screen.getByText('角色候选：沈微霜')).toBeInTheDocument();
    expect(screen.getByText('灵感候选：雨夜审讯')).toBeInTheDocument();
    expect(screen.getByText('密探必须隐藏真实姓名。')).toBeInTheDocument();
    expect(screen.getByText('这些素材只是写作参考，不会自动改写正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('正式设定 1 · 角色 1 · 灵感 1');
    expect(document.body).not.toHaveTextContent('batch #12');
    expect(document.body).not.toHaveTextContent('asset #1');
    expect(document.body).not.toHaveTextContent('inspiration');
    expect(document.body).not.toHaveTextContent('character');
    expect(document.body).not.toHaveTextContent('canon 候选');
  });
});
