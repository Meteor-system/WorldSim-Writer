import type { WorldPulseResponse } from '../api/types';
import { labelStatus, localizeBackendCopy } from './displayLabels';

type Props = {
  pulse: WorldPulseResponse | null;
  loading?: boolean;
  error?: string;
};

const STATUS_CLASS: Record<string, string> = {
  stable: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  watch: 'border-orange-200 bg-orange-50 text-orange-950',
  urgent: 'border-red-300 bg-red-50 text-red-950',
};

const MODE_LABELS: Record<string, string> = {
  draft: '继续创作',
  repair: '修复风险',
  converge: '叙事收束',
  archive: '快照归档',
};

function toneClass(status: string): string {
  if (status === 'risk' || status === 'urgent') return 'border-red-300 bg-red-50 text-red-950';
  if (status === 'watch') return 'border-orange-300 bg-orange-50 text-orange-950';
  return 'border-amber-900/10 bg-white/45 text-[#3b2511]';
}

export function WorldPulsePanel({ pulse, loading, error }: Props) {
  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在读取世界近况...</p>
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

  if (!pulse) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted">世界近况暂无数据。</p>
      </section>
    );
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">创作近况</p>
          <h2 className="text-2xl font-black text-[#34210f]">世界近况</h2>
          <p className="manuscript mt-2 text-sm text-[#5e3b1c]">{localizeBackendCopy(pulse.headline)}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm font-black">
          <span className={`rounded-full border px-3 py-1 ${STATUS_CLASS[pulse.pulse_status] ?? STATUS_CLASS.watch}`}>
            状态：{labelStatus(pulse.pulse_status)}
          </span>
          <span className="rounded-full border border-amber-900/15 bg-amber-100/70 px-3 py-1 text-[#5e3b1c]">
            模式：{MODE_LABELS[pulse.primary_mode] ?? labelStatus(pulse.primary_mode)}
          </span>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-5">
        {pulse.indicators.map((indicator) => (
          <article key={indicator.key} className={`rounded-2xl border p-3 ${toneClass(indicator.status)}`}>
            <p className="text-sm font-black">{indicator.label}</p>
            <p className="mt-1 text-lg font-black">{localizeBackendCopy(indicator.value)}</p>
            <p className="manuscript mt-2 text-xs">{localizeBackendCopy(indicator.detail)}</p>
          </article>
        ))}
      </div>

      <div className="rounded-2xl bg-white/35 p-4">
        <h3 className="font-black text-[#3b2511]">当前优先事项</h3>
        {pulse.focus.length === 0 ? (
          <p className="ink-muted mt-2 text-sm">当前没有需要优先处理的世界运营事项。</p>
        ) : (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {pulse.focus.map((item) => (
              <article key={item.focus_key} className={`rounded-2xl border p-3 ${toneClass(item.priority)}`}>
                <p className="text-xs font-black tracking-[0.18em]">{labelStatus(item.priority)}</p>
                <h4 className="mt-2 font-black">{item.title}</h4>
                <p className="manuscript mt-2 text-sm">{localizeBackendCopy(item.detail)}</p>
                <p className="manuscript mt-1 text-sm">建议：{localizeBackendCopy(item.suggested_action)}</p>
                {item.related_thread_id && <p className="mt-2 text-xs font-bold">关联线索：{item.related_thread_id}</p>}
              </article>
            ))}
          </div>
        )}
      </div>

      {pulse.next_actions.length > 0 && (
        <div className="rounded-2xl bg-amber-50/60 p-4">
          <h3 className="font-black text-[#3b2511]">建议下一步</h3>
          <div className="mt-3 space-y-2">
            {pulse.next_actions.map((action) => (
              <p key={action.action_key} className="manuscript text-sm">
                <strong>{localizeBackendCopy(action.label)}</strong>：{localizeBackendCopy(action.detail)}
              </p>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
