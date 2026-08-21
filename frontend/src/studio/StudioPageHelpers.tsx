import type { BeatCard, ChapterExecutionContext, DraftResponse, ApprovalReadinessResponse } from '../api/types';

/* ── Beat helpers ── */

export function dialogueToText(beat: BeatCard): string {
    return beat.key_dialogue_hints.join('\n');
}

export function textToDialogue(value: string): string[] {
    return value
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean);
}

/* ── Label helpers ── */

export function sourceLabel(source: ChapterExecutionContext['source']): string {
    return source === 'next_chapter_prep' ? '下一章准备台' : '手动';
}

export function names(values: Array<{ name?: string; title?: string }>): string {
    return values.map((value) => value.name ?? value.title).filter(Boolean).join('、') || '无';
}

/* ── Constants ── */

export const ACTIVE_CHAPTER_RECOVERY_MESSAGE = '这个世界已有进行中的章节。请返回世界页恢复该章节，完成审阅或处理后再开始下一章。';
export const OPENING_QUALITY_VALIDATION_VERSION = 5;

/* ── Error helpers ── */

export function isActiveChapterConflict(error: unknown): boolean {
    return error instanceof Error && error.message === 'ACTIVE_CHAPTER_EXISTS';
}

export function autoDraftFailureMessage(error: unknown): string {
    if (isActiveChapterConflict(error)) return ACTIVE_CHAPTER_RECOVERY_MESSAGE;
    const recoveryMessage = '第一章草稿暂未生成。已创建的世界和当前创作进度都已保留，可以直接重试。';
    const detail = error instanceof Error ? error.message.trim() : '';
    if (!detail || /^[A-Z][A-Z0-9_]+$/.test(detail)) return recoveryMessage;
    return `${recoveryMessage} 原因：${detail}`;
}

export function apiErrorStatus(err: unknown): number | undefined {
    return err instanceof Error && 'status' in err ? (err as Error & { status?: number }).status : undefined;
}

/* ── Opening quality helpers ── */

export function openingQualityStatus(status?: string, passed?: boolean, stale = false): string {
    if (stale) return '已过期';
    if (typeof passed === 'boolean') return passed ? '通过' : '需修订';
    if (status === 'pass' || status === 'passed' || status === 'ok') return '通过';
    if (status === 'warning' || status === 'needs_review') return '需复核';
    if (status === 'fail' || status === 'failed' || status === 'blocked') return '需修订';
    return status ?? '未标注';
}

export function openingQualityIsCurrent(draft: DraftResponse | null): boolean {
    const report = draft?.quality_report;
    if (!draft || report?.profile !== 'opening_chapter') return true;
    return report.status === 'pass'
        && report.evaluated_draft_version === draft.draft_version
        && report.validation_version === OPENING_QUALITY_VALIDATION_VERSION;
}

/* ── Draft helpers ── */

export function paragraphList(content: string): string[] {
    return content.split('\n\n').map((paragraph) => paragraph.trim()).filter(Boolean);
}

export function resolveDraftVersion(nextDraft: DraftResponse): number {
    const draftVersion = Number(nextDraft.draft_version);
    if (Number.isFinite(draftVersion) && draftVersion > 0) return draftVersion;
    return 1;
}

export function normalizeDraft(nextDraft: DraftResponse): DraftResponse {
    return { ...nextDraft, draft_version: resolveDraftVersion(nextDraft) };
}

/* ── Selection helpers ── */

export function previewIndex(change: { change_index?: number }, fallback: number): number {
    return typeof change.change_index === 'number' ? change.change_index : fallback;
}

export function toggleIndex(values: number[], index: number): number[] {
    return values.includes(index) ? values.filter((value) => value !== index) : [...values, index].sort((a, b) => a - b);
}

/* ── Consistency helpers ── */

export function consistencyLabel(summary: { blocking_count: number; warning_count: number }): string {
    if (summary.blocking_count > 0) return '有阻塞';
    if (summary.warning_count > 0) return '有提醒';
    return '通过';
}

/* ── Approval readiness helper ── */

export function isApprovalReadinessBlocked(readiness: ApprovalReadinessResponse | null): boolean {
    if (!readiness) return true;
    return readiness.status === 'blocked';
}

/* ── Sub-components ── */

