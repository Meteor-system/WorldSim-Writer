"""Narrative convergence system.

Measures narrative entropy and derives arc-mode guidance so the sandbox does
not spiral out of control on long novels. Pure logic — no DB access.
"""
import re
from typing import Any

ARC_MODES = ('expansion', 'consolidation', 'pressure', 'convergence', 'payoff', 'finale')

ARC_MODE_LABELS = {
    'expansion': '扩张（可以安全地开启新线索与新人）',
    'consolidation': '整理（优先合并、轻量回收小线索，谨慎开启新线索）',
    'pressure': '加压（推进已有冲突，不建议开启新支线）',
    'convergence': '收束（本章应回收至少一条开放线索，控制熵值）',
    'payoff': '兑现（核心伏笔进入兑现阶段，集中资源回收大伏笔）',
    'finale': '终局（所有必须回收的线索应当已经关闭，只做结局定格）',
}

# Entropy weights (calibrated on the 20-chapter zombie stress test)
WEIGHT_OPEN_FORESHADOW = 2.0
WEIGHT_URGENT_FORESHADOW = 1.0
WEIGHT_ACTIVE_CHARACTER = 0.5
WEIGHT_HIDDEN_SECRET = 0.7
WEIGHT_OPEN_GOAL = 0.3
WEIGHT_OPEN_THREAD = 0.8

ENTROPY_LEVELS = (
    (15.0, 'healthy', '熵值健康，故事可控'),
    (30.0, 'elevated', '熵值升高，应开始整理合并线索'),
    (50.0, 'strained', '熵值偏高，必须进入收束节奏'),
    (float('inf'), 'critical', '熵值危险，故事面临失控风险'),
)


def _parse_window_end(window: str | None) -> int | None:
    if not window:
        return None
    m = re.match(r'第(\d+)-(\d+)章', window)
    if not m:
        return None
    return int(m.group(2))


def compute_narrative_entropy(
    characters: list[Any],
    foreshadows: list[Any],
    summaries: list[Any] | None = None,
    approved_chapter_count: int = 0,
    chapter_number: int | None = None,
) -> dict[str, Any]:
    """Compute narrative entropy and classify open threads.

    Returns a dict with:
      - entropy: float score
      - level: one of healthy/elevated/strained/critical
      - message: human-readable guidance
      - breakdown: component scores
      - open_threads: classified thread list (must/should/light/merge/defer)
    """
    breakdown = {
        'open_foreshadows': 0.0,
        'urgent_foreshadows': 0.0,
        'active_characters': 0.0,
        'hidden_secrets': 0.0,
        'open_goals': 0.0,
        'open_threads': 0.0,
    }
    open_threads: list[dict[str, Any]] = []

    # Foreshadows
    for f in foreshadows:
        status = getattr(f, 'status', 'planted')
        if status in ('planted', 'advanced'):
            breakdown['open_foreshadows'] += WEIGHT_OPEN_FORESHADOW
            urgency = int(getattr(f, 'urgency_level', 1) or 1)
            if urgency >= 4:
                breakdown['urgent_foreshadows'] += WEIGHT_URGENT_FORESHADOW
            window_end = _parse_window_end(getattr(f, 'expected_resolution_window', None))
            if urgency >= 5 or (window_end is not None and approved_chapter_count >= window_end):
                must_resolve = True
            else:
                must_resolve = False
            open_threads.append({
                'title': getattr(f, 'title', str(f.id)),
                'kind': 'foreshadow',
                'urgency': urgency,
                'window': getattr(f, 'expected_resolution_window', None),
                'classification': 'must_resolve' if must_resolve else ('should_resolve' if urgency >= 4 else 'light'),
            })

    # Characters
    for ch in characters:
        if getattr(ch, 'status', 'active') == 'archived':
            continue
        breakdown['active_characters'] += WEIGHT_ACTIVE_CHARACTER
        goals = getattr(ch, 'current_goals', []) or []
        if len(goals) > 2:
            breakdown['open_goals'] += WEIGHT_OPEN_GOAL * (len(goals) - 2)
        hidden = getattr(ch, 'hidden_traits', {}) or {}
        secrets = [v for k, v in hidden.items() if k in ('secret', 'private_agenda', 'fear') and v]
        breakdown['hidden_secrets'] += WEIGHT_HIDDEN_SECRET * len(secrets)

    # Memory summaries open threads
    for summary in summaries or []:
        threads = getattr(summary, 'open_threads', None)
        if isinstance(threads, list):
            breakdown['open_threads'] += WEIGHT_OPEN_THREAD * len(threads)

    if chapter_number is not None:
        approved_chapter_count = chapter_number

    entropy = sum(breakdown.values())
    level = 'critical'
    message = ENTROPY_LEVELS[-1][2]
    for threshold, lvl, msg in ENTROPY_LEVELS:
        if entropy <= threshold:
            level = lvl
            message = msg
            break

    return {
        'entropy': round(entropy, 1),
        'level': level,
        'message': message,
        'breakdown': breakdown,
        'open_threads': open_threads,
    }


