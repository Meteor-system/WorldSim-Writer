import type { ArcPlanResponse } from '../api/types';

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

const ARC_MODE_LABELS: Record<string, string> = {
  expand: '扩展世界与人物',
  organize: '整理线索',
  pressure: '提高叙事压力',
  converge: '收束旧线索',
  payoff: '兑现承诺',
  endgame: '终局推进',
};

const EXPANSION_BUDGET_LABELS: Record<string, string> = {
  locked: '暂停新增',
  limited: '谨慎新增',
  open: '可以新增',
};

const TREATMENT_LABELS: Record<string, string> = {
  close: '本章收束',
  advance: '继续推进',
  merge: '合并处理',
  watch: '继续观察',
};

const PRIORITY_LABELS: Record<string, string> = {
  must_close: '必须处理',
  should_advance: '建议推进',
  can_delay: '可以稍后处理',
  can_leave_open: '可继续保留',
};

const THREAD_TYPE_LABELS: Record<string, string> = {
  foreshadow: '伏笔线索',
  character_goal: '角色目标',
  progression_hint: '推进提示',
  health_risk: '健康风险',
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

function labelFrom(map: Record<string, string>, value: string): string {
  return map[value] ?? value.replace(/_/g, ' ');
}

function labelThreadSource(threadId: string): string {
  const [threadType] = threadId.split(':');
  return THREAD_TYPE_LABELS[threadType] ?? '叙事线索';
}

export function ArcPlanPanel({ arcPlan, loading, error }: Props) {
  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在读取篇章模式...</p>
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
        <p className="ink-muted">篇章模式与收束计划暂无数据。</p>
      </section>
    );
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">篇章规划</p>
          <h2 className="text-2xl font-black text-[#34210f]">篇章收束计划</h2>
          <p className="manuscript mt-2 text-sm text-[#5e3b1c]">{arcPlan.mode_reason}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm font-black">
          <span className={`rounded-full border px-3 py-1 ${MODE_CLASS[arcPlan.arc_mode] ?? MODE_CLASS.pressure}`}>
            叙事阶段：{labelFrom(ARC_MODE_LABELS, arcPlan.arc_mode)}
          </span>
          <span className={`rounded-full border px-3 py-1 ${budgetClass(arcPlan.expansion_budget)}`}>
            开放新线索：{labelFrom(EXPANSION_BUDGET_LABELS, arcPlan.expansion_budget)}
          </span>
        </div>
      </div>

      <div className="rounded-2xl bg-amber-50/60 p-4">
        <p className="text-sm font-black text-[#5e3b1c]">第 {arcPlan.next_chapter_number} 章建议目标</p>
        <p className="manuscript mt-2">{arcPlan.recommended_goal}</p>
      </div>

      {arcPlan.guidance.length > 0 && (
        <div className="grid gap-3 md:grid-cols-2">
          {arcPlan.guidance.map((item) => (
            <article key={item.guidance_key} className="rounded-2xl border border-amber-900/10 bg-white/45 p-3">
              <h3 className="font-black text-[#3b2511]">{item.label}</h3>
              <p className="manuscript mt-2 text-sm">{item.detail}</p>
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
                <p className="text-xs font-black tracking-[0.18em]">
                  处理方式：{labelFrom(TREATMENT_LABELS, item.treatment)} · 优先级：{labelFrom(PRIORITY_LABELS, item.priority)}
                </p>
                <h4 className="mt-2 font-black">{item.title}</h4>
                <p className="manuscript mt-2 text-sm">{item.rationale}</p>
                <p className="manuscript mt-1 text-sm">建议：{item.suggested_next_step}</p>
                {item.thread_id && <p className="mt-2 text-xs font-bold">线索来源：{labelThreadSource(item.thread_id)}</p>}
                {item.related_character_ids.length > 0 && <p className="mt-1 text-xs font-bold">关联角色：{item.related_character_ids.length} 位</p>}
                {item.related_foreshadow_ids.length > 0 && <p className="mt-1 text-xs font-bold">关联伏笔：{item.related_foreshadow_ids.length} 条</p>}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
