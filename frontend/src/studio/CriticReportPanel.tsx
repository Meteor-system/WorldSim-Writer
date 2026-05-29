import type { CriticIssue, CriticReportResponse } from '../api/types';

type Props = {
  report: CriticReportResponse;
  working: boolean;
  onReviseParagraph: (paragraphIndex: number, mode: 'rewrite' | 'polish') => void;
};

const DIMENSION_LABELS: Record<string, string> = {
  pacing: '节奏',
  tension: '张力',
  character_consistency: '人物一致性',
  dialogue_quality: '对白质量',
  structure: '结构清晰度',
  world_continuity: '世界观/伏笔一致性',
  readability: '可读性',
};

const SEVERITY_WEIGHT: Record<CriticIssue['severity'], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

function dimensionLabel(dimension: string): string {
  return DIMENSION_LABELS[dimension] ?? dimension;
}

function sortedIssues(issues: CriticIssue[]): CriticIssue[] {
  return [...issues].sort((left, right) => SEVERITY_WEIGHT[left.severity] - SEVERITY_WEIGHT[right.severity]);
}

export function CriticReportPanel({ report, working, onReviseParagraph }: Props) {
  const hasHighSeverity = report.issues.some((issue) => issue.severity === 'high');

  return (
    <section className="book-card space-y-4 p-5">
      <div>
        <p className="chapter-kicker">Critic Report</p>
        <h2 className="text-2xl font-black text-[#34210f]">Critic 报告</h2>
        <p className="manuscript mt-2 text-lg font-bold">总评分：{report.overall_score}/100</p>
        <p className="manuscript mt-2">{report.summary}</p>
      </div>

      {report.is_stale && (
        <p className="paper-error">报告来自 v{report.draft_version}，当前草稿为 v{report.current_draft_version}，请重新生成。</p>
      )}

      {hasHighSeverity && (
        <div className="rounded-2xl border border-red-300 bg-red-50 p-4 text-red-900">
          <p className="font-bold">Critic 发现高风险问题，建议修订后再批准。</p>
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        {Object.entries(report.dimensions).map(([key, dimension]) => (
          <article key={key} className="rounded-2xl border border-amber-900/10 bg-white/35 p-4">
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-black text-[#3b2511]">{dimensionLabel(key)}</h3>
              <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-bold text-amber-900">{dimension.score}/100</span>
            </div>
            <p className="manuscript mt-2 text-sm">{dimension.summary}</p>
            {dimension.suggestions.slice(0, 3).map((suggestion) => (
              <p key={suggestion} className="manuscript mt-2 text-sm text-[#5e3b1c]">建议：{suggestion}</p>
            ))}
          </article>
        ))}
      </div>

      <div className="rounded-2xl bg-white/35 p-4">
        <h3 className="font-black text-[#3b2511]">问题列表</h3>
        <div className="mt-3 space-y-3">
          {sortedIssues(report.issues).map((issue, index) => (
            <article key={`${issue.dimension}-${issue.paragraph_index ?? 'all'}-${index}`} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
              <p className="text-sm font-bold text-[#3b2511]">
                [{issue.severity}] {dimensionLabel(issue.dimension)}{issue.paragraph_index !== null ? ` · 第 ${issue.paragraph_index + 1} 段` : ''}
              </p>
              <p className="manuscript mt-2 text-sm">{issue.message}</p>
              {issue.suggested_action && <p className="manuscript mt-1 text-sm text-[#5e3b1c]">建议动作：{issue.suggested_action}</p>}
              {issue.paragraph_index !== null && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className="secondary-button" disabled={working} onClick={() => onReviseParagraph(issue.paragraph_index as number, 'rewrite')}>
                    重写相关段落
                  </button>
                  <button className="secondary-button" disabled={working} onClick={() => onReviseParagraph(issue.paragraph_index as number, 'polish')}>
                    润色相关段落
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      </div>

      {report.suggestions.length > 0 && (
        <div className="rounded-2xl bg-white/35 p-4">
          <h3 className="font-black text-[#3b2511]">总体建议</h3>
          {report.suggestions.map((suggestion) => <p key={suggestion} className="manuscript mt-2 text-sm">{suggestion}</p>)}
        </div>
      )}
    </section>
  );
}
