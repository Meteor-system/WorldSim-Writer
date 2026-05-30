import type { ApprovalReadinessCheckStatus, ApprovalReadinessResponse, ApprovalReadinessStatus } from '../api/types';

type Props = {
  readiness: ApprovalReadinessResponse;
};

const STATUS_LABELS: Record<ApprovalReadinessStatus, string> = {
  ready: '审批准备就绪',
  needs_review: '建议复核后批准',
  blocked: '暂不可批准',
};

const STATUS_CLASS: Record<ApprovalReadinessStatus, string> = {
  ready: 'border-green-300 bg-green-50 text-green-900',
  needs_review: 'border-amber-300 bg-amber-50 text-amber-950',
  blocked: 'border-red-300 bg-red-50 text-red-900',
};

const CHECK_LABELS: Record<ApprovalReadinessCheckStatus, string> = {
  pass: '通过',
  warning: '复核',
  fail: '阻塞',
};

const CHECK_CLASS: Record<ApprovalReadinessCheckStatus, string> = {
  pass: 'border-green-200 bg-green-50/70 text-green-900',
  warning: 'border-amber-300 bg-amber-50/80 text-amber-950',
  fail: 'border-red-300 bg-red-50 text-red-900',
};

export function ApprovalReadinessPanel({ readiness }: Props) {
  return (
    <section className={`book-card space-y-4 border-2 p-5 ${STATUS_CLASS[readiness.status]}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">Approval Readiness</p>
          <h2 className="text-2xl font-black text-[#34210f]">审批准备度</h2>
          <p className="manuscript mt-2">{readiness.summary}</p>
          <p className="manuscript mt-2 text-sm">
            世界版本：v{readiness.world_version.source_world_version} → v{readiness.world_version.current_world_version}
          </p>
        </div>
        <span className="rounded-full bg-white/80 px-4 py-2 text-sm font-black shadow-sm">{STATUS_LABELS[readiness.status]}</span>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {readiness.checks.map((check) => (
          <article key={check.key} className={`rounded-2xl border p-4 ${CHECK_CLASS[check.status]}`}>
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-black">{check.label}</h3>
              <span className="rounded-full bg-white/75 px-3 py-1 text-xs font-bold">{CHECK_LABELS[check.status]}</span>
            </div>
            <p className="manuscript mt-2 text-sm">{check.message}</p>
          </article>
        ))}
      </div>

      {readiness.high_risk_items.length > 0 && (
        <div className="rounded-2xl border border-red-300 bg-red-50 p-4 text-red-900">
          <h3 className="font-black">高风险项目</h3>
          <div className="mt-3 space-y-2">
            {readiness.high_risk_items.map((item, index) => (
              <p key={`${item.source}-${index}`} className="manuscript text-sm">
                [{item.source}] {item.message}
              </p>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
