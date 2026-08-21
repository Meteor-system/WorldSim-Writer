"""Long-term memory retrieval with budget control.

Dependency-free BM25-ish scoring tuned for Chinese text + entity overlap.
Given a query (usually derived from the current chapter goal, active
foreshadows and character goals) we rank stored arc summaries and return
only the top-K within a character budget.
"""
import math
import re
from dataclasses import dataclass, field
from typing import Any

# Tuning constants (calibrated against the 20-chapter zombie stress test)
K1 = 1.2
B = 0.75
ENTITY_OVERLAP_BONUS = 3.0
TITLE_OVERLAP_BONUS = 1.5
RECENCY_DECAY_HALF_LIFE = 25.0  # chapters
PRIORITY_KEYWORD_BONUS = 1.5
DEFAULT_SUMMARY_BUDGET_CHARS = 3000
DEFAULT_SUMMARY_LIMIT = 8

_PRIORITY_KEYWORDS = {
    '真相', '解药', '计划', '感染', '秘密', '身份', '背叛', '黎明',
    '潜伏', '变异', '逃亡', '围城', '审讯', '反击', '牺牲', '救赎',
}

_TOKEN_RE = re.compile(r'[\u4e00-\u9fff]|[A-Za-z0-9_]+')


def _tokenize(text: str) -> list[str]:
    """Tokenize Chinese text into single chars and bigrams for recall."""
    if not text:
        return []
    text = text.lower()
    raw = _TOKEN_RE.findall(text)
    tokens: list[str] = []
    # Chinese: single chars + bigrams; latin/digits: full token
    chinese_buffer: list[str] = []
    for tok in raw:
        if re.match(r'[\u4e00-\u9fff]', tok):
            chinese_buffer.append(tok)
            if len(chinese_buffer) >= 2:
                tokens.append(chinese_buffer[-2] + chinese_buffer[-1])
        else:
            if chinese_buffer:
                tokens.extend(chinese_buffer[-1:])
                chinese_buffer = []
            tokens.append(tok)
    if chinese_buffer:
        tokens.extend(chinese_buffer[-1:])
    return tokens


@dataclass
class RetrievalCandidate:
    summary: Any
    score: float = 0.0
    components: dict[str, float] = field(default_factory=dict)
    covered: bool = False
    cold_chapters: int = 0


def _avg_doc_length(docs: list[list[str]]) -> float:
    return sum(len(d) for d in docs) / max(1, len(docs))


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    corpus: list[list[str]],
) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    n = len(corpus)
    avgdl = _avg_doc_length(corpus)
    doc_len = len(doc_tokens)
    score = 0.0
    tf: dict[str, int] = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1
    for token in set(query_tokens):
        if token not in tf:
            continue
        f = tf[token]
        df = sum(1 for d in corpus if token in d)
        idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
        numerator = f * (K1 + 1)
        denominator = f + K1 * (1 - B + B * doc_len / max(1, avgdl))
        score += idf * numerator / denominator
    return score


def _entity_overlap_score(
    summary: Any,
    entities: dict[str, list[str]],
) -> float:
    """Score overlap between summary text and named entities (characters,
    foreshadow titles, locations) supplied by the caller."""
    text = _summary_text(summary)
    text_tokens = set(_tokenize(text))
    score = 0.0
    for kind, names in entities.items():
        for name in names:
            name_tokens = set(_tokenize(name))
            if not name_tokens:
                continue
            overlap = len(name_tokens & text_tokens)
            if overlap:
                score += ENTITY_OVERLAP_BONUS * (overlap / max(1, len(name_tokens)))
                if kind == 'foreshadow':
                    score += TITLE_OVERLAP_BONUS
    return score


def _priority_bonus(summary: Any) -> float:
    text = _summary_text(summary)
    tokens = set(_tokenize(text))
    hits = sum(1 for kw in _PRIORITY_KEYWORDS if kw in text)
    return min(2.0, hits * PRIORITY_KEYWORD_BONUS)


