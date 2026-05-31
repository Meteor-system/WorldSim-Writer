import type { OpenThreadsResponse } from '../api/types';

type Props = {
  openThreads: OpenThreadsResponse | null;
  loading?: boolean;
  error?: string;
};

const PRIORITY_LABELS: Record<string, string> = {
  must_close: '必须收束',
  should_advance: '建议推进',
  can_delay: '可延后',
  can_leave_open: '可留白',
};

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function priorityClass(priority: string): string {
  if (priority === 'must_close') return 'border-red-300 bg-red-50 text-red-950';
  if (priority === 'should_advance') return 'border-orange-300 bg-orange-50 text-orange-950';
  return 'border-amber-900/10 bg-amber-50/40 text-[#3b2511]';
}

export function OpenThreadsPanel({ openThreads, loading, error }: Props) {
  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在加载开放线索...</p>
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

  if (!openThreads) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted">开放线索看板暂无数据。</p>
      </section>
    );
  }

  const summary = openThreads.summary;

  return (
    <section className="book-card space-y-5 p-5">
      <div>
        <p className="chapter-kicker">Story Convergence</p>
        <h2 className="text-2xl font-black text-[#34210f]">Open Threads Board</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">整理伏笔、角色目标、弧线提示与健康风险，帮助故事从扩张走向收束。</p>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <article className="rounded-2xl bg-amber-50/60 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">开放线索：{summary.total_open_threads}</p>
          <p className="ink-muted mt-1 text-xs">正式写作前需要看见的叙事债务。</p>
        </article>
        <article className="rounded-2xl bg-red-50 p-3">
          <p className="text-sm font-bold text-red-950">必须收束：{summary.must_close_count}</p>
          <p className="ink-muted mt-1 text-xs">建议先处理，再继续扩张。</p>
        </article>
        <article className="rounded-2xl bg-white/50 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">收束比：{percent(summary.convergence_ratio)}</p>
          <p className="ink-muted mt-1 text-xs">已关闭伏笔占全部伏笔的比例。</p>
        </article>
        <article className="rounded-2xl bg-white/50 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">叙事熵：{summary.narrative_entropy_level}</p>
          <p className="ink-muted mt-1 text-xs">开放线索压力的粗略等级。</p>
        </article>
      </div>

      {openThreads.suggested_next_actions.length > 0 && (
        <div className="rounded-2xl bg-amber-50/60 p-4">
          <h3 className="font-black text-[#3b2511]">建议下一步</h3>
          <div className="mt-3 space-y-2">
            {openThreads.suggested_next_actions.map((action, index) => (
              <p key={`${String(action.action_key ?? index)}`} className="manuscript text-sm">
                <strong>{String(action.label)}</strong>：{String(action.detail)}
              </p>
            ))}
          </div>
        </div>
      )}

      {openThreads.threads.length === 0 ? (
        <p className="ink-muted">当前没有需要优先处理的开放线索。</p>
      ) : (
        <div className="space-y-3">
          {openThreads.threads.map((thread) => (
            <article key={thread.thread_id} className={`rounded-2xl border p-4 ${priorityClass(thread.priority)}`}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.18em]">[{thread.priority}] {thread.thread_type} · {thread.pressure_level}</p>
                  <h3 className="mt-2 text-lg font-black">{thread.title}</h3>
                </div>
                <span className="rounded-full bg-white/60 px-3 py-1 text-xs font-bold">{PRIORITY_LABELS[thread.priority] ?? thread.priority}</span>
              </div>
              <p className="manuscript mt-3 text-sm">{thread.summary}</p>
              <p className="manuscript mt-2 text-sm">建议：{thread.suggested_action}</p>
              {thread.can_seed_next_chapter_goal && <p className="mt-2 text-xs font-black text-[#5e3b1c]">可作为下一章目标种子</p>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
