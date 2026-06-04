import { useState } from 'react';
import type { ChapterHistoryChange, ChapterHistoryDetailResponse, ChapterHistoryResponse } from '../api/types';

type Props = {
  history: ChapterHistoryResponse | null;
  loading: boolean;
  error?: string;
  onLoadDetail: (chapterId: number) => Promise<ChapterHistoryDetailResponse>;
};

function valueText(value: unknown): string {
  if (Array.isArray(value)) return value.map(String).join('、') || '无';
  if (value === null || value === undefined || value === '') return '未设置';
  return String(value);
}

function contextNames(values: Array<{ name?: string; title?: string }>): string {
  return values.map((value) => value.name ?? value.title).filter(Boolean).join('、') || '无';
}

function eventLabel(eventType: string): string {
  const labels: Record<string, string> = {
    chapter_approved: '章节已批准并写入世界历史',
    character_change: '角色状态已更新',
    foreshadow_change: '伏笔状态已更新',
    world_version_increment: '世界版本已推进',
    WORLD_CREATED: '世界已创建',
  };
  return labels[eventType] ?? '世界历史已更新';
}

function changeTarget(change: ChapterHistoryChange, nameLookup: Record<number, string>): string {
  const payloadName = typeof change.payload?.name === 'string' ? change.payload.name : undefined;
  const afterName = typeof change.after?.name === 'string' ? change.after.name : undefined;
  const beforeName = typeof change.before?.name === 'string' ? change.before.name : undefined;
  const knownName = typeof change.object_id === 'number' ? nameLookup[change.object_id] : undefined;
  const fallback = change.object_type === 'foreshadow' ? '伏笔' : '角色';
  return payloadName ?? afterName ?? beforeName ?? knownName ?? fallback;
}

function changeLines(change: ChapterHistoryChange): string[] {
  const lines: string[] = [];
  if (change.before?.status !== undefined || change.after?.status !== undefined) {
    lines.push(`状态：${valueText(change.before?.status)} → ${valueText(change.after?.status)}`);
  }
  if (change.after?.current_goals !== undefined) {
    lines.push(`目标：${valueText(change.after.current_goals)}`);
  }
  if (change.after?.description !== undefined) {
    lines.push(`说明：${valueText(change.after.description)}`);
  }
  if (change.after?.description_note !== undefined) {
    lines.push(`说明：${valueText(change.after.description_note)}`);
  }
  return lines.length > 0 ? lines : ['已写入正式变化。'];
}

function nameLookup(values: Array<{ character_id?: number; foreshadow_id?: number; name?: string; title?: string }>, idKey: 'character_id' | 'foreshadow_id'): Record<number, string> {
  return values.reduce<Record<number, string>>((lookup, value) => {
    const id = value[idKey];
    const label = value.name ?? value.title;
    if (typeof id === 'number' && label) lookup[id] = label;
    return lookup;
  }, {});
}

function ChangeList({ title, changes, targetLabel, nameLookup }: { title: string; changes: ChapterHistoryChange[]; targetLabel: string; nameLookup: Record<number, string> }) {
  return (
    <div className="rounded-2xl bg-white/35 p-4">
      <h4 className="font-black text-[#3b2511]">{title}</h4>
      {changes.length === 0 && <p className="ink-muted mt-2 text-sm">无正式变化。</p>}
      <div className="mt-3 space-y-3">
        {changes.map((change, index) => (
          <article key={`${targetLabel}-${index}`} className="rounded-xl border border-amber-900/10 bg-amber-50/40 p-3">
            <p className="text-sm font-bold text-[#5e3b1c]">{targetLabel}：{changeTarget(change, nameLookup)}</p>
            {changeLines(change).map((line) => (
              <p key={line} className="manuscript mt-2 text-sm">{line}</p>
            ))}
          </article>
        ))}
      </div>
    </div>
  );
}

