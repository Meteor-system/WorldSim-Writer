import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.event.models import EventLog
from app.import_node.models import ImportBatch, ImportCandidateAsset
from app.import_node.schemas import (
    ImportBatchListResponse,
    ImportBatchResponse,
    ImportBatchWithAssetsResponse,
    ImportCandidateAssetPreview,
    ImportCandidateAssetResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportConflict,
    ImportMaterialReferenceResponse,
    ImportPreviewRequest,
    ImportPreviewResponse,
    StyleHandbookDimension,
    StyleHandbookDraft,
    StyleHandbookPreviewRequest,
    StyleHandbookPreviewResponse,
)
from app.narrative.models import Chapter
from app.world.service import require_owned_world

ASSET_POOLS = ('inspiration', 'character', 'canon')
ROLE_KEYWORDS = ('主角', '反派', '密探', '剑修', '城主', '弟子', '长老', '掌门', '商人', '将军')
CANON_KEYWORDS = ('所有', '禁止', '必须', '世界规则', '不可违背', '真理', '规则')
MARKDOWN_PREFIX_RE = re.compile(r'^(#{1,6}\s*|[-*+]\s+|>\s*|`{3,}\s*)')
LEADING_LABEL_RE = re.compile(r'^(角色|人物|设定|规则|世界观|canon|真理|灵感|脑洞|片段|桥段|对白)\s*[:：\-]\s*', re.IGNORECASE)


def _excerpt(text: str, size: int = 500) -> str:
    compact = ' '.join(text.split())
    return compact[:size]


def _clean_content(content: str) -> str:
    normalized = content.replace('\r\n', '\n').replace('\r', '\n')
    cleaned_lines: list[str] = []
    previous_blank = False
    for raw_line in normalized.split('\n'):
        line = MARKDOWN_PREFIX_RE.sub('', raw_line.strip()).strip()
        if not line:
            if not previous_blank:
                cleaned_lines.append('')
            previous_blank = True
            continue
        cleaned_lines.append(line)
        previous_blank = False
    return '\n'.join(cleaned_lines).strip()