export function ExecutionContextSummary({ context, frozen }: { context?: ChapterExecutionContext | null; frozen?: boolean }) {
    if (!context) {
        return (
            <div className="book-card p-5">
                <h2 className="font-black text-[#3b2511]">本章设定（本章要写什么）</h2>
                <p className="mt-3 ink-muted">本章暂无来自下一章准备台的设定。创建章节时会根据当前目标生成手动设定快照。</p>
            </div>
        );
    }
    return (
        <div className="book-card p-5">
            <h2 className="font-black text-[#3b2511]">本章设定（本章要写什么）</h2>
            {frozen && <p className="mt-2 text-sm font-bold text-[#5e3b1c]">已冻结本章设定：{context.source} · v{context.source_world_version}</p>}
            <p className="mt-3 ink-muted">来源：{sourceLabel(context.source)}</p>
            <p className="mt-2 ink-muted">源世界版本：v{context.source_world_version}</p>
            <p className="mt-2 ink-muted">建议章节：第 {context.next_chapter_number ?? '?'} 章</p>
            <p className="mt-2 ink-muted">推荐 POV：{context.recommended_pov.name ?? '暂无'}</p>
            <p className="mt-2 ink-muted">优先角色：{names(context.priority_characters)}</p>
            <p className="mt-2 ink-muted">优先伏笔：{names(context.priority_foreshadows)}</p>
            <p className="mt-2 ink-muted">推进提示：{context.progression_hints.length} 条</p>
            <p className="mt-2 ink-muted">连续性提醒：{context.continuity_warnings.length} 条</p>
            {context.continuity_warnings.length > 0 && (
                <ul className="mt-3 space-y-2 rounded-xl bg-amber-50/70 p-3 text-sm text-[#5e3b1c]" aria-label="连续性提醒列表">
                    {context.continuity_warnings.map((warning, index) => (
                        <li key={`${warning.category}-${index}`}>{warning.message}</li>
                    ))}
                </ul>
            )}
            {context.style_handbook_reference && (
                <p className="mt-2 ink-muted">写作风格参考：{context.style_handbook_reference.source_title}（仅抽象风格维度，不写入正史）</p>
            )}
        </div>
    );
}

export function ExecutionContextSnapshot({ context }: { context?: ChapterExecutionContext | null }) {
    if (!context) return null;
    return (
        <section className="space-y-3 rounded-2xl bg-white/35 p-4">
            <h3 className="font-black text-[#3b2511]">本章设定快照</h3>
            <p className="manuscript text-sm">来源：{sourceLabel(context.source)} · v{context.source_world_version}</p>
            <p className="manuscript text-sm">目标：{context.goal}</p>
            <p className="manuscript text-sm">推荐 POV：{context.recommended_pov.name ?? '暂无'}</p>
            <p className="manuscript text-sm">优先角色：{names(context.priority_characters)}</p>
            <p className="manuscript text-sm">优先伏笔：{names(context.priority_foreshadows)}</p>
            {context.progression_hints.map((hint) => (
                <p key={hint.title} className="manuscript text-sm">推进提示：{hint.title}</p>
            ))}
            {context.continuity_warnings.map((warning, index) => (
                <p key={`${warning.category}-${index}`} className="manuscript text-sm">连续性提醒：{warning.message}</p>
            ))}
            {context.style_handbook_reference && (
                <div className="rounded-xl bg-amber-50/60 p-3" data-testid="execution-style-handbook">
                    <p className="manuscript text-sm font-bold">写作风格参考：{context.style_handbook_reference.source_title}</p>
                    <p className="manuscript text-xs ink-muted">仅参考抽象风格维度（节奏/语言密度/对白比例等），不写入正史，禁止照搬原文。</p>
                </div>
            )}
        </section>
    );
}

