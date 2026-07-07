import type { ArcPlanResponse } from '../api/types';
import { labelStatus, localizeBackendCopy } from './displayLabels';

type Props = {
  arcPlan: ArcPlanResponse | null;
  loading?: boolean;
  error?: string;
};

const MODE_CLASS: Record<string, string> = {
  expand: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  organize: 'border-orange-300 bg-orange-50 text-orange-950',
  pressure: 'border-amber-300 bg-amber-50 text-amber-950',
  converge: 'border-red-300 bg-red-50 text-red-950',
  payoff: 'border-purple-200 bg-purple-50 text-purple-950',
  endgame: 'border-slate-300 bg-slate-50 text-slate-950',
};

function budgetClass(budget: string): string {
  if (budget === 'locked') return 'border-red-300 bg-red-50 text-red-950';
  if (budget === 'limited') return 'border-orange-300 bg-orange-50 text-orange-950';
  return 'border-emerald-200 bg-emerald-50 text-emerald-900';
}

function treatmentClass(treatment: string): string {
  if (treatment === 'close') return 'border-red-300 bg-red-50 text-red-950';
  if (treatment === 'advance') return 'border-orange-300 bg-orange-50 text-orange-950';
  if (treatment === 'merge') return 'border-purple-200 bg-purple-50 text-purple-950';
  return 'border-amber-900/10 bg-white/45 text-[#3b2511]';
}

export function ArcPlanPanel({ arcPlan, loading, error }: Props) {
  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在读取篇章规划...</p>
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

  if (!arcPlan) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted">篇章规划与收束计划暂无数据。</p>
      </section>
    );
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">故事收束</p>
          <h2 className="text-2xl font-black text-[#34210f]">篇章规划与收束计划</h2>
          <p className="manuscript mt-2 text-sm text-[#5e3b1c]">{localizeBackendCopy(arcPlan.mode_reason)}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm font-black">
          <span className={`rounded-full border px-3 py-1 ${MODE_CLASS[arcPlan.arc_mode] ?? MODE_CLASS.pressure}`}>
            模式：{labelStatus(arcPlan.arc_mode)}
          </span>
          <span className={`rounded-full border px-3 py-1 ${budgetClass(arcPlan.expansion_budget)}`}>
            扩张预算：{labelStatus(arcPlan.expansion_budget)}
          </span>
        </div>
      </div>

      <div className="rounded-2xl bg-amber-50/60 p-4">
        <p className="text-sm font-black text-[#5e3b1c]">第 {arcPlan.next_chapter_number} 章建议目标</p>
        <p className="manuscript mt-2">{localizeBackendCopy(arcPlan.recommended_goal)}</p>
      </div>

      {arcPlan.guidance.length > 0 && (
        <div className="grid gap-3 md:grid-cols-2">
          {arcPlan.guidance.map((item) => (
            <article key={item.guidance_key} className="rounded-2xl border border-amber-900/10 bg-white/45 p-3">
              <h3 className="font-black text-[#3b2511]">{localizeBackendCopy(item.label)}</h3>
              <p className="manuscript mt-2 text-sm">{localizeBackendCopy(item.detail)}</p>
            </article>
          ))}
        </div>
      )}

      <div className="rounded-2xl bg-white/35 p-4">
        <h3 className="font-black text-[#3b2511]">收束计划</h3>
        {arcPlan.closure_items.length === 0 ? (
          <p className="ink-muted mt-2 text-sm">当前没有需要列入收束计划的开放线索。</p>
        ) : (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {arcPlan.closure_items.map((item) => (
              <article key={item.item_key} className={`rounded-2xl border p-3 ${treatmentClass(item.treatment)}`}>
                <p className="text-xs font-black tracking-[0.18em]">{labelStatus(item.treatment)} · {labelStatus(item.priority)}</p>
                <h4 className="mt-2 font-black">{localizeBackendCopy(item.title)}</h4>
                <p className="manuscript mt-2 text-sm">{localizeBackendCopy(item.rationale)}</p>
                <p className="manuscript mt-1 text-sm">建议：{localizeBackendCopy(item.suggested_next_step)}</p>
                {item.thread_id && <p className="mt-2 text-xs font-bold">关联线索：{item.thread_id}</p>}
                {item.related_character_ids.length > 0 && <p className="mt-1 text-xs font-bold">关联角色：{item.related_character_ids.join('、')}</p>}
                {item.related_foreshadow_ids.length > 0 && <p className="mt-1 text-xs font-bold">关联伏笔：{item.related_foreshadow_ids.join('、')}</p>}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
