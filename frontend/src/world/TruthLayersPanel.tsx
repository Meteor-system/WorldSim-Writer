import { useMemo, useState } from 'react';
import { updateWorldTruthLayers } from '../api/client';
import type { TruthLayer, WorldOverview } from '../api/types';

type Props = {
  world: WorldOverview;
  onChanged?: () => Promise<void> | void;
  readOnly?: boolean;
};

function normalizeLayer(layer: TruthLayer, index: number): TruthLayer {
  return {
    id: layer.id || ('layer-' + String(index + 1)),
    title: layer.title?.trim() || ('第' + String(index + 1) + '层'),
    content: layer.content,
    reveal_at_chapter: layer.reveal_at_chapter ?? 0,
    frozen: Boolean(layer.frozen),
  };
}

export function TruthLayersPanel({ world, onChanged, readOnly = false }: Props) {
  const initial = useMemo(
    () => (world.truth_layers ?? []).map((layer, index) => normalizeLayer(layer, index)),
    [world.truth_layers],
  );
  const [layers, setLayers] = useState<TruthLayer[]>(initial);
  const [editReason, setEditReason] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function updateLayer(index: number, patch: Partial<TruthLayer>) {
    setLayers((current) => current.map((layer, i) => (i === index ? { ...layer, ...patch } : layer)));
  }

  async function save() {
    if (layers.some((layer) => !layer.content.trim())) {
      setError('真相层正文不能为空');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await updateWorldTruthLayers(world.id, {
        truth_layers: layers.map((layer, index) => normalizeLayer(layer, index)),
        edit_reason: editReason.trim() || undefined,
      });
      setEditReason('');
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存真相层失败');
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="workbench-panel space-y-4" aria-label="世界真相层">
      <div>
        <p className="chapter-kicker">World Truth</p>
        <h2 className="text-2xl font-black text-[#34210f]">真相层</h2>
        <p className="manuscript mt-2 text-sm">冻结层写入后不可改内容；未冻结层可编辑。这些修改会提升世界版本。</p>
      </div>
      {error && <p className="paper-error" role="alert">{error}</p>}
      {layers.length === 0 && <p className="ink-muted text-sm">还没有分层真相。公开正史仍使用上方的世界正文。</p>}
      <ul className="space-y-4">
        {layers.map((layer, index) => {
          const frozen = Boolean(layer.frozen);
          const locked = frozen || readOnly;
          return (
            <li key={layer.id || index} className="rounded-2xl border border-amber-900/15 bg-white/40 p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-black text-[#3b2511]">{layer.title || ('第' + String(index + 1) + '层')}</h3>
                <label className="text-sm">
                  <input
                    type="checkbox"
                    className="mr-2 accent-amber-800"
                    checked={frozen}
                    disabled={readOnly}
                    onChange={(event) => updateLayer(index, { frozen: event.target.checked })}
                  />
                  冻结
                </label>
              </div>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">标题</span>
                <input className="paper-input mt-1" value={layer.title ?? ''} disabled={locked} onChange={(event) => updateLayer(index, { title: event.target.value })} />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">正文</span>
                <textarea className="paper-input mt-1 min-h-24" value={layer.content} disabled={locked} onChange={(event) => updateLayer(index, { content: event.target.value })} />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">揭示章节</span>
                <input className="paper-input mt-1" type="number" min={0} value={layer.reveal_at_chapter ?? 0} disabled={locked} onChange={(event) => updateLayer(index, { reveal_at_chapter: Number(event.target.value) })} />
              </label>
              {!readOnly && !frozen && (
                <button type="button" className="ghost-button" onClick={() => setLayers((current) => current.filter((_, i) => i !== index))}>删除此层</button>
              )}
            </li>
          );
        })}
      </ul>
      {!readOnly && (
        <div className="space-y-3">
          <button type="button" className="secondary-button" onClick={() => setLayers((current) => [...current, normalizeLayer({ content: '', reveal_at_chapter: 0, frozen: false }, current.length)])}>新增真相层</button>
          <label className="block">
            <span className="text-sm font-semibold text-[#4a321e]">修改原因（可选）</span>
            <input className="paper-input mt-1" value={editReason} onChange={(event) => setEditReason(event.target.value)} />
          </label>
          <button type="button" className="primary-button" disabled={saving} onClick={() => void save()}>{saving ? '保存中…' : '保存真相层'}</button>
        </div>
      )}
    </section>
  );
}
