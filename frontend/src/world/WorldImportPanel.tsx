import { useEffect, useMemo, useState } from 'react';
import type {
  ImportBatchListResponse,
  ImportBatchWithAssetsResponse,
  ImportCandidateAssetPreview,
  ImportConfirmRequest,
  ImportConfirmResponse,
  ImportPreviewRequest,
  ImportPreviewResponse,
  ImportSourceType,
} from '../api/types';

type Props = {
  worldId: number;
  readOnly?: boolean;
  onPreview: (worldId: number, data: ImportPreviewRequest) => Promise<ImportPreviewResponse>;
  onConfirm: (worldId: number, data: ImportConfirmRequest) => Promise<ImportConfirmResponse>;
  onListBatches: (worldId: number) => Promise<ImportBatchListResponse>;
};

const SOURCE_LABELS: Record<ImportSourceType, string> = {
  pasted_text: '粘贴文本',
  markdown: 'Markdown',
  txt: 'txt',
};

const POOL_LABELS: Record<ImportCandidateAssetPreview['asset_pool'], string> = {
  canon: 'canon 候选',
  character: '角色池候选',
  inspiration: '灵感池候选',
};

function countText(counts: Record<string, number>) {
  return `canon ${counts.canon ?? 0} · 角色 ${counts.character ?? 0} · 灵感 ${counts.inspiration ?? 0}`;
}

function groupAssets(assets: ImportCandidateAssetPreview[]) {
  return {
    canon: assets.filter((asset) => asset.asset_pool === 'canon'),
    character: assets.filter((asset) => asset.asset_pool === 'character'),
    inspiration: assets.filter((asset) => asset.asset_pool === 'inspiration'),
  };
}

export function WorldImportPanel({ worldId, readOnly = false, onPreview, onConfirm, onListBatches }: Props) {
  const [sourceType, setSourceType] = useState<ImportSourceType>('pasted_text');
  const [sourceTitle, setSourceTitle] = useState('粘贴素材');
  const [content, setContent] = useState('');
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [batches, setBatches] = useState<ImportBatchWithAssetsResponse[]>([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
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
        if (!cancelled) setError(err instanceof Error ? err.message : '导入批次加载失败');
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
      setError('请先粘贴 Markdown、txt 或文本素材。');
      return;
    }
    setError('');
    setConfirmed(null);
    setLoadingPreview(true);
    const request = { source_type: sourceType, source_title: sourceTitle.trim() || SOURCE_LABELS[sourceType], content: content.trim() };
    try {
      setPreview(await onPreview(worldId, request));
    } catch (err) {
      setError(err instanceof Error ? err.message : '结构化预览生成失败');
    } finally {
      setLoadingPreview(false);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : '候选资产写入失败');
    } finally {
      setConfirming(false);
    }
  }

  return (
    <section className="book-card motion-page-enter space-y-5 p-5" data-testid="world-import-panel">
      <div>
        <p className="chapter-kicker">Material Import</p>
        <h2 className="mt-2 text-2xl font-black text-[#34210f]">素材导入节点</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">导入素材会先进入候选资产池，不会自动改写正式 canon。</p>
        <p className="manuscript mt-1 text-sm text-[#5e3b1c]">系统会先解析、分类、清洗并提示冲突，确认后只写入候选资产和导入批次审计记录。</p>
      </div>

      {readOnly && <p className="rounded-2xl bg-amber-100/70 p-3 text-sm font-bold text-[#5e3b1c]">已归档小说为只读模式，不能导入新素材。</p>}

      <form className="surface-layer grid gap-4 rounded-2xl p-4 md:grid-cols-[12rem_minmax(0,1fr)]" onSubmit={submitPreview}>
        <label className="grid gap-1 text-sm font-bold text-[#4a321e]">
          素材类型
          <select className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" value={sourceType} onChange={(event) => setSourceType(event.target.value as ImportSourceType)} disabled={readOnly}>
            {Object.entries(SOURCE_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-bold text-[#4a321e]">
          来源标题
          <input className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" value={sourceTitle} onChange={(event) => setSourceTitle(event.target.value)} disabled={readOnly} />
        </label>
        <label className="grid gap-1 text-sm font-bold text-[#4a321e] md:col-span-2">
          素材正文
          <textarea className="min-h-36 rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2 leading-7" value={content} onChange={(event) => setContent(event.target.value)} disabled={readOnly} placeholder="粘贴设定文档、旧章节、大纲、角色小传或灵感片段" />
        </label>
        <div className="md:col-span-2 flex flex-wrap gap-3">
          <button type="submit" className="primary-button motion-soft-lift" disabled={readOnly || loadingPreview}>{loadingPreview ? '解析中…' : '生成结构化预览'}</button>
          <span className="self-center text-xs ink-muted">P0 只处理单份 Markdown/txt 或粘贴文本。</span>
        </div>
      </form>

      {error && <p role="alert" className="rounded-2xl bg-red-100/80 p-3 text-sm font-bold text-red-900">{error}</p>}

      {preview && (
        <div className="space-y-4" data-testid="import-preview">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-xl font-black text-[#34210f]">结构化预览</h3>
              <p className="text-sm ink-muted">{countText(preview.asset_counts)}，需确认后才写入候选资产。</p>
            </div>
            <button type="button" className="secondary-button motion-soft-lift" onClick={confirmPreview} disabled={readOnly || confirming || preview.assets.length === 0}>{confirming ? '写入中…' : '确认写入候选资产'}</button>
          </div>

          {preview.conflicts.length > 0 && (
            <div className="rounded-2xl border border-amber-900/20 bg-amber-100/70 p-4">
              <h4 className="font-black text-[#4a321e]">冲突提示</h4>
              <ul className="mt-2 space-y-2 text-sm text-[#5e3b1c]">
                {preview.conflicts.map((conflict, index) => <li key={`${conflict.category}-${index}`}>{conflict.message}</li>)}
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
          已写入候选资产批次 #{confirmed.batch.id}
          <span className="ml-2 font-normal">{countText(confirmed.batch.asset_counts)}</span>
        </div>
      )}

      <div className="space-y-3">
        <h3 className="text-lg font-black text-[#34210f]">最近导入批次</h3>
        {loadingBatches ? <p className="text-sm ink-muted">正在读取导入记录…</p> : batches.length === 0 ? <p className="text-sm ink-muted">还没有导入批次。</p> : (
          <div className="grid gap-3 md:grid-cols-2">
            {batches.map((batch) => (
              <article key={batch.id} className="surface-layer motion-soft-lift rounded-2xl p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="font-black text-[#34210f]">{batch.source_title}</h4>
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-[#5e3b1c]">候选资产 {batch.assets.length} 项</span>
                </div>
                <p className="mt-2 text-sm ink-muted">{countText(batch.asset_counts)}</p>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
