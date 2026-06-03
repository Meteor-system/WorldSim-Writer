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
  it('previews imported material as grouped candidate assets with canon safety copy', async () => {
    const user = userEvent.setup();
    const onPreview = vi.fn().mockResolvedValue(previewResponse);
    render(<WorldImportPanel worldId={7} onPreview={onPreview} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    expect(screen.getByText('素材导入节点')).toBeInTheDocument();
    expect(screen.getByText('导入素材会先进入候选资产池，不会自动改写正式 canon。')).toBeInTheDocument();

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

    expect(await screen.findByText('canon 候选')).toBeInTheDocument();
    expect(screen.getByText('角色池候选')).toBeInTheDocument();
    expect(screen.getByText('灵感池候选')).toBeInTheDocument();
    expect(screen.getByText('青岚城密探规则')).toBeInTheDocument();
    expect(screen.getByText('导入内容提到已有 canon 关键词：青岚城')).toBeInTheDocument();
  });

  it('confirms preview assets and shows audit batch result', async () => {
    const user = userEvent.setup();
    const onPreview = vi.fn().mockResolvedValue(previewResponse);
    const onConfirm = vi.fn().mockResolvedValue(confirmResponse);
    render(<WorldImportPanel worldId={7} onPreview={onPreview} onConfirm={onConfirm} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    await user.clear(screen.getByLabelText('来源标题'));
    await user.type(screen.getByLabelText('来源标题'), '旧设定.md');
    await user.type(screen.getByLabelText('素材正文'), '规则：青岚城密探必须隐藏真实姓名。');
    await user.click(screen.getByRole('button', { name: '生成结构化预览' }));
    await screen.findByText('canon 候选');
    await user.click(screen.getByRole('button', { name: '确认写入候选资产' }));

    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith(7, {
      source_type: 'pasted_text',
      source_title: '旧设定.md',
      content: '规则：青岚城密探必须隐藏真实姓名。',
      assets: previewResponse.assets,
      conflicts: previewResponse.conflicts,
    }));
    expect(await screen.findByRole('status')).toHaveTextContent('已写入候选资产批次 #12');
    const audit = screen.getByTestId('import-confirmed-batch');
    expect(within(audit).getByText('canon 1 · 角色 1 · 灵感 1')).toBeInTheDocument();
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
  });
});