export function OpeningQualityPanel({ draft }: { draft: DraftResponse | null }) {
    const report = draft?.quality_report;
    const checks = report?.checks ?? report?.opening_chapter?.checks ?? [];
    const advisories = report?.advisories ?? [];
    const currentDraftVersion = draft?.draft_version;
    const validationVersionOutdated = report?.profile === 'opening_chapter'
        && report.validation_version !== OPENING_QUALITY_VALIDATION_VERSION;
    const stale = Boolean(
        report?.profile === 'opening_chapter'
        && (report.status === 'stale' || report.evaluated_draft_version !== currentDraftVersion || validationVersionOutdated),
    );

    return (
        <section className="studio-quality-panel" aria-labelledby="opening-quality-title">
            <div className="studio-panel-heading">
                <p className="chapter-kicker">Opening Quality</p>
                <h2 id="opening-quality-title" className="text-2xl font-black text-[#34210f]">首章质量</h2>
            </div>
            {!report ? (
                <p className="manuscript text-sm">尚未评估首章质量。生成或载入草稿后，质量报告会在此显示。</p>
            ) : (
                <>
                    <p className="manuscript text-sm">状态：{openingQualityStatus(report.status, undefined, stale)}{report.profile ? ` · ${report.profile}` : ''}</p>
                    {stale && (
                        <div className="paper-error mt-3">
                            <p className="font-bold">{validationVersionOutdated ? '验证规则已更新，需重新评估' : '当前草稿未验证'}</p>
                            {validationVersionOutdated ? (
                                <p className="mt-1 text-sm">当前审批要求验证规则 v{OPENING_QUALITY_VALIDATION_VERSION}；该报告的规则版本缺失或不匹配。</p>
                            ) : typeof report.evaluated_draft_version === 'number' && typeof currentDraftVersion === 'number' && (
                                <p className="mt-1 text-sm">基于 v{report.evaluated_draft_version}，不适用于当前 v{currentDraftVersion}</p>
                            )}
                        </div>
                    )}
                    {(typeof report.character_count === 'number' || typeof report.paragraph_count === 'number') && (
                        <p className="manuscript text-sm">字数：{report.character_count ?? '未提供'} · 段落：{report.paragraph_count ?? '未提供'}</p>
                    )}
                    {typeof report.evaluated_draft_version === 'number' && <p className="manuscript text-sm">评估草稿：v{report.evaluated_draft_version}</p>}
                    {checks.length > 0 ? (
                        <ul className="studio-quality-checks">
                            {checks.map((check, index) => (
                                <li key={`${check.check ?? check.label}-${index}`}>
                                    <div className="flex items-baseline justify-between gap-3">
                                        <strong>{check.label}</strong>
                                        <span className="text-sm font-bold text-[#80501f]">{openingQualityStatus(check.status, check.passed, stale)}</span>
                                    </div>
                                    {check.message && <p className="manuscript mt-1 text-sm">{check.message}</p>}
                                    {(typeof check.paragraph_index === 'number' || check.quote) && <p className="manuscript mt-1 text-xs ink-muted">{typeof check.paragraph_index === 'number' ? `第 ${check.paragraph_index + 1} 段` : ''}{typeof check.paragraph_index === 'number' && check.quote ? ' · ' : ''}{check.quote ? `证据：${check.quote}` : ''}</p>}
                                    {typeof check.corrected_index === 'number' && <p className="manuscript mt-1 text-xs ink-muted">自动校正：第 {check.corrected_index + 1} 段</p>}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="manuscript text-sm">报告未包含可展示的检查项。</p>
                    )}
                    {advisories.length > 0 && (
                        <section className="mt-4 rounded-xl bg-amber-50/60 p-3" aria-labelledby="opening-quality-advisories-title">
                            <h3 id="opening-quality-advisories-title" className="font-black text-[#3b2511]">非阻断建议</h3>
                            <p className="manuscript mt-1 text-xs ink-muted">以下提示仅供修订参考，不影响首章质量硬门禁或审批。</p>
                            <ul className="mt-3 space-y-3">
                                {advisories.map((advisory, index) => (
                                    <li key={`${advisory.check}-${index}`} className="rounded-lg bg-white/50 p-3">
                                        <div className="flex items-baseline justify-between gap-3">
                                            <strong>{advisory.label}</strong>
                                            <span className="text-sm font-bold text-[#80501f]">状态：{advisory.state}</span>
                                        </div>
                                        {advisory.message && <p className="manuscript mt-1 text-sm">{advisory.message}</p>}
                                        {advisory.unglossed_terms && advisory.unglossed_terms.length > 0 && <p className="manuscript mt-1 text-xs ink-muted">术语样本：{advisory.unglossed_terms.join('、')}</p>}
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}
                </>
            )}
        </section>
    );
}
