import type { ChapterExecutionContext, NextChapterPrepResponse } from '../api/types';
import { buildExecutionContextFromPrep } from './chapterExecutionContext';

type Props = {
  prep: NextChapterPrepResponse | null;
  loading?: boolean;
  error?: string;
  onUseContext?: (context: ChapterExecutionContext) => void;
  onEnterStudioWithContext?: (context: ChapterExecutionContext) => void;
};

const WARNING_CLASS: Record<string, string> = {
  high: 'border-red-300 bg-red-50 text-red-950',
  medium: 'border-orange-300 bg-orange-50 text-orange-950',
  low: 'border-amber-900/10 bg-amber-50/40 text-[#3b2511]',
};

function signalLabel(signal: string): string {
  const labels: Record<string, string> = {
    character_arc_progression_hint: '角色弧线提示',
    story_arc: '故事弧线',
    urgent_foreshadow: '紧迫伏笔',
    recent_event_log: '近期事件',
    fallback: '默认推进',
  };
  return labels[signal] ?? signal;
}

export function NextChapterPrepPanel({ prep, loading, error, onUseContext, onEnterStudioWithContext }: Props) {
  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在加载下一章准备台...</p>
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

  if (!prep) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted">下一章准备台暂无建议。</p>
      </section>
    );
  }

  const context = buildExecutionContextFromPrep(prep);

  return (
    <section className="book-card space-y-4 p-5">
      <div>
        <p className="chapter-kicker">Next Chapter Prep</p>
        <h2 className="text-2xl font-black text-[#34210f]">下一章准备台</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">下一章准备台只提供写作建议，不会自动修改世界状态。</p>
      </div>

      <article className="rounded-2xl border border-amber-900/15 bg-white/45 p-4">
        <p className="chapter-kicker">第 {prep.next_chapter_number} 章建议目标</p>
        <p className="manuscript mt-2 text-lg">{prep.suggested_goal}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {prep.source_signals.map((signal) => (
            <span key={signal} className="rounded-full bg-amber-100/70 px-3 py-1 text-xs font-bold text-[#5e3b1c]">
              {signalLabel(signal)}
            </span>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {onUseContext && (
            <button className="secondary-button" onClick={() => onUseContext(context)}>
              用作下一章目标
            </button>
          )}
          {onEnterStudioWithContext && (
            <button className="primary-button" onClick={() => onEnterStudioWithContext(context)}>
              进入创作台并使用此目标
            </button>
          )}
        </div>
      </article>

      <p className="rounded-2xl bg-white/35 p-3 text-sm font-bold text-[#5e3b1c]">
        推荐 POV：{prep.recommended_pov_character_name ?? '暂无'}
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl bg-white/35 p-4">
          <h3 className="font-black text-[#3b2511]">优先角色</h3>
          {prep.priority_characters.length === 0 && <p className="ink-muted mt-2 text-sm">暂无优先角色。</p>}
          <div className="mt-3 space-y-3">
            {prep.priority_characters.map((character) => (
              <article key={character.character_id} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
                <p className="font-bold text-[#3b2511]">{character.name} · {character.role_type}</p>
                <p className="manuscript mt-1 text-sm">状态：{character.status}</p>
                <p className="manuscript mt-1 text-sm">理由：{character.reason}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white/35 p-4">
          <h3 className="font-black text-[#3b2511]">优先伏笔</h3>
          {prep.priority_foreshadows.length === 0 && <p className="ink-muted mt-2 text-sm">暂无优先伏笔。</p>}
          <div className="mt-3 space-y-3">
            {prep.priority_foreshadows.map((foreshadow) => (
              <article key={foreshadow.foreshadow_id} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
                <p className="font-bold text-[#3b2511]">{foreshadow.title} · {foreshadow.status} · urgency {foreshadow.urgency_level}</p>
                <p className="manuscript mt-1 text-sm">理由：{foreshadow.reason}</p>
              </article>
            ))}
          </div>
        </div>
      </div>

      {prep.progression_hints.length > 0 && (
        <div className="rounded-2xl bg-white/35 p-4">
          <h3 className="font-black text-[#3b2511]">推进提示</h3>
          <div className="mt-3 space-y-3">
            {prep.progression_hints.map((hint, index) => (
              <article key={`${hint.title}-${index}`} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
                <p className="font-bold text-[#3b2511]">{hint.title}</p>
                <p className="manuscript mt-1 text-sm">理由：{hint.rationale}</p>
                <p className="manuscript mt-1 text-sm">建议节拍：{hint.suggested_next_beat}</p>
              </article>
            ))}
          </div>
        </div>
      )}

      {prep.continuity_warnings.length > 0 && (
        <div className="rounded-2xl bg-white/35 p-4">
          <h3 className="font-black text-[#3b2511]">连续性提醒</h3>
          <div className="mt-3 space-y-3">
            {prep.continuity_warnings.map((warning, index) => (
              <p key={`${warning.category}-${index}`} className={`rounded-xl border p-3 text-sm font-bold ${WARNING_CLASS[warning.severity] ?? WARNING_CLASS.low}`}>
                {warning.message}
              </p>
            ))}
          </div>
        </div>
      )}

      {prep.recent_events.length > 0 && (
        <div className="rounded-2xl bg-white/35 p-4">
          <h3 className="font-black text-[#3b2511]">近期正式事件</h3>
          <div className="mt-3 space-y-2">
            {prep.recent_events.map((event) => (
              <p key={event.id} className="manuscript text-sm">
                {event.event_type} · 世界 {event.world_version_before} → {event.world_version_after}
              </p>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
