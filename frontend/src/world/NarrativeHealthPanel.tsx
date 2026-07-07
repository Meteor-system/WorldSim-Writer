import type { NarrativeHealthResponse } from '../api/types';
import { labelStatus, localizeBackendCopy } from './displayLabels';

type Props = {
  health: NarrativeHealthResponse | null;
  loading?: boolean;
  error?: string;
};

const STATUS_LABELS: Record<NarrativeHealthResponse['status'], string> = {
  healthy: '健康',
  watch: '观察',
  at_risk: '高风险',
};

const STATUS_CLASS: Record<NarrativeHealthResponse['status'], string> = {
  healthy: 'bg-emerald-50 text-emerald-900 border-emerald-200',
  watch: 'bg-orange-50 text-orange-950 border-orange-200',
  at_risk: 'bg-red-50 text-red-950 border-red-200',
};

function riskClass(severity: string): string {
  if (severity === 'high') return 'border-red-300 bg-red-50 text-red-950';
  if (severity === 'medium') return 'border-orange-300 bg-orange-50 text-orange-950';
  return 'border-amber-900/10 bg-amber-50/35 text-[#3b2511]';
}

export function NarrativeHealthPanel({ health, loading, error }: Props) {
  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在加载叙事健康度...</p>
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

  if (!health) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted">叙事健康度暂无数据。</p>
      </section>
    );
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">风险看板</p>
          <h2 className="text-2xl font-black text-[#34210f]">叙事健康度</h2>
          <p className="manuscript mt-2 text-sm text-[#5e3b1c]">汇总 Critic、角色弧线、伏笔压力与正式事件信号，只提供建议，不修改世界状态。</p>
        </div>
        <div className={`rounded-2xl border px-4 py-3 text-right ${STATUS_CLASS[health.status]}`}>
          <p className="text-3xl font-black">{health.health_score}/100</p>
          <p className="text-sm font-bold">{STATUS_LABELS[health.status]}</p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {health.metrics.map((metric) => (
          <article key={metric.key} className="rounded-2xl border border-amber-900/10 bg-white/35 p-4">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-black text-[#3b2511]">{metric.label}</h3>
              <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-bold text-[#5e3b1c]">{metric.value}</span>
            </div>
            <p className="manuscript mt-2 text-sm">{localizeBackendCopy(metric.detail)}</p>
          </article>
        ))}
      </div>

      <div className="rounded-2xl bg-white/35 p-4">
        <h3 className="font-black text-[#3b2511]">叙事风险</h3>
        {health.risks.length === 0 ? (
          <p className="ink-muted mt-2 text-sm">当前没有高风险叙事问题。</p>
        ) : (
          <div className="mt-3 space-y-3">
            {health.risks.map((risk, index) => (
              <article key={`${risk.source}-${risk.object_id ?? index}`} className={`rounded-xl border p-3 ${riskClass(risk.severity)}`}>
                <p className="text-sm font-black">[{labelStatus(risk.severity)}] {labelStatus(risk.source)}{risk.object_title ? ` · ${risk.object_title}` : ''}</p>
                <p className="manuscript mt-2 text-sm">{localizeBackendCopy(risk.message)}</p>
                <p className="manuscript mt-1 text-sm">建议：{localizeBackendCopy(risk.suggested_action)}</p>
              </article>
            ))}
          </div>
        )}
      </div>

      {health.suggested_actions.length > 0 && (
        <div className="rounded-2xl bg-amber-50/60 p-4">
          <h3 className="font-black text-[#3b2511]">建议下一步</h3>
          <div className="mt-3 space-y-2">
            {health.suggested_actions.map((action) => (
              <p key={action.action_key} className="manuscript text-sm"><strong>{localizeBackendCopy(action.label)}</strong>：{localizeBackendCopy(action.detail)}</p>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