def _meaningful_lines(cleaned_content: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for index, line in enumerate(cleaned_content.split('\n'), start=1):
        stripped = line.strip()
        if len(stripped) >= 3:
            lines.append((index, stripped))
    return lines


def _title_summary_from_line(line: str, pool: str) -> tuple[str, str]:
    without_label = LEADING_LABEL_RE.sub('', line).strip()
    if '：' in without_label:
        title, summary = without_label.split('：', 1)
    elif ':' in without_label:
        title, summary = without_label.split(':', 1)
    else:
        title, summary = without_label[:28], without_label
    title = title.strip(' #*-：:') or {'canon': 'canon 候选', 'character': '角色候选', 'inspiration': '灵感候选'}[pool]
    summary = summary.strip() or without_label
    return title[:120], summary[:300]


def _classify_line(line: str) -> str:
    if re.match(r'^(设定|规则|世界观|canon|真理)\s*[:：\-]', line, re.IGNORECASE) or any(keyword in line for keyword in CANON_KEYWORDS):
        return 'canon'
    if re.match(r'^(角色|人物)\s*[:：\-]', line) or ('：' in line and any(keyword in line for keyword in ROLE_KEYWORDS)):
        return 'character'
    return 'inspiration'


def _asset_counts(assets: list[ImportCandidateAssetPreview]) -> dict[str, int]:
    return {pool: sum(1 for asset in assets if asset.asset_pool == pool) for pool in ASSET_POOLS}


def _notable_terms(text: str) -> set[str]:
    terms = {term for term in re.findall(r'[一-鿿]{2,8}', text) if len(term) >= 2}
    stopwords = {'所有', '必须', '角色', '设定', '规则', '灵感', '世界', '人物'}
    return {term for term in terms if term not in stopwords}


def _detect_conflicts(db: Session, world_id: int, line: str, asset: ImportCandidateAssetPreview, truth_canon: str) -> list[ImportConflict]:
    conflicts: list[ImportConflict] = []
    canon_terms = _notable_terms(truth_canon)
    line_terms = _notable_terms(line)
    overlap = sorted((canon_terms & line_terms), key=len, reverse=True)
    if overlap:
        conflicts.append(
            ImportConflict(
                severity='warning',
                category='canon_overlap',
                message=f'导入内容提到已有 canon 关键词：{overlap[0]}',
                matched_text=overlap[0],
            )
        )

    if asset.asset_pool == 'character':
        existing = db.scalar(select(Character).where(Character.world_id == world_id).where(Character.name == asset.title))
        if existing is not None:
            conflicts.append(
                ImportConflict(
                    severity='warning',
                    category='character_duplicate',
                    message=f'角色池中已存在同名角色：{asset.title}',
                    matched_text=asset.title,
                    details={'character_id': existing.id},
                )
            )

    approved_chapters = list(db.scalars(select(Chapter).where(Chapter.world_id == world_id).where(Chapter.status == 'approved').order_by(Chapter.id).limit(20)))
    for chapter in approved_chapters:
        if chapter.title and chapter.title in line:
            conflicts.append(
                ImportConflict(
                    severity='warning',
                    category='approved_chapter_overlap',
                    message=f'导入内容提到已通过章节：{chapter.title}',
                    matched_text=chapter.title,
                    details={'chapter_id': chapter.id},
                )
            )
            break
    return conflicts


def _build_preview(db: Session, world_id: int, data: ImportPreviewRequest) -> ImportPreviewResponse:
    from app.world.models import World

    world = db.get(World, world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    cleaned = _clean_content(data.content)
    assets: list[ImportCandidateAssetPreview] = []
    conflicts: list[ImportConflict] = []
    seen: set[tuple[str, str, str]] = set()

    for line_number, line in _meaningful_lines(cleaned):
        pool = _classify_line(line)
        title, summary = _title_summary_from_line(line, pool)
        key = (pool, title, summary)
        if key in seen:
            continue
        seen.add(key)
        asset = ImportCandidateAssetPreview(
            asset_pool=pool,
            title=title,
            summary=summary,
            raw_text=line,
            metadata={'source_line': line_number, 'confidence': 'medium'},
        )
        assets.append(asset)
        conflicts.extend(_detect_conflicts(db, world.id, line, asset, world.truth_canon))

    return ImportPreviewResponse(
        world_id=world.id,
        source_type=data.source_type,
        source_title=data.source_title,
        cleaned_excerpt=_excerpt(cleaned),
        assets=assets,
        conflicts=conflicts,
        asset_counts=_asset_counts(assets),
    )


def preview_import(db: Session, user: User, world_id: int, data: ImportPreviewRequest) -> ImportPreviewResponse:
    world = require_owned_world(db, user, world_id)
    return _build_preview(db, world.id, data)


def _lines_with_punctuation(cleaned: str) -> list[str]:
    lines = [line.strip() for line in re.split(r'[。！？!?\n]+', cleaned) if line.strip()]
    return lines or [cleaned]


def _style_excerpt(text: str, size: int = 80) -> str:
    compact = ' '.join(text.split())
    if len(compact) <= size:
        return compact
    return f'{compact[:size].rstrip()}…'


def _dimension(label: str, value: str, evidence: str | None = None) -> StyleHandbookDimension:
    return StyleHandbookDimension(label=label, value=value, evidence=_style_excerpt(evidence) if evidence else None)


def _ratio_label(ratio: float, low: str, medium: str, high: str) -> str:
    if ratio < 0.18:
        return low
    if ratio < 0.38:
        return medium
    return high


def _build_style_handbook(cleaned: str) -> StyleHandbookDraft:
    lines = _lines_with_punctuation(cleaned)
    total_chars = max(1, sum(len(line) for line in lines))
    avg_sentence_length = total_chars / max(1, len(lines))
    dialogue_lines = [line for line in lines if '“' in line or '”' in line or re.search(r'(^|[，。！？!?])\s*[^，。！？!?]{1,16}[说问道喊答]', line)]
    question_or_reveal_lines = [line for line in lines if any(token in line for token in ('？', '?', '秘密', '真相', '发现', '不知道', '为何', '为什么'))]
    relationship_lines = [line for line in lines if any(token in line for token in ('他', '她', '父', '母', '兄', '姐', '敌', '友', '盟', '背叛', '承诺', '亏欠'))]
    foreshadow_lines = [line for line in lines if any(token in line for token in ('伏笔', '线索', '预兆', '痕迹', '记号', '谜', '旧', '再次', '终有一天'))]
    scene_lines = [line for line in lines if any(token in line for token in ('门', '城', '街', '雨', '夜', '房间', '战场', '大厅', '窗', '光'))]

    density_value = '高密度描写，句子承载较多意象或设定信息。' if avg_sentence_length >= 34 else '中等语言密度，叙述与信息交代相对均衡。' if avg_sentence_length >= 18 else '短句推进明显，适合快节奏情节。'
    dialogue_value = _ratio_label(len(dialogue_lines) / max(1, len(lines)), '对白占比较低，主要依赖叙述推进。', '对白与叙述交替，用对话释放人物关系和信息。', '对白占比较高，适合用人物交锋推动场景。')
    suspense_value = '悬念显性较强，适合每节保留一个待解问题。' if question_or_reveal_lines else '悬念较隐性，可在章节尾部补充明确问题或反转钩子。'
    relationship_value = '人物关系张力明显，适合围绕承诺、亏欠、敌友转换推进。' if relationship_lines else '人物关系信息较少，后续生成应主动补足角色目标冲突。'
    foreshadow_value = '已有线索/预兆表达，可抽象为“先给异常，再延迟解释”的伏笔模式。' if foreshadow_lines else '伏笔模式不突出，建议后续按章节目标添加可追踪悬念。'
    scene_value = '场景意象可见，适合用地点、天气或物件带动段落转场。' if scene_lines else '场景推进偏概述，生成章节时应补足可视化地点和动作。'
    pacing_value = '快节奏推进，适合短段落切换冲突。' if avg_sentence_length < 18 else '中速推进，适合“铺垫-冲突-钩子”的章节结构。' if avg_sentence_length < 34 else '慢热铺陈，适合先累积氛围和设定压力再爆发。'

    return StyleHandbookDraft(
        narrative_pacing=_dimension('叙事节奏', pacing_value, lines[0]),
        language_density=_dimension('语言密度', density_value, max(lines, key=len)),
        dialogue_ratio=_dimension('对白比例', dialogue_value, dialogue_lines[0] if dialogue_lines else None),
        scene_progression=_dimension('场景推进', scene_value, scene_lines[0] if scene_lines else lines[0]),
        suspense_structure=_dimension('悬念结构', suspense_value, question_or_reveal_lines[0] if question_or_reveal_lines else None),
        relationship_tension=_dimension('人物关系张力', relationship_value, relationship_lines[0] if relationship_lines else None),
        foreshadowing_pattern=_dimension('伏笔埋设/回收方式', foreshadow_value, foreshadow_lines[0] if foreshadow_lines else None),
        do_guidelines=[
            '保留抽象节奏、信息密度和场景推进方式，用于原创章节生成。',
            '把参考文本中的表达习惯转为可调参数，而不是复制具体句子。',
            '在 Studio 中继续区分写作参考与拟写入世界变化。',
        ],
        avoid_guidelines=[
            '不要复用原文句子、人物名、专有设定或标志性桥段。',
            '不要把风格手册当作正式 canon 或世界事实。',
            '不要承诺完全模仿某位作者或某部未授权作品。',
        ],
        originality_guidelines=[
            '用原创角色、地点和冲突承载这些抽象风格参数。',
            '若来源仅为一般阅读参考，只做宏观结构提炼。',
            '正式章节仍需经过 Studio 审稿与写入正史确认。',
        ],
    )


def _style_safety_notes(source_rights: str) -> list[str]:
    notes = [
        '风格手册草稿只是写作参考，不会写入 canon、不会推进世界进度，也不会写入世界历史记录。',
        '输出只保留抽象风格和结构参数，不复用原文句子、人物名、专有设定或标志性桥段。',
    ]
    if source_rights == 'general_reference':
        notes.append('来源标记为一般阅读参考：只能做宏观节奏、结构和语言气质提炼。')
    elif source_rights in {'own_work', 'authorized', 'public_domain'}:
        notes.append('来源标记允许更深入分析，但正式使用前仍需用户确认并保留来源记录。')
    return notes


def preview_style_handbook(db: Session, user: User, world_id: int, data: StyleHandbookPreviewRequest) -> StyleHandbookPreviewResponse:
    world = require_owned_world(db, user, world_id)
    cleaned = _clean_content(data.content)
    return StyleHandbookPreviewResponse(
        world_id=world.id,
        source_type=data.source_type,
        source_title=data.source_title,
        source_rights=data.source_rights,
        cleaned_excerpt=_excerpt(cleaned),
        handbook=_build_style_handbook(cleaned),
        safety_notes=_style_safety_notes(data.source_rights),
        generation_notes=[
            '已从参考文本提炼叙事节奏、语言密度、对白比例、场景推进、悬念结构、人物关系张力和伏笔方式。',
            '本次只生成可审阅草稿；确认入口与持久化将在后续轮次接入。',
        ],
    )


def _asset_response(asset: ImportCandidateAsset) -> ImportCandidateAssetResponse:
    return ImportCandidateAssetResponse(
        id=asset.id,
        world_id=asset.world_id,
        batch_id=asset.batch_id,
        asset_pool=asset.asset_pool,
        title=asset.title,
        summary=asset.summary,
        raw_text=asset.raw_text,
        metadata=asset.asset_metadata,
        status=asset.status,
        created_at=asset.created_at,
    )


def _batch_response(batch: ImportBatch) -> ImportBatchResponse:
    return ImportBatchResponse(
        id=batch.id,
        world_id=batch.world_id,
        source_type=batch.source_type,
        source_title=batch.source_title,
        original_excerpt=batch.original_excerpt,
        cleaned_excerpt=batch.cleaned_excerpt,
        status=batch.status,
        asset_counts=batch.asset_counts,
        conflicts=batch.conflicts,
        created_at=batch.created_at,
        confirmed_at=batch.confirmed_at,
    )


MATERIAL_REFERENCE_SAFETY_NOTE = '导入素材参考只用于创作提示，不会自动改写正式 canon。'


def material_references_for_world(db: Session, world_id: int, limit: int = 6) -> list[ImportMaterialReferenceResponse]:
    rows = db.execute(
        select(ImportCandidateAsset, ImportBatch)
        .join(ImportBatch, ImportBatch.id == ImportCandidateAsset.batch_id)
        .where(ImportCandidateAsset.world_id == world_id)
        .where(ImportCandidateAsset.status == 'candidate')
        .order_by(desc(ImportCandidateAsset.id))
        .limit(limit)
    ).all()
    return [
        ImportMaterialReferenceResponse(
            asset_id=asset.id,
            batch_id=batch.id,
            asset_pool=asset.asset_pool,
            title=asset.title,
            summary=asset.summary,
            raw_text=asset.raw_text,
            source_title=batch.source_title,
            source_type=batch.source_type,
            created_at=asset.created_at,
            safety_note=MATERIAL_REFERENCE_SAFETY_NOTE,
        )
        for asset, batch in rows
    ]


def confirm_import(db: Session, user: User, world_id: int, data: ImportConfirmRequest) -> ImportConfirmResponse:
    world = require_owned_world(db, user, world_id)
    cleaned = _clean_content(data.content)
    asset_counts = _asset_counts(data.assets)
    now = datetime.now(timezone.utc)
    batch = ImportBatch(
        world_id=world.id,
        source_type=data.source_type,
        source_title=data.source_title,
        original_excerpt=_excerpt(data.content),
        cleaned_excerpt=_excerpt(cleaned),
        status='confirmed',
        asset_counts=asset_counts,
        conflicts=[conflict.model_dump() for conflict in data.conflicts],
        confirmed_at=now,
    )
    db.add(batch)
    db.flush()

    candidate_assets: list[ImportCandidateAsset] = []
    for item in data.assets:
        candidate = ImportCandidateAsset(
            world_id=world.id,
            batch_id=batch.id,
            asset_pool=item.asset_pool,
            title=item.title,
            summary=item.summary,
            raw_text=item.raw_text,
            asset_metadata=item.metadata,
            status='candidate',
        )
        db.add(candidate)
        candidate_assets.append(candidate)
    db.flush()

    db.add(
        EventLog(
            world_id=world.id,
            chapter_id=None,
            event_type='material_import_confirmed',
            source_type='import_node',
            commit_id=f'import-node-{world.id}-{batch.id}-{uuid4().hex}',
            payload={
                'batch_id': batch.id,
                'source_type': batch.source_type,
                'source_title': batch.source_title,
                'asset_counts': asset_counts,
                'conflict_count': len(data.conflicts),
            },
            world_version_before=world.world_version,
            world_version_after=world.world_version,
        )
    )
    db.commit()
    db.refresh(batch)
    for candidate in candidate_assets:
        db.refresh(candidate)
    return ImportConfirmResponse(batch=_batch_response(batch), assets=[_asset_response(asset) for asset in candidate_assets])


def list_import_batches(db: Session, user: User, world_id: int) -> ImportBatchListResponse:
    world = require_owned_world(db, user, world_id)
    batches = list(db.scalars(select(ImportBatch).where(ImportBatch.world_id == world.id).order_by(desc(ImportBatch.id)).limit(20)))
    items: list[ImportBatchWithAssetsResponse] = []
    for batch in batches:
        assets = list(db.scalars(select(ImportCandidateAsset).where(ImportCandidateAsset.batch_id == batch.id).order_by(ImportCandidateAsset.id)))
        batch_payload = _batch_response(batch).model_dump()
        items.append(ImportBatchWithAssetsResponse(**batch_payload, assets=[_asset_response(asset) for asset in assets]))
    return ImportBatchListResponse(world_id=world.id, batches=items)