def _recency_boost(chapter_start: int, current_chapter: int) -> float:
    if current_chapter <= chapter_start:
        return 1.5
    distance = current_chapter - chapter_start
    return 1.0 / math.sqrt(max(1, distance / 5.0))


def _summary_text(summary: Any) -> str:
    parts = [getattr(summary, 'summary', '') or '']
    key_facts = getattr(summary, 'key_facts', None) or []
    open_threads = getattr(summary, 'open_threads', None) or []
    if isinstance(key_facts, list):
        parts.append('；'.join(str(x) for x in key_facts))
    if isinstance(open_threads, list):
        parts.append('；'.join(str(x) for x in open_threads))
    return ' '.join(parts)


def _query_text_from_state(
    chapter_goal: str = '',
    foreshadows: list[Any] | None = None,
    characters: list[Any] | None = None,
) -> str:
    parts = [chapter_goal]
    for f in foreshadows or []:
        if getattr(f, 'status', '') in ('planted', 'advanced'):
            parts.append(f"{getattr(f, 'title', '')} {getattr(f, 'description', '')}")
    for c in characters or []:
        goals = getattr(c, 'current_goals', None) or []
        if goals:
            parts.append(f"{getattr(c, 'name', '')} {' '.join(str(g) for g in goals)}")
    return ' '.join(p for p in parts if p)


def retrieve_summaries(
    summaries: list[Any],
    query_text: str,
    current_chapter: int = 1,
    limit: int = DEFAULT_SUMMARY_LIMIT,
    budget_chars: int = DEFAULT_SUMMARY_BUDGET_CHARS,
    entities: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Rank summaries and return the retrieval plan.

    Returns:
      {
        'retrieved': [summary objects within budget/limit],
        'ranked': [{summary, score, components} ...],
        'cold': [summaries not retrieved, with cold_chapters],
        'budget_chars': int,
        'used_chars': int,
        'limit': int,
      }
    """
    if not summaries:
        return {
            'retrieved': [],
            'ranked': [],
            'cold': [],
            'budget_chars': budget_chars,
            'used_chars': 0,
            'limit': limit,
        }

    docs = [_tokenize(_summary_text(s)) for s in summaries]
    query_tokens = _tokenize(query_text)
    ranked: list[RetrievalCandidate] = []
    for i, summary in enumerate(summaries):
        bm25 = _bm25_score(query_tokens, docs[i], docs)
        entity = _entity_overlap_score(summary, entities or {})
        priority = _priority_bonus(summary)
        recency = _recency_boost(int(getattr(summary, 'chapter_start', 1) or 1), current_chapter)
        total = bm25 + entity + priority + recency
        ranked.append(
            RetrievalCandidate(
                summary=summary,
                score=total,
                components={'bm25': round(bm25, 2), 'entity': round(entity, 2),
                            'priority': round(priority, 2), 'recency': round(recency, 2)},
                cold_chapters=max(0, current_chapter - int(getattr(summary, 'chapter_end', current_chapter) or current_chapter)),
            )
        )
    ranked.sort(key=lambda c: c.score, reverse=True)

    retrieved: list[Any] = []
    used = 0
    for cand in ranked:
        if len(retrieved) >= limit:
            break
        text = _summary_text(cand.summary)
        if used + len(text) > budget_chars:
            continue
        cand.covered = True
        retrieved.append(cand.summary)
        used += len(text)

    return {
        'retrieved': retrieved,
        'ranked': [
            {
                'summary': c.summary,
                'score': round(c.score, 2),
                'components': c.components,
                'covered': c.covered,
                'cold_chapters': c.cold_chapters,
            }
            for c in ranked
        ],
        'cold': [
            {
                'summary': c.summary,
                'score': round(c.score, 2),
                'cold_chapters': c.cold_chapters,
            }
            for c in ranked if not c.covered
        ],
        'budget_chars': budget_chars,
        'used_chars': used,
        'limit': limit,
    }
