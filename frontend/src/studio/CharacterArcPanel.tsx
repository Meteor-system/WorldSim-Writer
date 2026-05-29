import type { CharacterArcReportResponse, ContinuityRisk, ProgressionPriority } from '../api/types';

type Props = {
  report: CharacterArcReportResponse;
  working: boolean;
  onUseHintAsGoal?: (goal: string) => void;
};

const RISK_LABELS: Record<ContinuityRisk, string> = {
  none: '无风险',
  low: '低风险',
  medium: '中风险',
  high: '高风险',
};

const PRIORITY_LABELS: Record<ProgressionPriority, string> = {
  low: '低优先级',
  medium: '中优先级',
  high: '高优先级',
};

const PRIORITY_WEIGHT: Record<ProgressionPriority, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

function isRisky(risk: ContinuityRisk): boolean {
  return risk === 'high' || risk === 'medium';
}

function riskClass(risk: ContinuityRisk): string {
  if (risk === 'high') return 'border-red-300 bg-red-50 text-red-900';
  if (risk === 'medium') return 'border-orange-300 bg-orange-50 text-orange-950';
  return 'border-amber-900/10 bg-amber-50/35 text-[#3b2511]';
}

export function CharacterArcPanel({ report, working, onUseHintAsGoal }: Props) {
  const sortedHints = [...report.progression_hints].sort((left, right) => PRIORITY_WEIGHT[left.priority] - PRIORITY_WEIGHT[right.priority]);

  return (
    <section className="book-card space-y-4 p-5">
      <div>
        <p className="chapter-kicker">Character Arc Report</p>
        <h2 className="text-2xl font-black text-[#34210f]">角色弧线报告</h2>
        <p className="manuscript mt-2">{report.summary}</p>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">这是审核建议，不会自动提交世界状态；只有批准章节才会提交 approval preview 中列出的变化。</p>
      </div>

      {report.is_stale && (
        <p className="paper-error">报告来自 v{report.draft_version}，当前草稿为 v{report.current_draft_version}，请重新生成。</p>
      )}

      <div className="space-y-3 rounded-2xl bg-white/35 p-4">
        <h3 className="font-black text-[#3b2511]">角色弧线</h3>
        {report.character_arcs.map((arc) => (
          <article key={arc.character_id} className={`rounded-xl border p-4 ${riskClass(arc.continuity_risk)}`}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h4 className="font-black">{arc.name} · {arc.role_type ?? 'unknown'}</h4>
                <p className="text-sm font-semibold">出现：{arc.presence_level} · 阶段：{arc.arc_stage}</p>
              </div>
              <span className="rounded-full bg-white/70 px-3 py-1 text-sm font-bold">{RISK_LABELS[arc.continuity_risk]}</span>
            </div>
            <p className="manuscript mt-2 text-sm">当前状态：{arc.current_status ?? '未设置'}</p>
            {arc.current_goals.length > 0 && <p className="manuscript mt-1 text-sm">当前目标：{arc.current_goals.join('；')}</p>}
            <p className="manuscript mt-2 text-sm">本章功能：{arc.chapter_function}</p>
            <p className="manuscript mt-1 text-sm">观察到的变化：{arc.observed_shift}</p>
            {arc.proposed_state_change && <p className="manuscript mt-1 text-sm">拟提交变化：{JSON.stringify(arc.proposed_state_change)}</p>}
            {isRisky(arc.continuity_risk) && arc.risk_reason && (
              <p className="mt-2 text-sm font-bold">连续性{RISK_LABELS[arc.continuity_risk]}：{arc.risk_reason}</p>
            )}
            {arc.suggested_revision && <p className="manuscript mt-2 text-sm">修订建议：{arc.suggested_revision}</p>}
            {arc.next_chapter_setup && <p className="manuscript mt-1 text-sm">下一章铺垫：{arc.next_chapter_setup}</p>}
          </article>
        ))}
      </div>

      {report.relationship_notes.length > 0 && (
        <div className="space-y-3 rounded-2xl bg-white/35 p-4">
          <h3 className="font-black text-[#3b2511]">关系推进</h3>
          {report.relationship_notes.map((note, index) => (
            <article key={`${note.source_character_id}-${note.target_character_id}-${index}`} className={`rounded-xl border p-3 ${riskClass(note.risk_level)}`}>
              <p className="font-bold">{note.source_name} → {note.target_name} · {note.relation_type}</p>
              <p className="manuscript mt-1 text-sm">本章变化：{note.chapter_shift}</p>
              <p className="manuscript mt-1 text-sm">推进提示：{note.progression_hint}</p>
              {note.risk_reason && <p className="manuscript mt-1 text-sm">风险：{note.risk_reason}</p>}
            </article>
          ))}
        </div>
      )}

      {sortedHints.length > 0 && (
        <div className="space-y-3 rounded-2xl bg-white/35 p-4">
          <h3 className="font-black text-[#3b2511]">下一章推进提示</h3>
          {sortedHints.map((hint, index) => (
            <article key={`${hint.hint_type}-${hint.title}-${index}`} className={hint.priority === 'high' ? 'rounded-xl border border-red-200 bg-red-50 p-3 text-red-950' : 'rounded-xl border border-amber-900/10 bg-amber-50/35 p-3'}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <h4 className="font-black">{hint.title}</h4>
                <span className="rounded-full bg-white/70 px-3 py-1 text-sm font-bold">{PRIORITY_LABELS[hint.priority]}</span>
              </div>
              <p className="manuscript mt-2 text-sm">理由：{hint.rationale}</p>
              <p className="manuscript mt-1 text-sm">建议节拍：{hint.suggested_next_beat}</p>
              {hint.can_seed_next_chapter_goal && onUseHintAsGoal && (
                <button className="secondary-button mt-3" disabled={working} onClick={() => onUseHintAsGoal(hint.suggested_next_beat)}>
                  用作下一章目标
                </button>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
