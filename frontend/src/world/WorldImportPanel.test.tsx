import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ImportBatchListResponse, ImportConfirmResponse, ImportPreviewResponse, StyleHandbookPreviewResponse } from '../api/types';
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

const styleHandbookResponse: StyleHandbookPreviewResponse = {
  world_id: 7,
  source_type: 'pasted_text',
  source_title: '参考片段',
  source_rights: 'general_reference',
  cleaned_excerpt: '雨夜里，旧城门缓慢打开。',
  handbook: {
    narrative_pacing: { label: '叙事节奏', value: '中速推进，适合“铺垫-冲突-钩子”的章节结构。', evidence: '雨夜里，旧城门缓慢打开。' },
    language_density: { label: '语言密度', value: '中等语言密度，叙述与信息交代相对均衡。', evidence: '她问：“你为什么还记得那枚旧徽记？”' },
    dialogue_ratio: { label: '对白比例', value: '对白与叙述交替，用对话释放人物关系和信息。', evidence: '她问：“你为什么还记得那枚旧徽记？”' },
    scene_progression: { label: '场景推进', value: '场景意象可见，适合用地点、天气或物件带动段落转场。', evidence: '雨夜里，旧城门缓慢打开。' },
    suspense_structure: { label: '悬念结构', value: '悬念显性较强，适合每节保留一个待解问题。', evidence: '你为什么还记得那枚旧徽记？' },
    relationship_tension: { label: '人物关系张力', value: '人物关系张力明显，适合围绕承诺、亏欠、敌友转换推进。', evidence: '她问：“你为什么还记得那枚旧徽记？”' },
    foreshadowing_pattern: { label: '伏笔埋设/回收方式', value: '已有线索/预兆表达，可抽象为“先给异常，再延迟解释”的伏笔模式。', evidence: '墙缝里第二次出现同样的痕迹。' },
    do_guidelines: ['保留抽象节奏、信息密度和场景推进方式，用于原创章节生成。'],
    avoid_guidelines: ['不要复用原文句子、人物名、专有设定或标志性桥段。'],
    originality_guidelines: ['正式章节仍需经过 Studio 审稿与写入正史确认。'],
  },
  safety_notes: ['风格手册草稿只是写作参考，不会写入 canon、不会推进世界进度，也不会写入世界历史记录。', '输出只保留抽象风格和结构参数，不复用原文句子、人物名、专有设定或标志性桥段。'],
  generation_notes: ['已从参考文本提炼抽象参数。'],
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
    expect(screen.getByText('候选素材需确认后才保存；风格手册草稿只供审阅，不写入正式设定或世界历史记录。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '提炼风格手册草稿' })).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('当前只处理单份 Markdown/txt 或粘贴文本。');
    expect(document.body).not.toHaveTextContent('还没有导入批次。');
  });

  it('shows readable empty-content validation copy', async () => {
    const user = userEvent.setup();
    render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    await user.clear(screen.getByLabelText('素材正文'));
    await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));
    expect(document.body).not.toHaveTextContent('生成结构化预览');

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
    expect(screen.getByText('导入素材会先进入候选素材池，不会自动改写正式设定。')).toBeInTheDocument();
    expect(screen.getByText('系统会先解析、分类、清洗并提示冲突，确认后只写入候选素材记录，不会改动正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('导入批次审计记录');
    expect(screen.getByRole('option', { name: 'Markdown 文档' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '纯文本文件' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'txt' })).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('素材类型'), 'markdown');
    await user.clear(screen.getByLabelText('来源标题'));
    await user.type(screen.getByLabelText('来源标题'), '旧设定.md');
    await user.type(screen.getByLabelText('素材正文'), '规则：青岚城密探必须隐藏真实姓名。\n角色：沈微霜：密探，擅长伪装。\n灵感：雨夜审讯从一盏坏灯开始。');
    await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));

    await waitFor(() => expect(onPreview).toHaveBeenCalledWith(7, {
      source_type: 'markdown',
      source_title: '旧设定.md',
      content: '规则：青岚城密探必须隐藏真实姓名。\n角色：沈微霜：密探，擅长伪装。\n灵感：雨夜审讯从一盏坏灯开始。',
    }));

    expect(await screen.findByText('候选素材预览')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('结构化预览');
    expect(screen.getByText('正式设定候选')).toBeInTheDocument();
    expect(screen.getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1，需确认后才写入候选素材。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '确认写入候选素材' })).toBeInTheDocument();
    expect(screen.getByText('角色候选')).toBeInTheDocument();
    expect(screen.getByText('灵感候选')).toBeInTheDocument();
    expect(screen.getByText('青岚城密探规则')).toBeInTheDocument();
    expect(screen.getByText('这份素材可能和已有正式设定重叠：青岚城')).toBeInTheDocument();
    expect(screen.getByText('候选素材冲突提示')).toBeInTheDocument();
    expect(screen.getByText('这些提示只帮助你审阅候选素材，不会自动合并或改写正式设定。')).toBeInTheDocument();
    expect(screen.queryByText('冲突提示', { exact: true })).not.toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('正式设定 1 · 角色 1 · 灵感 1，需确认后才写入候选资产。');
    expect(document.body).not.toHaveTextContent('候选资产');
    expect(document.body).not.toHaveTextContent('canon 候选');
    expect(document.body).not.toHaveTextContent('canon 1');
    expect(document.body).not.toHaveTextContent('canon_overlap');
    expect(document.body).not.toHaveTextContent('导入内容提到已有 canon 关键词');
  });

  it('previews reference text as an abstract style handbook draft without confirming assets', async () => {
    const user = userEvent.setup();
    const onPreview = vi.fn().mockResolvedValue(previewResponse);
    const onPreviewStyleHandbook = vi.fn().mockResolvedValue(styleHandbookResponse);
    render(<WorldImportPanel worldId={7} onPreview={onPreview} onPreviewStyleHandbook={onPreviewStyleHandbook} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    await user.selectOptions(screen.getByLabelText('来源权限'), 'general_reference');
    await user.clear(screen.getByLabelText('来源标题'));
    await user.type(screen.getByLabelText('来源标题'), '参考片段');
    await user.type(screen.getByLabelText('素材正文'), '雨夜里，旧城门缓慢打开。她问：“你为什么还记得那枚旧徽记？”墙缝里第二次出现同样的痕迹。');
    await user.click(screen.getByRole('button', { name: '提炼风格手册草稿' }));

    await waitFor(() => expect(onPreviewStyleHandbook).toHaveBeenCalledWith(7, {
      source_type: 'pasted_text',
      source_title: '参考片段',
      source_rights: 'general_reference',
      content: '雨夜里，旧城门缓慢打开。她问：“你为什么还记得那枚旧徽记？”墙缝里第二次出现同样的痕迹。',
    }));
    expect(onPreview).not.toHaveBeenCalled();

    expect(await screen.findByTestId('style-handbook-preview')).toBeInTheDocument();
    expect(screen.getByText('参考文本抽象风格手册')).toBeInTheDocument();
    expect(screen.getByText('来源：参考片段 · 一般阅读参考。确认前不会保存为正式参考，也不会写入正史/canon。')).toBeInTheDocument();
    expect(screen.getByText('叙事节奏')).toBeInTheDocument();
    expect(screen.getByText('语言密度')).toBeInTheDocument();
    expect(screen.getByText('对白比例')).toBeInTheDocument();
    expect(screen.getByText('场景推进')).toBeInTheDocument();
    expect(screen.getByText('悬念结构')).toBeInTheDocument();
    expect(screen.getByText('人物关系张力')).toBeInTheDocument();
    expect(screen.getByText('伏笔埋设/回收方式')).toBeInTheDocument();
    expect(screen.getByText('不要复用原文句子、人物名、专有设定或标志性桥段。')).toBeInTheDocument();
    expect(screen.getByText('风格手册草稿只是写作参考，不会写入 canon、不会推进世界进度，也不会写入世界历史记录。')).toBeInTheDocument();
    expect(screen.queryByText('候选素材预览')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '确认写入候选素材' })).not.toBeInTheDocument();
  });

  it('offers to use the style handbook as writing reference with only abstract dimensions', async () => {
    const user = userEvent.setup();
    const onPreviewStyleHandbook = vi.fn().mockResolvedValue(styleHandbookResponse);
    const onUseStyleHandbook = vi.fn();
    render(
      <WorldImportPanel
        worldId={7}
        onPreview={vi.fn()}
        onPreviewStyleHandbook={onPreviewStyleHandbook}
        onUseStyleHandbook={onUseStyleHandbook}
        onConfirm={vi.fn()}
        onListBatches={vi.fn().mockResolvedValue(emptyBatches)}
      />,
    );

    await user.selectOptions(screen.getByLabelText('来源权限'), 'general_reference');
    await user.clear(screen.getByLabelText('来源标题'));
    await user.type(screen.getByLabelText('来源标题'), '参考片段');
    await user.type(screen.getByLabelText('素材正文'), '雨夜里，旧城门缓慢打开。');
    await user.click(screen.getByRole('button', { name: '提炼风格手册草稿' }));

    await screen.findByTestId('style-handbook-preview');
    await user.click(screen.getByRole('button', { name: '设为本次写作风格参考' }));

    expect(onUseStyleHandbook).toHaveBeenCalledTimes(1);
    const reference = onUseStyleHandbook.mock.calls[0][0];
    expect(reference.source_title).toBe('参考片段');
    expect(reference.source_rights).toBe('general_reference');
    // 只带入抽象维度，剥离原文证据，避免照抄原文
    expect(reference.handbook.narrative_pacing.value).toBe('中速推进，适合“铺垫-冲突-钩子”的章节结构。');
    expect(reference.handbook.narrative_pacing.evidence).toBeNull();
    expect(reference.handbook.language_density.evidence).toBeNull();
    expect(reference.handbook.foreshadowing_pattern.evidence).toBeNull();
    expect(reference.handbook.avoid_guidelines).toContain('不要复用原文句子、人物名、专有设定或标志性桥段。');
  });

  it('shows candidate-material fallback copy when preview generation fails', async () => {
    const user = userEvent.setup();
    render(<WorldImportPanel worldId={7} onPreview={vi.fn().mockRejectedValue('preview down')} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    await user.type(screen.getByLabelText('素材正文'), '灵感：雨夜审讯从一盏坏灯开始。');
    await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('候选素材预览生成失败');
    expect(document.body).not.toHaveTextContent('结构化预览生成失败');
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
    await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));
    await screen.findByText('正式设定候选');
    await user.click(screen.getByRole('button', { name: '确认写入候选素材' }));

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

  it('shows readable fallback copy when import records fail to load', async () => {
    render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={vi.fn().mockRejectedValue('network down')} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('导入记录加载失败');
    expect(document.body).not.toHaveTextContent('导入批次加载失败');
  });

  it('loads recent import batches as source audit history', async () => {
    const onListBatches = vi.fn().mockResolvedValue({
      world_id: 7,
      batches: [{ ...confirmResponse.batch, assets: confirmResponse.assets }],
    } satisfies ImportBatchListResponse);

    render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={onListBatches} />);

    expect(await screen.findByText('最近候选素材记录')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('最近导入批次');
    expect(screen.getByText('旧设定.md')).toBeInTheDocument();
    expect(screen.getByText('候选素材 3 项')).toBeInTheDocument();
    expect(screen.getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1')).toBeInTheDocument();
    expect(screen.getByText('候选素材写作参考')).toBeInTheDocument();
    expect(screen.getByText('正式设定候选：青岚城密探规则')).toBeInTheDocument();
    expect(screen.getByText('角色候选：沈微霜')).toBeInTheDocument();
    expect(screen.getByText('灵感候选：雨夜审讯')).toBeInTheDocument();
    expect(screen.getByText('密探必须隐藏真实姓名。')).toBeInTheDocument();
    expect(screen.getByText('这些候选素材只是写作参考，不会自动改写正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('可用创作参考');
    expect(document.body).not.toHaveTextContent('这些素材只是写作参考，不会自动改写正式设定。');
    expect(document.body).not.toHaveTextContent('正式设定 1 · 角色 1 · 灵感 1');
    expect(document.body).not.toHaveTextContent('batch #12');
    expect(document.body).not.toHaveTextContent('asset #1');
    expect(document.body).not.toHaveTextContent('inspiration');
    expect(document.body).not.toHaveTextContent('character');
    expect(document.body).not.toHaveTextContent('canon 候选');
  });
});