export function ChapterHistoryPanel({ history, loading, error, onLoadDetail }: Props) {
  const [selectedDetail, setSelectedDetail] = useState<ChapterHistoryDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');

  async function loadDetail(chapterId: number) {
    setDetailLoading(true);
    setDetailError('');
    try {
      setSelectedDetail(await onLoadDetail(chapterId));
    } catch (err) {
      setDetailError(err instanceof Error ? err.message : '章节详情暂不可用');
    } finally {
      setDetailLoading(false);
    }
  }

  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在加载章节历史...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="book-card p-5">
        <p className="paper-error" role="alert">{error}</p>
      </section>
    );
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div>
        <p className="chapter-kicker">Approved Chapter History</p>
        <h2 className="text-2xl font-black text-[#34210f]">章节历史</h2>
      </div>

      {!history || history.chapters.length === 0 ? (
        <p className="ink-muted">还没有已批准章节。</p>
      ) : (
        <div className="space-y-3">
          {history.chapters.map((chapter) => (
            <article key={chapter.id} className="rounded-2xl border border-amber-900/15 bg-white/35 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-black text-[#3b2511]">
                    {chapter.title} · v{chapter.approved_version} · 世界 {chapter.base_world_version} → {chapter.world_version_after}
                  </h3>
                  <p className="manuscript mt-2 text-sm">{chapter.approved_excerpt}</p>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs font-bold text-[#5e3b1c]">
                    <span className="rounded-full bg-amber-100/70 px-3 py-1">事件 {chapter.event_count}</span>
                    <span className="rounded-full bg-amber-100/70 px-3 py-1">角色变化 {chapter.character_change_count}</span>
                    <span className="rounded-full bg-amber-100/70 px-3 py-1">伏笔变化 {chapter.foreshadow_change_count}</span>
                  </div>
                </div>
                <button className="secondary-button" disabled={detailLoading} onClick={() => void loadDetail(chapter.id)}>
                  查看详情
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {detailLoading && <p className="ink-muted" role="status">正在加载章节详情...</p>}
      {detailError && <p className="paper-error" role="alert">{detailError}</p>}

      {selectedDetail && (
        <article className="space-y-4 rounded-2xl border border-amber-900/15 bg-amber-50/35 p-4">
          <div>
            <p className="chapter-kicker">Chapter Detail</p>
            <h3 className="text-xl font-black text-[#34210f]">章节详情</h3>
            <p className="mt-2 text-sm font-bold text-[#5e3b1c]">
              {selectedDetail.title} · v{selectedDetail.approved_version}
            </p>
            <p className="mt-1 text-sm font-bold text-[#5e3b1c]">
              世界版本：{selectedDetail.world_version_before} → {selectedDetail.world_version_after}
            </p>
          </div>

          <div className="rounded-2xl bg-white/45 p-4">
            <h4 className="font-black text-[#3b2511]">批准正文</h4>
            <p className="manuscript mt-3 whitespace-pre-wrap">{selectedDetail.approved_content}</p>
          </div>

          <div className="rounded-2xl bg-white/35 p-4">
            <h4 className="font-black text-[#3b2511]">审批结算说明</h4>
            <p className="manuscript mt-2 text-sm">
              世界版本：第 {selectedDetail.world_version_before} 版 → 第 {selectedDetail.world_version_after} 版。
            </p>
            <p className="manuscript mt-1 text-sm">
              正式结算：角色变化 {selectedDetail.character_changes.length} 条，伏笔变化 {selectedDetail.foreshadow_changes.length} 条。
            </p>
            {selectedDetail.events.some((event) => event.event_type === 'chapter_approved') && (
              <p className="manuscript mt-1 text-sm">正式事件：章节已批准并写入世界历史。</p>
            )}
            {(selectedDetail.execution_context?.material_references ?? []).length > 0 ? (
              <div className="mt-2 space-y-1">
                {selectedDetail.execution_context?.material_references.map((reference) => (
                  <p key={`${reference.source_title}-${reference.title}`} className="manuscript text-sm">
                    导入素材参考：{reference.title}（来源：{reference.source_title}）。
                  </p>
                ))}
                <p className="manuscript text-sm font-bold text-[#5e3b1c]">这些导入素材只是本章创作参考，不代表已自动进入正式 canon。</p>
              </div>
            ) : (
              <p className="manuscript mt-1 text-sm">本章未使用导入素材参考。</p>
            )}
          </div>

          {selectedDetail.execution_context && (
            <div className="rounded-2xl bg-white/35 p-4">
              <h4 className="font-black text-[#3b2511]">执行上下文快照</h4>
              <p className="manuscript mt-2 text-sm">目标：{selectedDetail.execution_context.goal}</p>
              <p className="manuscript mt-1 text-sm">推荐 POV：{selectedDetail.execution_context.recommended_pov.name ?? '暂无'}</p>
              <p className="manuscript mt-1 text-sm">优先角色：{contextNames(selectedDetail.execution_context.priority_characters)}</p>
              <p className="manuscript mt-1 text-sm">优先伏笔：{contextNames(selectedDetail.execution_context.priority_foreshadows)}</p>
            </div>
          )}

          {selectedDetail.critic_summary && <p className="manuscript rounded-2xl bg-white/35 p-3">Critic：{selectedDetail.critic_summary}</p>}
          {selectedDetail.character_arc_summary && <p className="manuscript rounded-2xl bg-white/35 p-3">角色弧线：{selectedDetail.character_arc_summary}</p>}

          <ChangeList title="角色变化" changes={selectedDetail.character_changes} targetLabel="角色" nameLookup={nameLookup(selectedDetail.execution_context?.priority_characters ?? [], 'character_id')} />
          <ChangeList title="伏笔变化" changes={selectedDetail.foreshadow_changes} targetLabel="伏笔" nameLookup={nameLookup(selectedDetail.execution_context?.priority_foreshadows ?? [], 'foreshadow_id')} />

          <div className="rounded-2xl bg-white/35 p-4">
            <h4 className="font-black text-[#3b2511]">正式事件</h4>
            <div className="mt-3 space-y-2">
              {selectedDetail.events.map((event) => (
                <p key={event.id} className="manuscript text-sm">
                  {eventLabel(event.event_type)} · 世界第 {event.world_version_before} 版 → 第 {event.world_version_after} 版
                </p>
              ))}
            </div>
          </div>
        </article>
      )}
    </section>
  );
}
