import { useEffect, useMemo, useState } from 'react';
import type {
  ImportBatchListResponse,
  ImportBatchWithAssetsResponse,
  ImportCandidateAssetPreview,
  ImportConfirmRequest,
  ImportConfirmResponse,
  ImportPreviewRequest,
  ImportPreviewResponse,
  ImportSourceRights,
  ImportSourceType,
  StyleHandbookDimension,
  StyleHandbookDraft,
  StyleHandbookPreviewRequest,
  StyleHandbookPreviewResponse,
  StyleHandbookReference,
} from '../api/types';

type Props = {
  worldId: number;
  readOnly?: boolean;
  onPreview: (worldId: number, data: ImportPreviewRequest) => Promise<ImportPreviewResponse>;
  onPreviewStyleHandbook?: (worldId: number, data: StyleHandbookPreviewRequest) => Promise<StyleHandbookPreviewResponse>;
  onUseStyleHandbook?: (reference: StyleHandbookReference) => void;
  onConfirm: (worldId: number, data: ImportConfirmRequest) => Promise<ImportConfirmResponse>;
  onListBatches: (worldId: number) => Promise<ImportBatchListResponse>;
  onConfirmed?: (response: ImportConfirmResponse) => void;
};

const SOURCE_LABELS: Record<ImportSourceType, string> = {
  pasted_text: '粘贴文本',
  markdown: 'Markdown 文档',
  txt: '纯文本文件',
};

const SOURCE_RIGHT_LABELS: Record<ImportSourceRights, string> = {
  own_work: '自有作品',
  authorized: '授权文本',
  public_domain: '公版/公共领域',
  general_reference: '一般阅读参考',
};

const POOL_LABELS: Record<ImportCandidateAssetPreview['asset_pool'], string> = {
  canon: '正式设定候选',
  character: '角色候选',
  inspiration: '灵感候选',
};

function countText(counts: Record<string, number>) {
  return `正式设定候选 ${counts.canon ?? 0} · 角色候选 ${counts.character ?? 0} · 灵感候选 ${counts.inspiration ?? 0}`;
}

function conflictText(conflict: ImportPreviewResponse['conflicts'][number]) {
  const matchedText = conflict.matched_text ? `：${conflict.matched_text}` : '';
  if (conflict.category === 'canon_overlap') return `这份素材可能和已有正式设定重叠${matchedText}`;
  if (conflict.category === 'character_duplicate') return `这份素材可能和已有角色设定重叠${matchedText}`;
  return conflict.message.replace(/canon/g, '正式设定');
}

function assetReferenceLabel(asset: { asset_pool: ImportCandidateAssetPreview['asset_pool']; title: string }) {
  return `${POOL_LABELS[asset.asset_pool]}：${asset.title}`;
}

function groupAssets(assets: ImportCandidateAssetPreview[]) {
  return {
    canon: assets.filter((asset) => asset.asset_pool === 'canon'),
    character: assets.filter((asset) => asset.asset_pool === 'character'),
    inspiration: assets.filter((asset) => asset.asset_pool === 'inspiration'),
  };
}

function handbookDimensions(handbook: StyleHandbookPreviewResponse['handbook']): StyleHandbookDimension[] {
  return [
    handbook.narrative_pacing,
    handbook.language_density,
    handbook.dialogue_ratio,
    handbook.scene_progression,
    handbook.suspense_structure,
    handbook.relationship_tension,
    handbook.foreshadowing_pattern,
  ];
}

function stripEvidence(dimension: StyleHandbookDimension): StyleHandbookDimension {
  return { label: dimension.label, value: dimension.value, evidence: null };
}

function toStyleHandbookReference(response: StyleHandbookPreviewResponse): StyleHandbookReference {
  const handbook: StyleHandbookDraft = {
    narrative_pacing: stripEvidence(response.handbook.narrative_pacing),
    language_density: stripEvidence(response.handbook.language_density),
    dialogue_ratio: stripEvidence(response.handbook.dialogue_ratio),
    scene_progression: stripEvidence(response.handbook.scene_progression),
    suspense_structure: stripEvidence(response.handbook.suspense_structure),
    relationship_tension: stripEvidence(response.handbook.relationship_tension),
    foreshadowing_pattern: stripEvidence(response.handbook.foreshadowing_pattern),
    do_guidelines: [...response.handbook.do_guidelines],
    avoid_guidelines: [...response.handbook.avoid_guidelines],
    originality_guidelines: [...response.handbook.originality_guidelines],
  };
  return {
    source_title: response.source_title,
    source_rights: response.source_rights,
    handbook,
    safety_notes: [...response.safety_notes],
  };
}