def derive_arc_mode(
    entropy: float,
    chapter_number: int,
    total_planned_chapters: int = 200,
    final_chapter_override: bool = False,
) -> str:
    """Derive the arc-mode that should constrain the current chapter."""
    if final_chapter_override:
        return 'finale'
    if chapter_number <= 0:
        return 'expansion'

    progress = chapter_number / max(1, total_planned_chapters)

    # Early chapters: expansion (opening contract needs freedom)
    if chapter_number <= 5:
        return 'expansion'

    # Entropy-driven override takes precedence in the middle
    if entropy > 50:
        return 'convergence'
    if entropy > 30:
        return 'consolidation'

    # Progress-driven phases
    if progress < 0.15:
        return 'expansion'
    if progress <= 0.50:
        return 'pressure'
    if progress <= 0.80:
        return 'convergence'
    if progress <= 0.95:
        return 'payoff'
    return 'finale'


def compute_convergence_ratio(
    opened_threads: int,
    closed_threads: int,
    merged_threads: int = 0,
) -> float:
    """Convergence ratio = (closed + merged) / max(1, opened)."""
    numerator = closed_threads + merged_threads
    denominator = max(1, opened_threads)
    return round(numerator / denominator, 2)


def build_closure_plan(
    foreshadows: list[Any],
    characters: list[Any],
    approved_chapter_count: int = 0,
) -> list[dict[str, Any]]:
    """Build a closure plan: what should be resolved, by when, with what priority."""
    plan = []
    for f in foreshadows:
        status = getattr(f, 'status', 'planted')
        if status not in ('planted', 'advanced'):
            continue
        window_end = _parse_window_end(getattr(f, 'expected_resolution_window', None))
        urgency = int(getattr(f, 'urgency_level', 1) or 1)
        if window_end is None:
            recommended = approved_chapter_count + max(10, 30 - urgency * 3)
        else:
            recommended = window_end
        overdue = window_end is not None and approved_chapter_count >= window_end
        plan.append({
            'title': getattr(f, 'title', str(f.id)),
            'urgency': urgency,
            'window': getattr(f, 'expected_resolution_window', None),
            'recommended_chapter': recommended,
            'overdue': overdue,
            'priority': 'P0' if (overdue or urgency >= 5) else ('P1' if urgency >= 4 else 'P2'),
        })
    plan.sort(key=lambda item: (item['overdue'], item['urgency']), reverse=True)
    return plan


def build_arc_transition_report(
    chapter_range: tuple[int, int],
    foreshadows: list[Any],
    characters: list[Any],
    entropy_before: float,
    entropy_after: float,
) -> dict[str, Any]:
    """Generate an arc transition report (vol-end summary)."""
    closed = [f for f in foreshadows if getattr(f, 'status', '') == 'resolved']
    active = [f for f in foreshadows if getattr(f, 'status', '') in ('planted', 'advanced')]
    return {
        'chapter_range': f'第{chapter_range[0]}-{chapter_range[1]}章',
        'entropy_before': round(entropy_before, 1),
        'entropy_after': round(entropy_after, 1),
        'entropy_delta': round(entropy_after - entropy_before, 1),
        'closed_foreshadows': [f.title for f in closed],
        'active_foreshadows': [f.title for f in active],
        'active_character_goals': sum(len(getattr(c, 'current_goals', []) or []) for c in characters),
        'convergence_ratio': compute_convergence_ratio(
            opened_threads=len(active) + 1,
            closed_threads=len(closed),
        ),
        'guidance': '下一卷应以收束为主，优先关闭 overdue 伏笔。'
        if entropy_after > 30
        else '下一卷可适度扩张，但需控制新线索数量。',
    }