export function WorldImportPanel({ worldId, readOnly = false, onPreview, onPreviewStyleHandbook, onUseStyleHandbook, onConfirm, onListBatches, onConfirmed }: Props) {
  const [sourceType, setSourceType] = useState<ImportSourceType>('pasted_text');
  const [sourceRights, setSourceRights] = useState<ImportSourceRights>('general_reference');
  const [sourceTitle, setSourceTitle] = useState('粘贴素材');
  const [content, setContent] = useState('');
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [styleHandbook, setStyleHandbook] = useState<StyleHandbookPreviewResponse | null>(null);
  const [batches, setBatches] = useState<ImportBatchWithAssetsResponse[]>([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingStyleHandbook, setLoadingStyleHandbook] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [loadingBatches, setLoadingBatches] = useState(false);
  const [error, setError] = useState('');
  const [confirmed, setConfirmed] = useState<ImportConfirmResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingBatches(true);
    onListBatches(worldId)
      .then((response) => {
        if (!cancelled) setBatches(response.batches);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : '导入记录加载失败');
      })
      .finally(() => {
        if (!cancelled) setLoadingBatches(false);
      });
    return () => {
      cancelled = true;
    };
  }, [onListBatches, worldId]);

  const groupedAssets = useMemo(() => groupAssets(preview?.assets ?? []), [preview]);

  async function submitPreview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (readOnly) return;
    if (!content.trim()) {
      setError('请先粘贴一段素材正文。');
      return;
    }
    setError('');
    setConfirmed(null);
    setStyleHandbook(null);
    setLoadingPreview(true);
    const request = { source_type: sourceType, source_title: sourceTitle.trim() || SOURCE_LABELS[sourceType], content: content.trim() };
    try {
      setPreview(await onPreview(worldId, request));
    } catch (err) {
      setError(err instanceof Error ? err.message : '候选素材预览生成失败');
    } finally {
      setLoadingPreview(false);
    }
  }

  async function previewStyleHandbookDraft() {
    if (readOnly) return;
    if (!onPreviewStyleHandbook) {
      setError('风格手册草稿入口暂不可用');
      return;
    }
    if (!content.trim()) {
      setError('请先粘贴一段参考文本。');
      return;
    }
    setError('');
    setPreview(null);
    setConfirmed(null);
    setLoadingStyleHandbook(true);
    const request: StyleHandbookPreviewRequest = {
      source_type: sourceType,
      source_title: sourceTitle.trim() || SOURCE_LABELS[sourceType],
      source_rights: sourceRights,
      content: content.trim(),
    };
    try {
      setStyleHandbook(await onPreviewStyleHandbook(worldId, request));
    } catch (err) {
      setError(err instanceof Error ? err.message : '风格手册草稿生成失败');
    } finally {
      setLoadingStyleHandbook(false);
    }
  }

  async function confirmPreview() {
    if (!preview || readOnly) return;
    setError('');
    setConfirming(true);
    const request: ImportConfirmRequest = {
      source_type: sourceType,
      source_title: sourceTitle.trim() || SOURCE_LABELS[sourceType],
      content: content.trim(),
      assets: preview.assets,
      conflicts: preview.conflicts,
    };
    try {
      const response = await onConfirm(worldId, request);
      setConfirmed(response);
      setBatches((current) => [{ ...response.batch, assets: response.assets }, ...current]);
      onConfirmed?.(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : '候选素材写入失败');
    } finally {
      setConfirming(false);
    }
  }

  return (
    <section className="book-card motion-page-enter space-y-5 p-5" data-testid="world-import-panel">
      <div>
        <p className="chapter-kicker">素材导入</p>
        <h2 className="mt-2 text-2xl font-black text-[#34210f]">素材导入节点</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">导入素材会先进入候选素材池，不会自动改写正式设定。</p>
        <p className="manuscript mt-1 text-sm text-[#5e3b1c]">系统会先解析、分类、清洗并提示冲突，确认后只写入候选素材记录，不会改动正式设定。</p>
      </div>

      {readOnly && <p className="rounded-2xl bg-amber-100/70 p-3 text-sm font-bold text-[#5e3b1c]">已归档小说为只读模式，不能导入新素材。</p>}

      <form className="surface-layer grid gap-4 rounded-2xl p-4 md:grid-cols-[12rem_12rem_minmax(0,1fr)]" onSubmit={submitPreview}>
        <label className="grid gap-1 text-sm font-bold text-[#4a321e]">
          素材类型
          <select className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" value={sourceType} onChange={(event) => setSourceType(event.target.value as ImportSourceType)} disabled={readOnly}>
            {Object.entries(SOURCE_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-bold text-[#4a321e]">
          来源权限
          <select className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" value={sourceRights} onChange={(event) => setSourceRights(event.target.value as ImportSourceRights)} disabled={readOnly}>
            {Object.entries(SOURCE_RIGHT_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-bold text-[#4a321e]">
          来源标题
          <input className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" value={sourceTitle} onChange={(event) => setSourceTitle(event.target.value)} disabled={readOnly} />
        </label>
        <label className="grid gap-1 text-sm font-bold text-[#4a321e] md:col-span-3">
          素材正文
          <textarea className="min-h-36 rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2 leading-7" value={content} onChange={(event) => setContent(event.target.value)} disabled={readOnly} placeholder="粘贴设定文档、旧章节、大纲、角色小传或灵感片段" />
        </label>
        <div className="md:col-span-3 flex flex-wrap gap-3">
          <button type="submit" className="primary-button motion-soft-lift" disabled={readOnly || loadingPreview}>{loadingPreview ? '解析中…' : '生成候选素材预览'}</button>
          <button type="button" className="secondary-button motion-soft-lift" onClick={previewStyleHandbookDraft} disabled={readOnly || loadingStyleHandbook}>{loadingStyleHandbook ? '提炼中…' : '提炼风格手册草稿'}</button>
          <span className="self-center text-xs ink-muted">候选素材需确认后才保存；风格手册草稿只供审阅，不写入正式设定或世界历史记录。</span>
        </div>
      </form>

      {error && <p role="alert" className="rounded-2xl bg-red-100/80 p-3 text-sm font-bold text-red-900">{error}</p>}

      {styleHandbook && (
        <div className="space-y-4 rounded-3xl border border-amber-900/15 bg-white/55 p-5" data-testid="style-handbook-preview">
          <div>
            <p className="chapter-kicker">风格手册草稿</p>
            <h3 className="text-xl font-black text-[#34210f]">参考文本抽象风格手册</h3>
            <p className="manuscript mt-2 text-sm text-[#5e3b1c]">来源：{styleHandbook.source_title} · {SOURCE_RIGHT_LABELS[styleHandbook.source_rights]}。确认前不会保存为正式参考，也不会写入正史/canon。</p>
            {onUseStyleHandbook && (
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  className="secondary-button motion-soft-lift"
                  onClick={() => onUseStyleHandbook(toStyleHandbookReference(styleHandbook))}
                  disabled={readOnly}
                >设为本次写作风格参考</button>
                <span className="text-xs ink-muted">只会把抽象风格维度带入下一章创作，不会写入正史，也不会照抄原文。</span>
              </div>
            )}
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {handbookDimensions(styleHandbook.handbook).map((dimension) => (
              <article key={dimension.label} className="surface-layer rounded-2xl p-4">
                <h4 className="font-black text-[#34210f]">{dimension.label}</h4>
                <p className="manuscript mt-2 text-sm text-[#5e3b1c]">{dimension.value}</p>
                {dimension.evidence && <p className="mt-2 text-xs ink-muted">参考证据：{dimension.evidence}</p>}
              </article>
            ))}
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <section className="rounded-2xl bg-amber-50/70 p-4">
              <h4 className="font-black text-[#34210f]">可借鉴的抽象参数</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[#5e3b1c]">
                {styleHandbook.handbook.do_guidelines.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </section>
            <section className="rounded-2xl bg-red-50/70 p-4">
              <h4 className="font-black text-[#34210f]">明确不要做</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[#5e3b1c]">
                {styleHandbook.handbook.avoid_guidelines.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </section>
            <section className="rounded-2xl bg-emerald-50/70 p-4">
              <h4 className="font-black text-[#34210f]">原创使用边界</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[#5e3b1c]">
                {styleHandbook.handbook.originality_guidelines.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </section>
          </div>
          <div className="rounded-2xl border border-amber-900/15 bg-amber-100/70 p-4">
            <h4 className="font-black text-[#34210f]">安全说明</h4>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm font-bold text-[#5e3b1c]">
              {styleHandbook.safety_notes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          </div>
        </div>
      )}

      {preview && (
        <div className="space-y-4" data-testid="import-preview">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-xl font-black text-[#34210f]">候选素材预览</h3>
              <p className="text-sm ink-muted">{countText(preview.asset_counts)}，需确认后才写入候选素材。</p>
            </div>
            <button type="button" className="secondary-button motion-soft-lift" onClick={confirmPreview} disabled={readOnly || confirming || preview.assets.length === 0}>{confirming ? '写入中…' : '确认写入候选素材'}</button>
          </div>

          {preview.conflicts.length > 0 && (
            <div className="rounded-2xl border border-amber-900/20 bg-amber-100/70 p-4">
              <h4 className="font-black text-[#4a321e]">候选素材冲突提示</h4>
              <p className="manuscript mt-1 text-sm font-bold text-[#5e3b1c]">这些提示只帮助你审阅候选素材，不会自动合并或改写正式设定。</p>
              <ul className="mt-2 space-y-2 text-sm text-[#5e3b1c]">
                {preview.conflicts.map((conflict, index) => <li key={`${conflict.category}-${index}`}>{conflictText(conflict)}</li>)}
              </ul>
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-3">
            {(['canon', 'character', 'inspiration'] as const).map((pool) => (
              <section key={pool} className="surface-layer rounded-2xl p-4">
                <h4 className="font-black text-[#34210f]">{POOL_LABELS[pool]}</h4>
                <div className="mt-3 space-y-3">
                  {groupedAssets[pool].length === 0 ? <p className="text-sm ink-muted">暂无候选</p> : groupedAssets[pool].map((asset, index) => (
                    <article key={`${asset.title}-${index}`} className="motion-soft-lift rounded-2xl border border-amber-900/15 bg-white/45 p-3">
                      <h5 className="font-bold text-[#4a321e]">{asset.title}</h5>
                      <p className="mt-1 text-sm text-[#5e3b1c]">{asset.summary}</p>
                    </article>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>
      )}

      {confirmed && (
        <div role="status" className="paper-success p-4" data-testid="import-confirmed-batch">
          <p className="font-bold">已写入候选素材。</p>
          <p className="mt-1 font-normal">这些候选素材会作为写作参考出现在下一章准备区，不会自动改写正式设定。</p>
          <span className="mt-2 block font-normal">{countText(confirmed.batch.asset_counts)}</span>
        </div>
      )}

      <div className="space-y-3">
        <h3 className="text-lg font-black text-[#34210f]">最近候选素材记录</h3>
        {loadingBatches ? <p className="text-sm ink-muted">正在读取导入记录…</p> : batches.length === 0 ? <p className="text-sm ink-muted">还没有导入素材参考。导入后会先作为候选素材出现在下一章准备区，不会自动改写正式设定。</p> : (
          <div className="grid gap-3 md:grid-cols-2">
            {batches.map((batch) => (
              <article key={batch.id} className="surface-layer motion-soft-lift rounded-2xl p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="font-black text-[#34210f]">{batch.source_title}</h4>
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-[#5e3b1c]">候选素材 {batch.assets.length} 项</span>
                </div>
                <p className="mt-2 text-sm ink-muted">{countText(batch.asset_counts)}</p>
                {batch.assets.length > 0 && (
                  <div className="mt-3 rounded-2xl bg-white/45 p-3">
                    <p className="text-sm font-bold text-[#4a321e]">候选素材写作参考</p>
                    <div className="mt-2 space-y-2">
                      {batch.assets.map((asset, index) => (
                        <article key={`${asset.title}-${index}`}>
                          <p className="text-sm font-bold text-[#5e3b1c]">{assetReferenceLabel(asset)}</p>
                          <p className="manuscript mt-1 text-sm text-[#5e3b1c]">{asset.summary}</p>
                        </article>
                      ))}
                    </div>
                    <p className="manuscript mt-3 text-sm font-bold text-[#5e3b1c]">这些候选素材只是写作参考，不会自动改写正式设定。</p>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
