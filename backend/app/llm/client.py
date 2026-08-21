import ast
import inspect
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from time import perf_counter
from urllib.parse import urlsplit
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.llm.usage import AuditSessionFactory, extract_provider_usage, record_llm_usage, safe_error_code
from app.llm.schemas import (
    ChapterExtraction,
    ChapterGeneration,
    ChapterOutline,
    ChapterQualityReport,
    MemoryCompression,
    CharacterArcReport,
    OpeningEvidence,
    CritiqueReport,
    LiteraryCriticReport,
    LiteraryReviewReport,
    ParagraphRevision,
    StoryArcChapter,
    WorldCreationDraftPayload,
    WORLD_CREATION_DRAFT_JSON_SCHEMA,
    parse_chapter_extraction,
    parse_chapter_generation,
    parse_chapter_outline,
    parse_memory_compression,
    parse_quality_report,
    parse_opening_evidence_repair,
    parse_character_arc_report,
    parse_critique_report,
    parse_literary_critic_report,
    parse_literary_review,
    parse_paragraph_revision,
    parse_story_arc,
    parse_world_creation_draft,
)


MOCK_CHAPTER = {
    "title": "雨夜书阁",
    "draft_content": "暮色四合，秋雨如丝。青岚城因灵脉衰退而连夜戒严，城主府的灯火隔着雨幕巡查每一条巷道。\n\n身为云河剑宗外门弟子，林砚裹紧了外袍，踏过泥泞的青石巷。他已经三天没有合眼了，裂纹玉佩上的纹路日夜在脑海中盘旋。他必须在三日内查清玉佩与师门旧案的关系，否则灵脉一断，师妹也会被城主府带走。\n\n\"这里……\"他停下脚步，看见巷尾有一间从未见过的阁楼。匾额上写着\"忘归书阁\"三个古字，门扉半掩，透出暖黄色的光。\n\n推门而入，书卷的气味扑面而来。四面墙壁嵌满了竹简和线装书，中央的檀木桌上，一本古书正散发着幽幽青光。\n\n林砚的心跳骤然加快。他伸出手，指尖触碰到书封的瞬间，一股温热的气流顺着手臂涌入胸口。古书自动翻开，第一页赫然写着——\n\n\"青岚灵脉，将于三日后断绝。\"\n\n他猛地后退一步，目光却被下一页吸引：一幅精细的城主府地图，标注着一条从未见过的密道，直通地下深处。\n\n\"你是谁？\"身后传来一个苍老的声音。\n\n林砚转身，看见一位白发老者站在门口，手中提着一盏纸灯笼。老人的眼睛浑浊却锐利，仿佛能看穿一切。\n\n\"我……我只是避雨。\"林砚下意识地握紧了怀中的玉佩。\n\n老者微微一笑：\"避雨的人，不会走进忘归书阁。你身上有它的召唤。\"他指了指桌上的古书，\"拿走吧。它会告诉你真相——关于城主府，关于灵脉，也关于你自己。\"\n\n林砚犹豫了片刻，最终还是将古书收入怀中。青光透过衣襟，隐隐可见。\n\n\"记住，\"老者在他身后说道，\"三日之后，一切都会改变。选择权在你手中。\"\n\n走出书阁时，雨已经停了。林砚回头望去——巷尾空空荡荡，仿佛那间阁楼从未存在过。\n\n他深吸一口气，快步消失在夜色中。怀中的古书微微发烫，像是在催促他做出决定。",
    "context_summary": "林砚在雨夜发现神秘书阁，获得一本预言古书。古书记载青岚灵脉将在三日后断绝，并包含城主府密道地图。神秘老者暗示林砚被古书选中，将真相与选择权交到他手中。",
    "review_hints": [
        "裂纹玉佩线索推进：林砚三天未眠，持续关注玉佩纹路",
        "新伏笔引入：忘归书阁和预言古书，三日倒计时开始",
        "城主府叛乱传闻新证据：古书中的密道地图",
        "角色状态变化：林砚从调查者变为被选中者",
    ],
    "proposed_character_changes": [
        {"character_id": 1, "status": "获得预言古书，面临三日抉择", "current_goals": ["破解古书预言", "探查城主府密道", "保护灵脉"]}
    ],
    "proposed_foreshadow_changes": [
        {"foreshadow_id": 1, "status": "advanced", "description_note": "玉佩与古书产生共鸣，暗示两者关联"}
    ],
    "opening_evidence": [
        {"check": "background", "paragraph_index": 0, "quote": "青岚城因灵脉衰退而连夜戒严"},
        {"check": "protagonist_identity", "paragraph_index": 1, "quote": "身为云河剑宗外门弟子"},
        {"check": "motivation", "paragraph_index": 1, "quote": "必须在三日内查清玉佩与师门旧案的关系"},
        {"check": "personality_evidence_plan", "paragraph_index": 11, "quote": "犹豫了片刻，最终还是将古书收入怀中"},
        {"check": "conflict_goal", "paragraph_index": 1, "quote": "否则灵脉一断，师妹也会被城主府带走"},
        {"check": "locked_pov", "paragraph_index": 9, "quote": "林砚下意识地握紧了怀中的玉佩"},
    ],
}

MOCK_WORLD_CREATION_DRAFT = {
    "draft": {
        "title": "死因王国",
        "genre_template": "fantasy",
        "truth_canon": "在这个王国里，每个人出生时都会被分配一个未来死因。死因不是诅咒，而是王权、教会和命运官共同维护的社会秩序。主角发现自己的死因被篡改，意味着有人正在改写整个王国的命运账本。",
        "tone_profile": {"style": "黑暗奇幻悬疑", "pacing": "高张力冷启动", "theme": "命运是否可以被审判"},
        "starter_assets": {
            "characters": [
                {
                    "name": "伊莱",
                    "role_type": "protagonist",
                    "status": "active",
                    "public_profile": {
                        "identity": "低阶命运抄写员",
                        "skill": "辨认死因纹章",
                        "public_motivation": "维护死因档案的可信度",
                    },
                    "hidden_traits": {
                        "secret": "出生记录缺失了最后一页",
                        "fear": "自己的命运从未被登记",
                        "private_agenda": "找到原始命运账本",
                        "weakness": "过度相信书面记录",
                    },
                    "destiny_flag": "死因被篡改者",
                    "current_goals": ["查明自己的死因为何被改写", "确认命运官是否参与造假"],
                },
                {
                    "name": "维拉",
                    "role_type": "rival",
                    "status": "active",
                    "public_profile": {
                        "identity": "王国命运官",
                        "skill": "审判死因合法性",
                        "public_motivation": "维持命运秩序",
                    },
                    "hidden_traits": {
                        "secret": "掌握旧账本钥匙",
                        "fear": "害怕命运账本公开崩塌",
                        "private_agenda": "阻止王室篡改记录曝光",
                        "weakness": "无法容忍失控",
                    },
                    "destiny_flag": "掌握旧账本钥匙的人",
                    "current_goals": ["阻止伊莱接触王室死因档案"],
                },
            ],
            "relations": [
                {"source_index": 0, "target_index": 1, "relation_type": "mutual_suspicion", "intensity": 4, "visibility": "private"}
            ],
            "foreshadows": [
                {
                    "title": "空白死因页",
                    "description": "伊莱的出生死因登记页上留有一块被银火烧穿的空白，边缘残留王室封蜡。",
                    "foreshadow_type": "fate_record_clue",
                    "status": "planted",
                    "urgency_level": 4,
                    "related_character_indexes": [0, 1],
                    "expected_resolution_window": "第3-5章",
                }
            ],
        },
    },
    "first_chapter_goal": "让伊莱在替人誊写死因档案时发现自己的记录被银火烧穿，并在维拉赶到封锁档案室前偷看到王室封蜡。",
    "generation_notes": ["已把一句话脑洞扩展为可审阅的世界创建表单草稿。"],
    "safety_notes": ["草稿尚未创建世界；确认前不会写入正史或推进世界进度。"],
    "followup_questions": ["主角更想推翻死因秩序，还是先救一个被错误判死的人？"],
}

MOCK_OUTLINE = {
    "core_conflict": "林砚必须判断沈微霜是否可信，并决定是否进入城主府密道。",
    "pov_suggestion": "林砚",
    "pacing": "悬疑递进，章末揭示新入口",
    "role_skill_targets": ["林砚", "沈微霜"],
    "beats": [
        {
            "beat_id": "beat-1",
            "summary": "林砚在雨夜追踪裂纹玉佩的灵力反应。",
            "pov_character": "林砚",
            "location": "青岚城后巷",
            "emotional_arc": "疲惫 -> 警觉",
            "key_dialogue_hints": ["这枚玉佩在指路。"],
        },
        {
            "beat_id": "beat-2",
            "summary": "沈微霜阻止林砚进入密道，却暴露自己知道更多内情。",
            "pov_character": "林砚",
            "location": "城主府外墙",
            "emotional_arc": "怀疑 -> 对峙",
            "key_dialogue_hints": ["你不该来这里。"],
        },
    ],
    "opening_contract": {
        "background": "青岚城灵脉衰退，雨夜戒严使调查窗口迅速收紧。",
        "protagonist_identity": "林砚是云河剑宗外门弟子，也是裂纹玉佩线索的持有者。",
        "motivation": "林砚必须查清玉佩与师门旧案的关系，并避免师妹被城主府带走。",
        "personality_evidence_plan": "通过林砚明知危险仍收下古书、继续追查的选择表现他的谨慎与担当。",
        "conflict_goal": "在灵脉三日后断绝前确认密道与玉佩的关系，同时躲避城主府追查。",
        "locked_pov": "林砚第三人称限知视角。",
    },
}

MOCK_CRITIQUE = {
    "score": 84,
    "issues": [
        {"category": "character_voice", "severity": "medium", "message": "沈微霜台词可以更克制。"},
        {"category": "foreshadow", "severity": "low", "message": "裂纹玉佩线索已推进，但回收窗口仍需保持。"},
    ],
    "suggestions": ["加强林砚担心牵连师门的内心压力。"],
    "consistency_check": {
        "character_voice": "needs_minor_revision",
        "foreshadow_usage": "advanced",
        "world_rule_adherence": "pass",
        "pacing": "pass",
    },
}

MOCK_LITERARY_CRITIC = {
    "overall_score": 82,
    "summary": "章节结构清晰，角色动机基本稳定，但中段对白可以更有潜台词。",
    "dimensions": {
        "pacing": {"score": 80, "summary": "推进稳定。", "issues": [], "suggestions": ["保留章末钩子。"]},
        "tension": {"score": 82, "summary": "冲突明确。", "issues": [], "suggestions": ["强化对峙压力。"]},
        "character_consistency": {"score": 84, "summary": "角色目标一致。", "issues": [], "suggestions": ["保持林砚谨慎。"]},
        "dialogue_quality": {
            "score": 74,
            "summary": "对白略直白。",
            "issues": [
                {
                    "severity": "medium",
                    "dimension": "dialogue_quality",
                    "message": "沈微霜台词可以更克制。",
                    "paragraph_index": 1,
                    "suggested_action": "润色相关段落。",
                }
            ],
            "suggestions": ["减少解释性台词。"],
        },
        "structure": {"score": 83, "summary": "起承转合清楚。", "issues": [], "suggestions": ["章末增加反转。"]},
        "world_continuity": {"score": 88, "summary": "世界状态一致。", "issues": [], "suggestions": ["保持伏笔推进。"]},
        "readability": {"score": 78, "summary": "语言顺畅。", "issues": [], "suggestions": ["压缩重复意象。"]},
    },
    "issues": [
        {
            "severity": "medium",
            "dimension": "dialogue_quality",
            "message": "沈微霜台词可以更克制。",
            "paragraph_index": 1,
            "suggested_action": "润色相关段落。",
        }
    ],
    "suggestions": ["优先润色第二段对白。"],
}

MOCK_CHARACTER_ARC_REPORT = {
    "summary": "本章推动林砚从被动调查转向主动选择下一步行动。",
    "character_arcs": [
        {
            "character_id": 1,
            "name": "林砚",
            "role_type": "protagonist",
            "current_status": "active",
            "current_goals": [],
            "presence_level": "major",
            "arc_stage": "choice",
            "chapter_function": "承担调查者与选择者功能。",
            "observed_shift": "从谨慎观察转向主动追问线索。",
            "proposed_state_change": {"status": "获得预言古书，面临三日抉择"},
            "continuity_risk": "medium",
            "risk_reason": "信任建立需要更多铺垫。",
            "suggested_revision": "增加林砚试探盟友的动作。",
            "next_chapter_setup": "让林砚围绕密道做出第一次冒险选择。",
        }
    ],
    "relationship_notes": [],
    "progression_hints": [
        {
            "hint_type": "character",
            "priority": "high",
            "title": "让林砚做出是否冒险进入密道的选择",
            "rationale": "当前章节已给出线索，下一章需要转化为行动。",
            "suggested_next_beat": "林砚在城主府外墙试探密道入口。",
            "related_character_ids": [1],
            "related_foreshadow_ids": [1],
            "can_seed_next_chapter_goal": True,
        }
    ],
}


MOCK_STORY_ARC = [
    {
        "chapter_number": 1,
        "title": "裂纹玉佩的召唤",
        "summary": "林砚发现裂纹玉佩开始指向青岚城深处。城主府的异常灵力让他意识到灵脉危机并非自然衰退。",
        "core_conflict": "林砚必须决定是否冒险调查城主府。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["裂纹玉佩"],
    },
    {
        "chapter_number": 2,
        "title": "密道外的拦截",
        "summary": "沈微霜在城主府外阻止林砚靠近密道。两人的对峙暴露她知道灵脉衰退的隐情。",
        "core_conflict": "林砚必须判断沈微霜是敌是友。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["城主府密道"],
    },
    {
        "chapter_number": 3,
        "title": "忘归书阁",
        "summary": "雨夜中，林砚进入只在灵力紊乱时出现的忘归书阁。古书预言青岚灵脉将在三日后断绝。",
        "core_conflict": "林砚必须接受预言并寻找可信盟友。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["预言古书"],
    },
    {
        "chapter_number": 4,
        "title": "师门旧债",
        "summary": "林砚发现师门旧案与城主府封印有关。继续追查可能让他背负叛徒后人的污名。",
        "core_conflict": "林砚必须在个人名誉与真相之间取舍。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["师门旧案"],
    },
    {
        "chapter_number": 5,
        "title": "灵井回声",
        "summary": "地下灵井传来第二个人的脚步声，证明有人正在提前抽离灵脉。沈微霜被迫透露她一直在监视灵井。",
        "core_conflict": "林砚与沈微霜必须短暂合作却无法互相信任。",
        "pov_suggestion": "沈微霜",
        "foreshadow_hints": ["灵井异响"],
    },
    {
        "chapter_number": 6,
        "title": "城主的空座",
        "summary": "城主公开露面时表现得像被某种契约操控。林砚意识到真正的对手可能藏在城主身后。",
        "core_conflict": "林砚必须揭穿操控者而不惊动城主府守卫。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["城主府叛乱传闻"],
    },
    {
        "chapter_number": 7,
        "title": "玉佩中的名字",
        "summary": "裂纹玉佩映出一个被抹去的名字，指向林砚家族与灵脉契约的源头。线索同时引来城主府追兵。",
        "core_conflict": "林砚必须保护线索并面对自己的血脉身份。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["裂纹玉佩", "血脉契约"],
    },
    {
        "chapter_number": 8,
        "title": "三日之限",
        "summary": "预言中的最后一日到来，青岚城开始出现灵力枯竭。林砚必须选择先救城民还是先阻止幕后仪式。",
        "core_conflict": "救人会错过仪式，阻止仪式会牺牲眼前城民。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["三日倒计时"],
    },
    {
        "chapter_number": 9,
        "title": "地下封印",
        "summary": "林砚与沈微霜进入地下封印核心，发现灵脉断绝是旧契约反噬。两人必须共同承担解除封印的代价。",
        "core_conflict": "解除封印需要牺牲一段关键记忆。",
        "pov_suggestion": "沈微霜",
        "foreshadow_hints": ["地下封印", "血脉契约"],
    },
    {
        "chapter_number": 10,
        "title": "青岚新脉",
        "summary": "林砚用玉佩重写契约，保住青岚城但改变了自己与灵脉的关系。旧伏笔得到回收，新危机在灵脉深处苏醒。",
        "core_conflict": "胜利的代价让林砚成为新契约的承载者。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["裂纹玉佩", "青岚灵脉"],
    },
]


def _last_user_prompt(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get('role') == 'user' and isinstance(message.get('content'), str):
            return message['content']
    return ''


_OPENING_SENTENCE_BOUNDARIES = ('，', ',', '；', ';', '。', '！', '!', '？', '?', '：', ':')


def _opening_paragraphs(content: str) -> list[str]:
    return [paragraph.strip() for paragraph in content.split('\n\n') if paragraph.strip()]


def _opening_quote_spans(paragraph: str, quote: str) -> list[tuple[int, int]]:
    spans = []
    search_start = 0
    while True:
        quote_start = paragraph.find(quote, search_start)
        if quote_start < 0:
            return spans
        spans.append((quote_start, quote_start + len(quote)))
        search_start = quote_start + 1


def _opening_sentence_at(paragraph: str, span_start: int, span_end: int) -> str:
    sentence_start = 0
    sentence_end = len(paragraph)
    for boundary in _OPENING_SENTENCE_BOUNDARIES:
        boundary_start = paragraph.rfind(boundary, 0, span_start)
        sentence_start = max(sentence_start, boundary_start + 1)
        boundary_end = paragraph.find(boundary, span_end)
        if boundary_end >= 0:
            sentence_end = min(sentence_end, boundary_end + 1)
    return paragraph[sentence_start:sentence_end].strip()


def _opening_evidence_needs_repair(content: str, opening_evidence: list[OpeningEvidence]) -> bool:
    expected_checks = {
        'background',
        'protagonist_identity',
        'motivation',
        'personality_evidence_plan',
        'conflict_goal',
        'locked_pov',
    }
    if len(opening_evidence) != len(expected_checks) or {evidence.check for evidence in opening_evidence} != expected_checks:
        return True

    paragraphs = _opening_paragraphs(content)
    positioned = []
    seen_quotes = set()
    for evidence in opening_evidence:
        if evidence.quote in seen_quotes:
            return True
        seen_quotes.add(evidence.quote)
        if not 0 <= evidence.paragraph_index < len(paragraphs) or not evidence.quote.strip():
            return True
        spans = _opening_quote_spans(paragraphs[evidence.paragraph_index], evidence.quote)
        if len(spans) != 1:
            return True
        quote_start, quote_end = spans[0]
        positioned.append((evidence.check, evidence.paragraph_index, quote_start, quote_end))

    for index, (_check, paragraph_index, quote_start, quote_end) in enumerate(positioned):
        sentence = _opening_sentence_at(paragraphs[paragraph_index], quote_start, quote_end)
        for _other_check, other_paragraph_index, other_start, other_end in positioned[index + 1:]:
            if paragraph_index != other_paragraph_index:
                continue
            if max(quote_start, other_start) < min(quote_end, other_end):
                return True
            if sentence == _opening_sentence_at(paragraphs[other_paragraph_index], other_start, other_end):
                return True
    return False


def _looks_like_opening_prompt(messages: list[dict[str, str]]) -> bool:
    return 'opening_contract' in _last_user_prompt(messages)


def _mock_opening_evidence_repair(
    content: str,
    opening_evidence: list[OpeningEvidence],
) -> list[OpeningEvidence]:
    paragraphs = _opening_paragraphs(content)
    checks = (
        'background',
        'protagonist_identity',
        'motivation',
        'personality_evidence_plan',
        'conflict_goal',
        'locked_pov',
    )
    if len(paragraphs) < len(checks):
        return opening_evidence
    return [
        OpeningEvidence(check=check, paragraph_index=index, quote=paragraphs[index])
        for index, check in enumerate(checks)
    ]


def _opening_evidence_repair_messages(
    messages: list[dict[str, str]],
    content: str,
    opening_evidence: list[OpeningEvidence],
) -> list[dict[str, str]]:
    evidence_payload = [evidence.model_dump() for evidence in opening_evidence]
    return [
        {
            'role': 'system',
            'content': (
                '你是 WorldSim-Writer 的 opening_evidence 修复器。只返回合法 JSON，且根对象只能包含 '
                'opening_evidence 一个字段：{"opening_evidence":[{"check":"background|protagonist_identity|motivation|'
                'personality_evidence_plan|conflict_goal|locked_pov","paragraph_index":0,"quote":"正文原文片段"}]}。'
                '你只能修复 opening_evidence，禁止输出或改写 title、draft_content、context_summary、review_hints、'
                'proposed_character_changes 或 proposed_foreshadow_changes。paragraph_index 必须是正文非空自然段的 0-based 索引；'
                'quote 必须是对应自然段中的连续原文子串，并为每项选择唯一、不重叠且不复用的证据。必须完整返回六项 check。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'原始章节请求上下文：\n{_last_user_prompt(messages)}\n'
                f'不可修改正文：\n{content}\n'
                f'当前 opening_evidence：{json.dumps(evidence_payload, ensure_ascii=False)}\n'
                '请只返回修复后的 opening_evidence。正文必须保持逐字不变。'
            ),
        },
    ]


def _looks_like_contextual_prompt(prompt: str) -> bool:
    return any(
        marker in prompt
        for marker in (
            '世界标题：',
            '世界设定：',
            '角色：\n',
            '伏笔：\n',
            '紧迫伏笔：\n',
            '当前正文：\n',
            '本章目标：',
            '章节目标：',
            '用户一句话脑洞：',
            '请规划前 10 章故事弧线',
            '请为第',
        )
    )


def _raise_for_unparseable_context(messages: list[dict[str, str]]) -> None:
    if _looks_like_contextual_prompt(_last_user_prompt(messages)):
        raise ValueError('MODEL_RESPONSE_INVALID')


def _literal_value(raw: str, default):
    try:
        value = ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        return default
    return value if isinstance(value, type(default)) else default


def _prompt_value(prompt: str, *labels: str) -> str:
    for label in labels:
        match = re.search(rf'^{re.escape(label)}：(.*)$', prompt, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ''


def _prompt_block(prompt: str, label: str, end_labels: tuple[str, ...]) -> str:
    end_pattern = '|'.join(re.escape(value) for value in end_labels)
    match = re.search(
        rf'^{re.escape(label)}：\n(.*?)(?=^(?:{end_pattern})：|\Z)',
        prompt,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ''


def _prompt_text_section(prompt: str, label: str, end_markers: tuple[str, ...]) -> str:
    marker = f'{label}：\n'
    start = prompt.find(marker)
    if start < 0:
        return ''
    value = prompt[start + len(marker):]
    end_positions = [value.find(marker) for marker in end_markers if value.find(marker) >= 0]
    if end_positions:
        value = value[:min(end_positions)]
    return value.strip()


def _key_value_fields(raw: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2).strip()
        for match in re.finditer(
            r'(?:^|,\s*)([A-Za-z_]+)=(.*?)(?=,\s*[A-Za-z_]+=|$)',
            raw,
        )
    }


def _numbered_entities(block: str) -> list[dict]:
    entities = []
    for line in block.splitlines():
        match = re.match(r'^-\s*(\d+):\s*([^,\n]+)(?:,\s*(.*))?$', line.strip())
        if not match:
            continue
        fields = _key_value_fields(match.group(3) or '')
        profile_raw = fields.get('public_profile') or fields.get('profile') or fields.get('public') or '{}'
        hidden_raw = fields.get('hidden_traits') or fields.get('hidden') or '{}'
        entities.append({
            'id': int(match.group(1)),
            'name': match.group(2).strip(),
            'role': fields.get('role', '').strip(),
            'status': fields.get('status', '').strip(),
            'profile': _literal_value(profile_raw, {}),
            'hidden_traits': _literal_value(hidden_raw, {}),
            'destiny': fields.get('destiny', '').strip(),
            'goals': _literal_value(fields.get('goals', '[]'), []),
            'type': fields.get('type', '').strip(),
            'urgency': fields.get('urgency', '').strip(),
            'description': fields.get('description', '').strip(),
            'window': fields.get('window', '').strip(),
            'related': _literal_value(fields.get('related', '[]'), []),
        })
    return entities


def _mock_prompt_entities(prompt: str) -> tuple[list[dict], list[dict]]:
    character_block = _prompt_block(
        prompt,
        '角色',
        ('紧迫伏笔', '伏笔', '关系', '近期事件', '章节标题', '本章目标', '章节目标', 'Outliner上下文'),
    )
    foreshadow_block = _prompt_block(
        prompt,
        '紧迫伏笔',
        ('本章目标', '章节目标', 'Outliner上下文', '近期事件', '章节标题'),
    ) or _prompt_block(
        prompt,
        '伏笔',
        ('本章目标', '章节目标', 'Outliner上下文', '近期事件', '章节标题'),
    )
    return _numbered_entities(character_block), _numbered_entities(foreshadow_block)


def _parse_mock_prompt(messages: list[dict[str, str]]) -> dict | None:
    """Parse production-shaped narrative prompts into deterministic mock context."""
    prompt = _last_user_prompt(messages)
    world_title = _prompt_value(prompt, '世界标题')
    world_canon = _prompt_value(prompt, '世界设定')
    chapter_goal = _prompt_value(prompt, '本章目标', '章节目标')
    if not (world_title and world_canon and chapter_goal and '角色：\n' in prompt):
        return None

    characters, foreshadows = _mock_prompt_entities(prompt)
    recommended_pov = _prompt_value(prompt, '- 推荐 POV')
    if recommended_pov in {'暂无', '无', 'None'}:
        recommended_pov = ''
    chapter_match = re.search(r'^- 章节序号：\s*(\d+)', prompt, re.MULTILINE)
    outline_context = _literal_value(_prompt_value(prompt, 'Outliner上下文'), {})
    return {
        'prompt': prompt,
        'world_title': world_title,
        'world_canon': world_canon,
        'chapter_goal': chapter_goal,
        'chapter_title': _prompt_value(prompt, '章节标题'),
        'characters': characters,
        'foreshadows': foreshadows,
        'recommended_pov': recommended_pov,
        'chapter_number': int(chapter_match.group(1)) if chapter_match else None,
        'opening_contract': outline_context.get('opening_contract') if isinstance(outline_context, dict) else None,
    }


def _parse_report_context(messages: list[dict[str, str]]) -> dict:
    prompt = _last_user_prompt(messages)
    characters, foreshadows = _mock_prompt_entities(prompt)
    relation_block = _prompt_block(prompt, '关系', ('伏笔', '近期事件', '章节标题'))
    relations = []
    for line in relation_block.splitlines():
        match = re.match(r'^-\s*(\d+)->(\d+):\s*(.*)$', line.strip())
        if not match:
            continue
        fields = _key_value_fields(match.group(3))
        relations.append({
            'source_id': int(match.group(1)),
            'target_id': int(match.group(2)),
            'type': fields.get('type', 'related'),
            'intensity': int(fields['intensity']) if fields.get('intensity', '').isdigit() else None,
            'visibility': fields.get('visibility') or None,
        })
    chapter_match = re.search(r'^- 章节序号：\s*(\d+)', prompt, re.MULTILINE)
    outline_context = _literal_value(_prompt_value(prompt, 'Outliner上下文'), {})
    return {
        'prompt': prompt,
        'world_title': _prompt_value(prompt, '世界标题'),
        'world_canon': _prompt_value(prompt, '世界设定'),
        'chapter_title': _prompt_value(prompt, '章节标题'),
        'chapter_goal': _prompt_value(prompt, '本章目标', '章节目标'),
        'characters': characters,
        'foreshadows': foreshadows,
        'relations': relations,
        'recommended_pov': _prompt_value(prompt, '- 推荐 POV'),
        'chapter_number': int(chapter_match.group(1)) if chapter_match else None,
        'opening_contract': outline_context.get('opening_contract') if isinstance(outline_context, dict) else None,
        'current_content': _prompt_text_section(prompt, '当前正文', ('\nCritic报告：',)) or _prompt_text_section(
            prompt,
            '正文',
            ('\n请检查', '\n请从', '\n请分析'),
        ),
        'instruction': _prompt_value(prompt, '人工修订指令'),
    }


def _mock_pov(context: dict) -> dict | None:
    characters = context['characters']
    if not characters:
        return None
    recommended = context.get('recommended_pov') or ''
    return next((character for character in characters if character['name'] == recommended), None) or next(
        (character for character in characters if character['role'] == 'protagonist'),
        characters[0],
    )


def _contextual_mock_outline(context: dict) -> ChapterOutline:
    pov = _mock_pov(context)
    is_opening = context.get('chapter_number') == 1
    if is_opening and pov is None:
        raise ValueError('MODEL_RESPONSE_INVALID')

    names = [character['name'] for character in context['characters']]
    foreshadow = context['foreshadows'][0] if context['foreshadows'] else None
    foreshadow_title = foreshadow['name'] if foreshadow else '当前线索'
    location = context['world_title']
    actor = pov['name'] if pov else '现场调查者'
    outline_data = {
        'core_conflict': f"{actor}必须在{context['world_title']}完成{context['chapter_goal']}，并承受{foreshadow_title}带来的阻力。",
        'pov_suggestion': pov['name'] if pov else None,
        'pacing': '首章冷启动，逐步收紧冲突。' if is_opening else '承接既有进展，推动当前冲突升级。',
        'role_skill_targets': names,
        'beats': [
            {
                'beat_id': 'beat-1',
                'summary': f"{actor}在{context['world_title']}发现{foreshadow_title}与章节目标相连。",
                'pov_character': pov['name'] if pov else None,
                'location': location,
                'emotional_arc': '警觉 -> 决断',
                'key_dialogue_hints': [context['chapter_goal']],
            },
            {
                'beat_id': 'beat-2',
                'summary': f"{actor}面对新的阻力，决定继续推进{foreshadow_title}。",
                'pov_character': pov['name'] if pov else None,
                'location': location,
                'emotional_arc': '犹疑 -> 行动',
                'key_dialogue_hints': [f"{foreshadow_title}不能就此中断。"],
            },
        ],
        'opening_contract': None,
    }
    if is_opening and pov is not None:
        identity = pov['profile'].get('identity') or pov['role'] or '当前事件的调查者'
        goals = '、'.join(pov['goals']) or context['chapter_goal']
        outline_data['opening_contract'] = {
            'background': f"{context['world_title']}的规则是：{context['world_canon']}",
            'protagonist_identity': f"{pov['name']}是{identity}。",
            'motivation': f"{pov['name']}必须{goals}。",
            'personality_evidence_plan': f"通过{pov['name']}在压力下仍选择推进{context['chapter_goal']}，表现其主动与克制。",
            'conflict_goal': f"{pov['name']}要完成{context['chapter_goal']}，并处理{foreshadow_title}。",
            'locked_pov': f"固定跟随{pov['name']}第三人称限知视角。",
        }
    return ChapterOutline.model_validate(outline_data)


def _contextual_mock_chapter(context: dict) -> ChapterGeneration:
    pov = _mock_pov(context)
    is_opening = context.get('chapter_number') == 1 or bool(context.get('opening_contract'))
    if is_opening and pov is None:
        raise ValueError('MODEL_RESPONSE_INVALID')

    foreshadow = context['foreshadows'][0] if context['foreshadows'] else None
    foreshadow_title = foreshadow['name'] if foreshadow else '眼前线索'
    chapter_number = context.get('chapter_number') or 1
    if pov is None:
        paragraphs = [
            f"{context['world_title']}的公共记录仍写着：{context['world_canon']}，但现场出现了无法被旧规则解释的异常。",
            f"空置的通道里没有登记角色留下姓名，只有反复出现的痕迹指向同一件事：{context['chapter_goal']}",
            f"调查因此从人物选择转向世界规则本身，记录者逐项核对时间、地点与物证，不替任何缺席者编造身份。",
            f"当新的阻力封住出口，现场证据仍把行动方向压向{foreshadow_title}，迫使调查继续而不是回到无关旧案。",
        ]
        return ChapterGeneration.model_validate({
            'title': f"第{chapter_number}章 {context['chapter_goal'].rstrip('。！？!?')}",
            'draft_content': '\n\n'.join(paragraphs),
            'context_summary': f"{context['world_title']}的世界级冲突围绕{context['chapter_goal']}继续推进。",
            'review_hints': ['当前世界没有可引用角色，草稿未提出角色或伏笔 ID 变化。'],
            'proposed_character_changes': [],
            'proposed_foreshadow_changes': [],
            'opening_evidence': [],
        })

    names = [character['name'] for character in context['characters']]
    other_names = [name for name in names if name != pov['name']]
    counterpart = '、'.join(other_names) or '尚未露面的阻力方'
    identity = pov['profile'].get('identity') or pov['role'] or '当前事件的调查者'
    personal_goal = '、'.join(pov['goals']) or context['chapter_goal']
    paragraphs = [
        f"{context['world_title']}的空气像被无形的门闩扣住，街道、站台与远处的灯光都服从同一条规则：{context['world_canon']}。{pov['name']}站在异常发生的边缘，先确认退路，再把目光移向{foreshadow_title}，因为今夜任何迟疑都会让线索失去位置。",
        f"作为{identity}，{pov['name']}熟悉这里每一道日常秩序，却也看出眼前细节与常识不合。{counterpart}留下的动静隔着障碍传来，迫使{pov['name']}把身份带来的责任和个人判断放在同一次选择里。",
        f"{pov['name']}没有忘记自己的目标：{personal_goal}。要完成“{context['chapter_goal']}”，必须先分清谁在制造假象、谁在保护真相；如果此刻后退，{foreshadow_title}就会被下一次变化彻底掩埋。",
        f"压力逼近时，{pov['name']}没有立刻相信最方便的解释，而是俯身核对痕迹、重新安排顺序，再主动触碰{foreshadow_title}。这个克制又冒险的动作暴露了性格，也让原本停滞的局面第一次出现可追踪的回应。",
        f"新的阻力随即封住路径。为了{context['chapter_goal']}，{pov['name']}必须与{counterpart}周旋，同时守住刚刚确认的事实；冲突不再只是得到一件东西，而是决定是否用自己的代价换取继续调查的机会。",
        f"叙述始终只跟随{pov['name']}第三人称限知视角：{pov['name']}只能依据亲眼所见、亲耳所闻和当下推断作出决定。就在下一步行动确定时，{foreshadow_title}给出新的反应，把{context['world_title']}的秘密推向更近也更危险的位置。",
    ]
    draft_content = '\n\n'.join(paragraphs)
    evidence = []
    if is_opening:
        evidence = [
            {'check': 'background', 'paragraph_index': 0, 'quote': paragraphs[0]},
            {'check': 'protagonist_identity', 'paragraph_index': 1, 'quote': paragraphs[1]},
            {'check': 'motivation', 'paragraph_index': 2, 'quote': paragraphs[2]},
            {'check': 'personality_evidence_plan', 'paragraph_index': 3, 'quote': paragraphs[3]},
            {'check': 'conflict_goal', 'paragraph_index': 4, 'quote': paragraphs[4]},
            {'check': 'locked_pov', 'paragraph_index': 5, 'quote': paragraphs[5]},
        ]
    return ChapterGeneration.model_validate({
        'title': f"第{chapter_number}章 {foreshadow_title}",
        'draft_content': draft_content,
        'context_summary': f"{pov['name']}在{context['world_title']}推进了{foreshadow_title}与章节目标。",
        'review_hints': [f"检查{pov['name']}与{counterpart}的后续关系。"],
        'proposed_character_changes': [{
            'character_id': pov['id'],
            'status': f"推进{context['chapter_goal']}",
            'current_goals': pov['goals'] or [context['chapter_goal']],
        }],
        'proposed_foreshadow_changes': ([{
            'foreshadow_id': foreshadow['id'],
            'status': 'advanced',
            'description_note': f"{foreshadow_title}已在本章推进。",
        }] if foreshadow else []),
        'opening_evidence': evidence,
    })


def _contextual_mock_story_arc(messages: list[dict[str, str]]) -> list[StoryArcChapter] | None:
    prompt = _last_user_prompt(messages)
    world_title = _prompt_value(prompt, '世界标题')
    world_canon = _prompt_value(prompt, '世界设定')
    if not world_title or '请规划前 10 章故事弧线' not in prompt:
        return None
    characters, foreshadows = _mock_prompt_entities(prompt)
    pov = next((character for character in characters if character['role'] == 'protagonist'), None)
    pov = pov or (characters[0] if characters else None)
    pov_name = pov['name'] if pov else '环境观察视角'
    cast = '、'.join(character['name'] for character in characters) or '尚未登记的行动者'
    foreshadow_titles = [foreshadow['name'] for foreshadow in foreshadows]
    chapters = []
    for chapter_number in range(1, 11):
        focus = foreshadow_titles[(chapter_number - 1) % len(foreshadow_titles)] if foreshadow_titles else '世界规则异常'
        chapters.append({
            'chapter_number': chapter_number,
            'title': f"第{chapter_number}章 {focus}的回响",
            'summary': (
                f"{cast}在{world_title}继续追查{focus}，并验证“{world_canon}”带来的后果。"
                f"第{chapter_number}章让已有目标承受更具体的代价。"
            ),
            'core_conflict': f"{pov_name}必须在推进{focus}与保护当前关系之间作出第{chapter_number}次选择。",
            'pov_suggestion': pov_name,
            'foreshadow_hints': [focus] if foreshadow_titles else [],
        })
    return parse_story_arc(json.dumps(chapters, ensure_ascii=False))


def _suggest_goal_entities(prompt: str) -> tuple[list[str], list[str]]:
    character_block = _prompt_block(prompt, '角色', ('伏笔',))
    foreshadow_block = _prompt_block(prompt, '伏笔', ())
    characters = []
    for line in character_block.splitlines():
        match = re.match(r'^-\s*(.+?)（(.+?)）:', line.strip())
        if match:
            characters.append(match.group(1).strip())
    foreshadows = []
    for line in foreshadow_block.splitlines():
        match = re.match(r'^-\s*(.+?)（(.+?)）:', line.strip())
        if match:
            foreshadows.append(match.group(1).strip())
    return characters, foreshadows


def _contextual_mock_goal(messages: list[dict[str, str]]) -> dict | None:
    prompt = _last_user_prompt(messages)
    world_title = _prompt_value(prompt, '世界标题')
    world_canon = _prompt_value(prompt, '世界设定')
    if not world_title or '请为第' not in prompt:
        return None
    characters, foreshadows = _suggest_goal_entities(prompt)
    chapter_match = re.search(r'请为第\s*(\d+)\s*章', prompt)
    chapter_number = int(chapter_match.group(1)) if chapter_match else 1
    actor = characters[0] if characters else '一名未具名调查者'
    counterpart = '、'.join(characters[1:]) or '阻止调查的人'
    clue = foreshadows[0] if foreshadows else '世界规则中的异常'
    return {
        'goal': (
            f"第{chapter_number}章让{actor}在{world_title}追查{clue}，并从“{world_canon}”的规则中找到一个会改变行动方向的新证据。"
            f"{actor}必须与{counterpart}正面交锋，在保住线索和维持现有关系之间作出无法撤回的选择。"
        )
    }


def _contextual_mock_world_creation(messages: list[dict[str, str]]) -> WorldCreationDraftPayload:
    prompt = _last_user_prompt(messages)
    brief = _prompt_value(prompt, '用户一句话脑洞') or prompt.strip() or '一个等待命名的原创世界'
    variant_match = re.search(r'本次请生成“(.+?)”方向', prompt)
    variant = variant_match.group(1).strip() if variant_match else '原创悬疑'
    compact_brief = re.sub(r'\s+', '', brief).strip('。！？!?，,；;：:') or '未命名世界'
    title = compact_brief[:12]
    anchor = compact_brief[-4:]
    if any(keyword in brief for keyword in ('深空', '星舰', '宇宙', '列车')):
        genre = '科幻悬疑'
    elif any(keyword in brief for keyword in ('浮岛', '魔法', '王国', '神谕')):
        genre = '奇幻悬疑'
    else:
        genre = '原创悬疑'
    protagonist_name = f'{anchor}追索者'
    counterpart_name = f'{anchor}守门人'
    clue_title = f'{anchor}异常记录'
    style_note = f'{variant}、克制而具象'
    if '写作风格手册参考' in prompt:
        style_note += '，吸收用户提供的抽象风格维度'
    generation_notes = [f'以“{brief}”为核心前提扩展世界规则、角色冲突和首章切口。']
    if variant_match:
        generation_notes.append(f'本候选采用“{variant}”方向，与其他候选保持可比较差异。')
    if 'Import Node 候选素材' in prompt:
        generation_notes.append('已将候选素材仅作为只读灵感，输出保持原创且未升级为正史。')
    return WorldCreationDraftPayload.model_validate({
        'draft': {
            'title': title,
            'genre_template': genre,
            'truth_canon': f'{brief}。这个前提构成公开秩序，但其代价和例外仍被掌权者隐瞒。',
            'tone_profile': {
                'style': style_note,
                'pacing': '以异常事件冷启动，逐步转入关系对抗',
                'theme': '个体选择如何撬动被维护的秩序',
            },
            'starter_assets': {
                'characters': [
                    {
                        'name': protagonist_name,
                        'role_type': 'protagonist',
                        'status': 'active',
                        'public_profile': {
                            'identity': f'{anchor}现象的一线记录者',
                            'skill': '从异常细节中还原事件顺序',
                            'public_motivation': f'保护受{anchor}规则影响的人',
                        },
                        'hidden_traits': {
                            'secret': f'曾亲手隐去一份{anchor}记录',
                            'fear': '真相会证明自己也是秩序的共犯',
                            'private_agenda': f'找到{clue_title}的原始版本',
                            'weakness': '在证据不足时仍会独自承担风险',
                        },
                        'destiny_flag': f'{anchor}规则的例外者',
                        'current_goals': [f'查明{clue_title}为何被篡改', f'阻止下一次{anchor}异常伤害无辜者'],
                    },
                    {
                        'name': counterpart_name,
                        'role_type': 'rival',
                        'status': 'active',
                        'public_profile': {
                            'identity': f'{anchor}秩序的执行者',
                            'skill': '控制档案与通行权限',
                            'public_motivation': '避免公开秩序立即崩塌',
                        },
                        'hidden_traits': {
                            'secret': f'知道{clue_title}被修改的原因',
                            'fear': '旧规则失效后无人能承担代价',
                            'private_agenda': f'在追索者找到原件前封存{clue_title}',
                            'weakness': '把控制误当成保护',
                        },
                        'destiny_flag': f'{anchor}旧秩序的守门人',
                        'current_goals': [f'阻止{protagonist_name}公开{clue_title}'],
                    },
                ],
                'relations': [
                    {
                        'source_index': 0,
                        'target_index': 1,
                        'relation_type': 'mutual_suspicion',
                        'intensity': 4,
                        'visibility': 'private',
                    }
                ],
                'foreshadows': [
                    {
                        'title': clue_title,
                        'description': f'一份与“{brief}”公开说法不一致的记录，边缘留有被二次封存的痕迹。',
                        'foreshadow_type': 'rule_exception_clue',
                        'status': 'planted',
                        'urgency_level': 5,
                        'related_character_indexes': [0, 1],
                        'expected_resolution_window': '第2-4章',
                    }
                ],
            },
        },
        'first_chapter_goal': (
            f'让{protagonist_name}在处理一次{anchor}异常时发现{clue_title}，'
            f'并在{counterpart_name}封锁现场前决定保留证据。'
        ),
        'generation_notes': generation_notes[:3],
        'safety_notes': ['当前结果只是可编辑草稿；用户确认前不会创建世界、写入 canon 或推进正史。'],
        'followup_questions': [f'你希望{protagonist_name}先保护一个具体的人，还是先公开{clue_title}？'],
    })


def _mock_paragraph_revision(messages: list[dict[str, str]]) -> ParagraphRevision:
    prompt = _last_user_prompt(messages)
    match = re.fullmatch(
        r'世界设定：(.*?)\n章节标题：(.*?)\n修订模式：(.*?)\n用户指令：(.*?)\n待修订段落：(.*)',
        prompt,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError('MODEL_RESPONSE_INVALID')

    mode = match.group(3).strip()
    instruction = re.sub(r'\s+', ' ', match.group(4)).strip()
    paragraph = match.group(5).strip()
    if mode not in {'rewrite', 'polish'} or not paragraph:
        raise ValueError('MODEL_RESPONSE_INVALID')

    mode_label = '重写' if mode == 'rewrite' else '润色'
    direction = instruction if instruction and instruction != '无' else f'完成{mode_label}并保持原意'
    return ParagraphRevision(
        paragraph=f'{paragraph}（{mode_label}要求：{direction}）',
        revision_note=f'已按{mode_label}模式处理当前段落。',
    )


def _contextual_mock_revision(messages: list[dict[str, str]]) -> ChapterGeneration | None:
    context = _parse_report_context(messages)
    if not context['world_title'] or not context['current_content']:
        return None
    context['chapter_goal'] = context['chapter_goal'] or context['chapter_title'] or '推进当前章节冲突'
    pov = _mock_pov(context)
    foreshadow = context['foreshadows'][0] if context['foreshadows'] else None
    instruction = context['instruction'] or '保持当前冲突并提高可读性。'
    if context.get('opening_contract'):
        base = _contextual_mock_chapter(context)
        revised_content = (
            f"{base.draft_content}\n\n原稿保留片段：{context['current_content']}"
            f"\n\n人工修订指令已落实：{instruction}"
        )
        payload = base.model_dump()
        payload.update({
            'title': f"{context['chapter_title'] or base.title}（修订版）",
            'draft_content': revised_content,
            'context_summary': f"依据当前正文与人工指令完成首章整稿修订：{instruction}",
            'review_hints': [f'复核人工修订指令是否完整落实：{instruction}'],
        })
        return ChapterGeneration.model_validate(payload)

    actor = pov['name'] if pov else '当前行动者'
    clue = foreshadow['name'] if foreshadow else '当前线索'
    return ChapterGeneration.model_validate({
        'title': f"{context['chapter_title'] or clue}（修订版）",
        'draft_content': (
            f"{context['current_content']}\n\n"
            f"修订落实：{instruction} {actor}围绕{clue}重新选择行动顺序，并让后续冲突直接承接当前正文。"
        ),
        'context_summary': f"依据当前正文、{actor}与人工指令完成整稿修订。",
        'review_hints': [f'重新检查{actor}、{clue}与人工指令的一致性。'],
        'proposed_character_changes': ([{
            'character_id': pov['id'],
            'status': f'已按修订指令推进：{instruction}',
            'current_goals': pov['goals'] or [context['chapter_goal']],
        }] if pov else []),
        'proposed_foreshadow_changes': ([{
            'foreshadow_id': foreshadow['id'],
            'status': 'advanced',
            'description_note': f'{clue}已按当前修订指令继续推进。',
        }] if foreshadow else []),
        'opening_evidence': [],
    })


def _contextual_mock_critique(messages: list[dict[str, str]]) -> CritiqueReport | None:
    context = _parse_report_context(messages)
    if not context['current_content']:
        return None
    names = [character['name'] for character in context['characters']]
    cast = '、'.join(names) or '当前行动者'
    clue = context['foreshadows'][0]['name'] if context['foreshadows'] else '当前线索'
    excerpt = re.sub(r'\s+', ' ', context['current_content'])[:80]
    return CritiqueReport.model_validate({
        'score': 84,
        'issues': [
            {
                'category': 'pacing',
                'severity': 'medium',
                'message': f'{cast}围绕{clue}的转折可再增加一个动作铺垫；当前正文片段为“{excerpt}”。',
            }
        ],
        'suggestions': [f'让{cast}在触碰{clue}前先暴露一次判断代价。'],
        'consistency_check': {
            'character_voice': f'{cast}的行动目标与当前输入一致',
            'foreshadow_usage': f'{clue}已进入当前场景',
            'world_rule_adherence': context['world_canon'] or '未提供额外世界规则',
            'pacing': 'needs_minor_revision',
        },
    })


def _contextual_mock_literary_critic(messages: list[dict[str, str]]) -> LiteraryCriticReport | None:
    context = _parse_report_context(messages)
    if not context['current_content']:
        return None
    names = [character['name'] for character in context['characters']]
    cast = '、'.join(names) or '当前行动者'
    clue = context['foreshadows'][0]['name'] if context['foreshadows'] else '当前线索'
    excerpt = re.sub(r'\s+', ' ', context['current_content'])[:80]
    dimension_labels = {
        'pacing': '节奏',
        'tension': '张力',
        'character_consistency': '人物一致性',
        'dialogue_quality': '对白质量',
        'structure': '结构',
        'world_continuity': '世界连续性',
        'readability': '可读性',
    }
    issue = {
        'severity': 'medium',
        'dimension': 'pacing',
        'message': f'{cast}与{clue}的交锋略快，需让“{excerpt}”之后的选择获得更清晰的因果停顿。',
        'paragraph_index': 0,
        'suggested_action': f'补充{cast}确认{clue}风险的动作。',
    }
    dimensions = {
        key: {
            'score': 82 if key != 'dialogue_quality' else 78,
            'summary': f'{label}围绕{cast}、{clue}和当前正文保持一致。',
            'issues': [issue] if key == 'pacing' else [],
            'suggestions': [f'继续用{clue}推动{label}，避免引入无关角色或设定。'],
        }
        for key, label in dimension_labels.items()
    }
    return LiteraryCriticReport.model_validate({
        'overall_score': 82,
        'summary': f'{context["chapter_title"] or "当前章节"}以{cast}和{clue}为中心，结构清晰但转折仍可增加铺垫。',
        'dimensions': dimensions,
        'issues': [issue],
        'suggestions': [f'优先调整{cast}面对{clue}时的动作节奏。'],
    })


def _contextual_mock_character_arc(messages: list[dict[str, str]]) -> CharacterArcReport | None:
    context = _parse_report_context(messages)
    if not context['world_title'] or '请分析本章角色弧线推进' not in context['prompt']:
        return None
    content = context['current_content']
    foreshadow_ids = [foreshadow['id'] for foreshadow in context['foreshadows']]
    clue = context['foreshadows'][0]['name'] if context['foreshadows'] else '当前冲突'
    character_arcs = []
    for character in context['characters']:
        mentioned = character['name'] in content
        character_arcs.append({
            'character_id': character['id'],
            'name': character['name'],
            'role_type': character['role'] or None,
            'current_status': character['status'] or None,
            'current_goals': character['goals'],
            'presence_level': 'major' if mentioned else 'mentioned',
            'arc_stage': 'choice' if mentioned else 'setup',
            'chapter_function': f"围绕{clue}承担{character['role'] or '当前角色'}功能。",
            'observed_shift': f"{character['name']}从维持原目标转向回应{clue}带来的新压力。",
            'proposed_state_change': {'status': f'已回应{clue}'},
            'continuity_risk': 'low' if mentioned else 'medium',
            'risk_reason': None if mentioned else f"正文对{character['name']}的直接行动证据较少。",
            'suggested_revision': f"保留{character['name']}与{clue}之间可见的因果动作。",
            'next_chapter_setup': f"让{character['name']}承担一次围绕{clue}的明确选择。",
        })
    by_id = {character['id']: character for character in context['characters']}
    relationship_notes = []
    for relation in context['relations']:
        source = by_id.get(relation['source_id'])
        target = by_id.get(relation['target_id'])
        if source is None or target is None:
            continue
        relationship_notes.append({
            'source_character_id': source['id'],
            'target_character_id': target['id'],
            'source_name': source['name'],
            'target_name': target['name'],
            'relation_type': relation['type'],
            'current_intensity': relation['intensity'],
            'visibility': relation['visibility'],
            'chapter_shift': f"{source['name']}与{target['name']}因{clue}增加了一层互相试探。",
            'progression_hint': f"下一章让两人围绕{clue}交换一项不对等信息。",
            'risk_level': 'low',
            'risk_reason': None,
        })
    character_ids = [character['id'] for character in context['characters']]
    progression_hints = []
    if character_ids or foreshadow_ids:
        progression_hints.append({
            'hint_type': 'character' if character_ids else 'foreshadow',
            'priority': 'high',
            'title': f'让当前角色围绕{clue}作出不可撤回的选择',
            'rationale': f'{context["world_title"]}当前章节已经把{clue}带入冲突。',
            'suggested_next_beat': f'下一章直接承接正文，让{clue}迫使角色改变行动顺序。',
            'related_character_ids': character_ids,
            'related_foreshadow_ids': foreshadow_ids,
            'can_seed_next_chapter_goal': True,
        })
    names = '、'.join(character['name'] for character in context['characters']) or '当前世界'
    return CharacterArcReport.model_validate({
        'summary': f'{names}在{context["world_title"]}围绕{clue}形成了可延续的角色压力。',
        'character_arcs': character_arcs,
        'relationship_notes': relationship_notes,
        'progression_hints': progression_hints,
    })


@dataclass(frozen=True)
class LLMUsageContext:
    db: Session | None = None
    audit_session_factory: AuditSessionFactory | None = None
    request_id: str | None = None
    world_id: int | None = None
    chapter_id: int | None = None
    draft_id: int | None = None


def _serialized_output_chars(value: Any) -> int:
    model_dump = getattr(value, 'model_dump', None)
    if callable(model_dump):
        value = model_dump(mode='json')
    try:
        return len(json.dumps(value, ensure_ascii=False, separators=(',', ':'), default=str))
    except (TypeError, ValueError):
        return len(str(value))


def _audit_mock_call(
    operation: str,
    messages_builder: Callable[..., list[dict[str, str]]] | None = None,
):
    def decorator(method):
        @wraps(method)
        def wrapped(self, messages, *args, **kwargs):
            if not self.mock:
                return method(self, messages, *args, **kwargs)
            audit_messages = messages
            if messages_builder is not None:
                audit_messages = messages_builder(messages, *args, **kwargs)
            started_at = perf_counter()
            try:
                result = method(self, messages, *args, **kwargs)
            except Exception as exc:
                self._record_usage(
                    operation=operation,
                    messages=audit_messages,
                    started_at=started_at,
                    status='failed',
                    attempt_count=1,
                    error_code=safe_error_code(exc),
                )
                raise
            self._record_usage(
                operation=operation,
                messages=audit_messages,
                started_at=started_at,
                status='success',
                attempt_count=1,
                output_chars=_serialized_output_chars(result),
            )
            return result

        return wrapped

    return decorator


class LLMClient:
    def __init__(self, settings: Settings | None = None, mock: bool | None = None) -> None:
        self.settings = settings or get_settings()
        self.mock = self.settings.llm_mock if mock is None else mock
        self._usage_context = LLMUsageContext()

    def configure_usage_context(
        self,
        *,
        db: Session | None = None,
        audit_session_factory: AuditSessionFactory | None = None,
        request_id: str | None = None,
        world_id: int | None = None,
        chapter_id: int | None = None,
        draft_id: int | None = None,
    ) -> None:
        self._usage_context = LLMUsageContext(
            db=db,
            audit_session_factory=audit_session_factory,
            request_id=request_id,
            world_id=world_id,
            chapter_id=chapter_id,
            draft_id=draft_id,
        )

    def _provider_name(self) -> str:
        if self.mock:
            return 'mock'
        return urlsplit(str(self.settings.llm_base_url)).hostname or 'unknown'

    @staticmethod
    def _input_chars(messages: list[dict[str, str]]) -> int:
        return sum(
            len(message.get('content', ''))
            for message in messages
            if isinstance(message.get('content'), str)
        )

    def _response_provenance(
        self,
        url: str,
        response: Any = None,
        payload: Any = None,
        *,
        json_object: bool,
        json_schema: dict | None,
        use_json_object: bool,
        retry_reason: str | None,
    ) -> dict[str, Any]:
        if json_schema is not None and not use_json_object:
            response_format = 'json_schema'
        elif json_object or use_json_object:
            response_format = 'json_object'
        else:
            response_format = 'none'
        provenance: dict[str, Any] = {
            'endpoint': urlsplit(url).path or '/',
            'schema_mode': response_format,
            'response_format': response_format,
        }
        if json_schema is not None:
            provenance['schema_name'] = 'world_creation_draft_v1'
        if retry_reason:
            provenance['retry_reason'] = retry_reason

        headers = getattr(response, 'headers', None)
        if headers is not None:
            provider_request_id = headers.get('x-request-id') or headers.get('request-id')
            if isinstance(provider_request_id, str) and provider_request_id:
                provenance['provider_request_id'] = provider_request_id
        if isinstance(payload, dict):
            response_id = payload.get('id') or payload.get('response_id')
            if isinstance(response_id, str) and response_id:
                provenance['response_id'] = response_id
            if 'provider_request_id' not in provenance:
                provider_request_id = payload.get('provider_request_id') or payload.get('request_id')
                if isinstance(provider_request_id, str) and provider_request_id:
                    provenance['provider_request_id'] = provider_request_id
            finish_reason = payload.get('finish_reason')
            choices = payload.get('choices')
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                finish_reason = choices[0].get('finish_reason') or finish_reason
            if isinstance(finish_reason, str) and finish_reason:
                provenance['finish_reason'] = finish_reason
        return provenance

    def _record_usage(
        self,
        *,
        operation: str,
        messages: list[dict[str, str]],
        started_at: float,
        status: str,
        attempt_count: int,
        schema_fallback_used: bool = False,
        http_status: int | None = None,
        output_chars: int = 0,
        usage: dict[str, int | None] | None = None,
        error_code: str | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> None:
        context = self._usage_context
        if context.db is None and context.audit_session_factory is None:
            return
        token_usage = usage or {}
        try:
            record_llm_usage(
                context.db,
                session_factory=context.audit_session_factory,
                operation=operation,
                provider=self._provider_name(),
                api_mode=self.settings.llm_api_mode,
                model=self.settings.llm_model,
                is_mock=bool(self.mock),
                status=status,
                duration_ms=max(0, int(round((perf_counter() - started_at) * 1000))),
                attempt_count=attempt_count,
                schema_fallback_used=schema_fallback_used,
                world_id=context.world_id,
                chapter_id=context.chapter_id,
                draft_id=context.draft_id,
                http_status=http_status,
                input_message_count=len(messages),
                input_chars=self._input_chars(messages),
                output_chars=max(0, output_chars),
                input_tokens=token_usage.get('input_tokens'),
                output_tokens=token_usage.get('output_tokens'),
                total_tokens=token_usage.get('total_tokens'),
                error_code=error_code,
                request_id=context.request_id,
                provenance=provenance,
            )
        except Exception:
            return

    def _post_json_for_operation(
        self,
        messages: list[dict[str, str]],
        *,
        operation: str,
        success_validator: Callable[[str], Any] | None = None,
        **kwargs: Any,
    ) -> str:
        post_json = self._post_json
        call_kwargs: dict[str, Any] = {
            **kwargs,
            'operation': operation,
            'success_validator': success_validator,
        }
        try:
            parameters = inspect.signature(post_json).parameters
        except (TypeError, ValueError):
            return post_json(messages, **call_kwargs)
        if any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()):
            return post_json(messages, **call_kwargs)
        supported_kwargs = {
            name: value for name, value in call_kwargs.items() if name in parameters
        }
        return post_json(messages, **supported_kwargs)

    def _post_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        json_object: bool = True,
        json_schema: dict | None = None,
        allow_json_object_fallback: bool = False,
        operation: str = 'llm_request',
        success_validator: Callable[[str], Any] | None = None,
    ) -> str:
        started_at = perf_counter()
        base_url = str(self.settings.llm_base_url).rstrip('/')
        is_responses = self.settings.llm_api_mode == 'responses'
        url = f'{base_url}/responses' if is_responses else f'{base_url}/chat/completions'
        timeout = httpx.Timeout(
            connect=self.settings.llm_timeout_seconds,
            read=self.settings.llm_read_timeout_seconds,
            write=self.settings.llm_timeout_seconds,
            pool=self.settings.llm_timeout_seconds,
        )
        use_json_object = False
        schema_fallback_used = False
        retry_reason = None
        attempt_count = 0
        http_status = None
        response = None
        payload = None
        usage = None
        content: str | None = None

        def build_request_payload(use_json_object: bool) -> dict:
            if is_responses:
                payload = {
                    'model': self.settings.llm_model,
                    'input': messages,
                    'temperature': temperature,
                    'store': False,
                }
                if json_schema is not None and not use_json_object:
                    payload['text'] = {
                        'format': {
                            'type': 'json_schema',
                            'name': 'world_creation_draft_v1',
                            'strict': True,
                            'schema': json_schema,
                        },
                    }
                elif json_object:
                    payload['text'] = {'format': {'type': 'json_object'}}
                return payload

            payload = {
                'model': self.settings.llm_model,
                'messages': messages,
                'temperature': temperature,
            }
            if json_schema is not None and not use_json_object:
                payload['response_format'] = {
                    'type': 'json_schema',
                    'json_schema': {
                        'name': 'world_creation_draft_v1',
                        'strict': True,
                        'schema': json_schema,
                    },
                }
            elif json_object:
                payload['response_format'] = {'type': 'json_object'}
            return payload

        import time
        import random as _random
        try:
            for attempt in range(3):
                attempt_count = attempt + 1
                try:
                    response = httpx.post(
                        url,
                        headers={'Authorization': f'Bearer {self.settings.llm_api_key}'},
                        json=build_request_payload(use_json_object),
                        timeout=timeout,
                    )
                    response_status = getattr(response, 'status_code', None)
                    http_status = response_status if isinstance(response_status, int) else None
                    response.raise_for_status()
                    break
                except httpx.TimeoutException as exc:
                    raise TimeoutError('MODEL_TIMEOUT') from exc
                except httpx.HTTPStatusError as exc:
                    response = exc.response
                    http_status = exc.response.status_code
                    # Exponential backoff for rate limits (429) and server errors (5xx)
                    if attempt < 2 and http_status in (429, 502, 503, 504):
                        wait = (2 ** attempt) + _random.uniform(0, 1)
                        _retry_logger = __import__('logging').getLogger('worldsim.llm')
                        _retry_logger.info(
                            'llm_retry_backoff',
                            extra={
                                'event': 'llm.retry',
                                'attempt': attempt_count,
                                'status': http_status,
                                'wait_seconds': round(wait, 2),
                            },
                        )
                        time.sleep(wait)
                        continue
                    error_text = exc.response.text[:2000].casefold()
                    schema_format_mentioned = any(
                        marker in error_text
                        for marker in ('json_schema', 'strict', 'response_format', 'text.format')
                    )
                    invalid_schema_mentioned = any(
                        marker in error_text
                        for marker in (
                            'invalid schema',
                            'invalid json schema',
                            'invalid_json_schema',
                            'schema is invalid',
                            'schema invalid',
                            'schema validation',
                            'malformed schema',
                            'malformed response_format',
                            'unsupported keyword',
                            'invalid parameter',
                            'unknown property',
                            'unrecognized property',
                        )
                    )
                    unsupported_mentioned = any(
                        marker in error_text
                        for marker in ('not supported', 'unsupported')
                    ) or any(
                        marker in error_text
                        for marker in (
                            'unknown parameter',
                            'unrecognized parameter',
                            'unknown field',
                            'unrecognized field',
                            'unknown response_format',
                            'unrecognized response_format',
                            'unknown json_schema',
                            'unrecognized json_schema',
                        )
                    )
                    if (
                        attempt == 0
                        and allow_json_object_fallback
                        and json_schema is not None
                        and exc.response.status_code == 400
                        and schema_format_mentioned
                        and unsupported_mentioned
                        and not invalid_schema_mentioned
                    ):
                        schema_fallback_used = True
                        retry_reason = 'schema_unsupported'
                        use_json_object = True
                        continue
                    if exc.response.status_code in {401, 403}:
                        raise RuntimeError('MODEL_AUTH_FAILED') from exc
                    if exc.response.status_code == 429:
                        raise RuntimeError('MODEL_RATE_LIMITED') from exc
                    raise RuntimeError('MODEL_REQUEST_FAILED') from exc
                except httpx.HTTPError as exc:
                    response = getattr(exc, 'response', None)
                    response_status = getattr(response, 'status_code', None)
                    http_status = response_status if isinstance(response_status, int) else None
                    raise RuntimeError('MODEL_REQUEST_FAILED') from exc

            if response is None:
                raise RuntimeError('MODEL_REQUEST_FAILED')
            try:
                payload = response.json()
            except ValueError as exc:
                raise ValueError('MODEL_RESPONSE_INVALID') from exc
            if not isinstance(payload, dict):
                raise ValueError('MODEL_RESPONSE_INVALID')
            usage = extract_provider_usage(payload)
            provenance = self._response_provenance(
                url,
                response,
                payload,
                json_object=json_object,
                json_schema=json_schema,
                use_json_object=use_json_object,
                retry_reason=retry_reason,
            )

            def finish_content(value: str) -> str:
                if success_validator is not None:
                    success_validator(value)
                self._record_usage(
                    operation=operation,
                    messages=messages,
                    started_at=started_at,
                    status='success',
                    attempt_count=attempt_count,
                    schema_fallback_used=schema_fallback_used,
                    http_status=http_status,
                    output_chars=len(value),
                    usage=usage,
                    provenance=provenance,
                )
                return value

            if self.settings.llm_api_mode == 'chat_completions':
                choices = payload.get('choices')
                if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                    raise ValueError('MODEL_RESPONSE_INVALID')
                message = choices[0].get('message')
                if not isinstance(message, dict):
                    raise ValueError('MODEL_RESPONSE_INVALID')
                if message.get('refusal'):
                    raise ValueError('MODEL_RESPONSE_INVALID')
                content = message.get('content')
                if not isinstance(content, str) or not content:
                    raise ValueError('MODEL_RESPONSE_INVALID')
                return finish_content(content)

            output_texts: list[str] = []
            refusal_present = False
            output = payload.get('output')
            if isinstance(output, list):
                for item in output:
                    if not isinstance(item, dict) or item.get('type') != 'message':
                        continue
                    content = item.get('content')
                    if not isinstance(content, list):
                        continue
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        if part.get('type') == 'refusal':
                            refusal_present = True
                            continue
                        if part.get('type') != 'output_text':
                            continue
                        text = part.get('text')
                        if isinstance(text, str) and text:
                            output_texts.append(text)
            if refusal_present:
                raise ValueError('MODEL_RESPONSE_INVALID')
            if output_texts:
                content = ''.join(output_texts)
                return finish_content(content)

            fallback_output_text = payload.get('output_text')
            if isinstance(fallback_output_text, str) and fallback_output_text:
                content = fallback_output_text
                return finish_content(content)
            raise ValueError('MODEL_RESPONSE_INVALID')
        except Exception as exc:
            self._record_usage(
                operation=operation,
                messages=messages,
                started_at=started_at,
                status='failed',
                attempt_count=max(1, attempt_count),
                schema_fallback_used=schema_fallback_used,
                http_status=http_status,
                output_chars=len(content) if isinstance(content, str) else 0,
                usage=usage,
                error_code=safe_error_code(exc),
                provenance=self._response_provenance(
                    url,
                    response,
                    payload,
                    json_object=json_object,
                    json_schema=json_schema,
                    use_json_object=use_json_object,
                    retry_reason=retry_reason,
                ),
            )
            raise

    @_audit_mock_call('story_arc')
    def generate_story_arc(self, messages: list[dict[str, str]]) -> list[StoryArcChapter]:
        if self.mock:
            contextual = _contextual_mock_story_arc(messages)
            if contextual is not None:
                return contextual
            _raise_for_unparseable_context(messages)
            return parse_story_arc(json.dumps(MOCK_STORY_ARC, ensure_ascii=False))
        return parse_story_arc(
            self._post_json_for_operation(
                messages,
                temperature=0.4,
                json_object=False,
                operation='story_arc',
                success_validator=parse_story_arc,
            )
        )

    @_audit_mock_call('chapter_outline')
    def generate_outline(self, messages: list[dict[str, str]]) -> ChapterOutline:
        if self.mock:
            context = _parse_mock_prompt(messages)
            if context is not None:
                return _contextual_mock_outline(context)
            _raise_for_unparseable_context(messages)
            return ChapterOutline.model_validate(MOCK_OUTLINE)
        return parse_chapter_outline(
            self._post_json_for_operation(
                messages,
                temperature=0.4,
                operation='chapter_outline',
                success_validator=parse_chapter_outline,
            )
        )

    @_audit_mock_call('literary_review')
    def generate_literary_review(self, messages: list[dict[str, str]]) -> LiteraryReviewReport:
        if self.mock:
            return LiteraryReviewReport(
                literary_score=3,
                over_explaining=['（mock）解释过度占位'],
                emotional_telling=[],
                functional_dialogue=[],
                cliche_hooks=[],
                voice_notes=[],
                rewrite_suggestions=[],
            )
        return parse_literary_review(
            self._post_json_for_operation(
                messages,
                temperature=0.1,
                operation='literary_review',
                success_validator=parse_literary_review,
            )
        )

    @_audit_mock_call('quality_engine')
    def generate_quality_report(self, messages: list[dict[str, str]]) -> ChapterQualityReport:
        if self.mock:
            return ChapterQualityReport(
                theme_advancement=3,
                character_arc_progress=3,
                anti_cliche_risks=['（mock）俗套风险占位'],
                rhythm_score=3,
                voice_consistency=3,
                overall_score=3,
            )
        return parse_quality_report(
            self._post_json_for_operation(
                messages,
                temperature=0.2,
                operation='quality_engine',
                success_validator=parse_quality_report,
            )
        )

    @_audit_mock_call('memory_compression')
    def compress_memories(self, messages: list[dict[str, str]]) -> MemoryCompression:
        if self.mock:
            return MemoryCompression(
                summary='（mock）前情摘要：角色们在安全区周边活动，关系与伏笔持续发展。',
                key_facts=['（mock）关键事实占位'],
                open_threads=['（mock）开放线索占位'],
            )
        return parse_memory_compression(
            self._post_json_for_operation(
                messages,
                temperature=0.3,
                operation='memory_compression',
                success_validator=parse_memory_compression,
            )
        )

    @_audit_mock_call('world_creation_draft')
    def generate_world_creation_draft(self, messages: list[dict[str, str]]) -> WorldCreationDraftPayload:
        if self.mock:
            return _contextual_mock_world_creation(messages)
        return parse_world_creation_draft(
            self._post_json_for_operation(
                messages,
                temperature=0.5,
                json_schema=WORLD_CREATION_DRAFT_JSON_SCHEMA,
                allow_json_object_fallback=True,
                operation='world_creation_draft',
                success_validator=parse_world_creation_draft,
            ),
        )

    @_audit_mock_call('opening_evidence_repair', _opening_evidence_repair_messages)
    def repair_opening_evidence(
        self,
        messages: list[dict[str, str]],
        content: str,
        opening_evidence: list[OpeningEvidence],
    ) -> list[OpeningEvidence]:
        if self.mock:
            return _mock_opening_evidence_repair(content, opening_evidence)
        repaired = parse_opening_evidence_repair(
            self._post_json_for_operation(
                _opening_evidence_repair_messages(messages, content, opening_evidence),
                temperature=0.0,
                operation='opening_evidence_repair',
                success_validator=parse_opening_evidence_repair,
            )
        )
        return repaired.opening_evidence

    def _repair_opening_evidence_once(
        self,
        messages: list[dict[str, str]],
        generation: ChapterGeneration,
    ) -> ChapterGeneration:
        if not _looks_like_opening_prompt(messages) or not _opening_evidence_needs_repair(
            generation.draft_content,
            generation.opening_evidence,
        ):
            return generation
        try:
            repaired_evidence = self.repair_opening_evidence(
                messages,
                generation.draft_content,
                generation.opening_evidence,
            )
        except (TimeoutError, ValueError, RuntimeError):
            return generation
        if not _opening_evidence_needs_repair(generation.draft_content, repaired_evidence):
            return generation.model_copy(update={'opening_evidence': repaired_evidence})
        return generation

    DRAFT_CONTENT_PLACEHOLDER = '<<<DRAFT_CONTENT_PLACEHOLDER>>>'

    def generate_chapter_two_phase(
        self,
        writer_messages: list[dict[str, str]],
        extractor_messages: list[dict[str, str]],
    ) -> ChapterGeneration:
        """Generate a chapter in two phases: prose first, then structured extraction.

        Phase 1: Generate pure narrative prose (no JSON constraint).
        Phase 2: Feed the prose to an extractor that returns structured metadata.

        The extractor_messages should contain DRAFT_CONTENT_PLACEHOLDER where the
        generated prose should be inserted. This placeholder is replaced after
        phase 1 completes.

        This separation improves reliability because:
        - The Writer can focus on literary quality without JSON formatting pressure.
        - The Extractor sees the final text and can produce accurate quotes/evidence.
        - If one phase fails, we can retry just that phase.
        """
        if self.mock:
            context = _parse_mock_prompt(writer_messages)
            if context is not None:
                return _contextual_mock_chapter(context)
            _raise_for_unparseable_context(writer_messages)
            return ChapterGeneration.model_validate(dict(MOCK_CHAPTER))

        # Phase 1: Generate prose only
        prose_response = self._post_json_for_operation(
            writer_messages,
            temperature=0.7,
            json_object=False,
            operation='chapter_generation_prose',
        )

        # Substitute the generated prose into the extraction messages
        populated_extraction_messages = [
            {
                **msg,
                'content': msg['content'].replace(
                    self.DRAFT_CONTENT_PLACEHOLDER, prose_response
                ),
            }
            for msg in extractor_messages
        ]

        # Phase 2: Extract structured metadata from the prose
        try:
            extraction = parse_chapter_extraction(
                self._post_json_for_operation(
                    populated_extraction_messages,
                    temperature=0.2,
                    operation='chapter_generation_extraction',
                    success_validator=parse_chapter_extraction,
                )
            )
            return ChapterGeneration.model_validate({
                **extraction.model_dump(),
                'title': f'第{context.get("chapter_number", "?")}章' if (
                    context := _parse_mock_prompt(writer_messages)
                ) else '未命名章节',
                'draft_content': prose_response,
            })
        except ValueError:
            import logging
            _extraction_logger = logging.getLogger('worldsim.llm')
            _extraction_logger.warning(
                'chapter_generation_extraction_failed: prose saved, metadata empty'
            )
            return ChapterGeneration.model_validate({
                'title': '未命名章节',
                'draft_content': prose_response,
                'context_summary': '（自动提取失败，请手动填写摘要）',
                'review_hints': ['自动提取失败：正文已保留，请手动审核并编辑元数据。'],
                'proposed_character_changes': [],
                'proposed_foreshadow_changes': [],
                'opening_evidence': [],
            })

    @_audit_mock_call('chapter_generation')
    def generate_chapter(self, messages: list[dict[str, str]]) -> ChapterGeneration:
        if self.mock:
            context = _parse_mock_prompt(messages)
            if context is not None:
                return _contextual_mock_chapter(context)
            _raise_for_unparseable_context(messages)

            user_msg = _last_user_prompt(messages)
            char_match = re.search(r'角色：\n(.+?)(?=\n伏笔：)', user_msg, re.DOTALL)
            fore_match = re.search(r'伏笔：\n(.+?)(?=\n本章目标：)', user_msg, re.DOTALL)
            char_id = 1
            fore_id = 1
            if char_match:
                char_lines = char_match.group(1).strip().split('\n')
                if char_lines:
                    char_id = int(char_lines[0].split(':')[0].replace('- ', ''))
            if fore_match:
                fore_lines = fore_match.group(1).strip().split('\n')
                if fore_lines:
                    fore_id = int(fore_lines[0].split(':')[0].replace('- ', ''))
            mock_data = dict(MOCK_CHAPTER)
            mock_data['proposed_character_changes'] = [
                {"character_id": char_id, "status": "获得预言古书，面临三日抉择", "current_goals": ["破解古书预言", "探查城主府密道", "保护灵脉"]}
            ]
            mock_data['proposed_foreshadow_changes'] = [
                {"foreshadow_id": fore_id, "status": "advanced", "description_note": "玉佩与古书产生共鸣，暗示两者关联"}
            ]
            return ChapterGeneration.model_validate(mock_data)

        generation = parse_chapter_generation(
            self._post_json_for_operation(
                messages,
                temperature=0.7,
                operation='chapter_generation',
                success_validator=parse_chapter_generation,
            )
        )
        return self._repair_opening_evidence_once(messages, generation)

    @_audit_mock_call('chapter_revision')
    def revise_chapter(self, messages: list[dict[str, str]]) -> ChapterGeneration:
        if self.mock:
            contextual = _contextual_mock_revision(messages)
            if contextual is not None:
                return contextual
            _raise_for_unparseable_context(messages)
            mock_data = dict(MOCK_CHAPTER)
            mock_data['title'] = f"{mock_data['title']}（修订版）"
            mock_data['draft_content'] = f"修订版：{mock_data['draft_content']}"
            mock_data['context_summary'] = '根据审稿意见和人工指令完成整稿修订。'
            mock_data['review_hints'] = ['重新生成 Critic 报告确认修订效果']
            return ChapterGeneration.model_validate(mock_data)
        return parse_chapter_generation(
            self._post_json_for_operation(
                messages,
                temperature=0.6,
                operation='chapter_revision',
                success_validator=parse_chapter_generation,
            )
        )

    @_audit_mock_call('paragraph_revision')
    def revise_paragraph(self, messages: list[dict[str, str]]) -> ParagraphRevision:
        if self.mock:
            return _mock_paragraph_revision(messages)
        return parse_paragraph_revision(
            self._post_json_for_operation(
                messages,
                temperature=0.6,
                operation='paragraph_revision',
                success_validator=parse_paragraph_revision,
            )
        )

    @_audit_mock_call('chapter_goal_suggestion')
    def suggest_goal(self, messages: list[dict[str, str]]) -> dict:
        if self.mock:
            contextual = _contextual_mock_goal(messages)
            if contextual is not None:
                return contextual
            _raise_for_unparseable_context(messages)
            return {'goal': '主角面对当前世界的异常规则，获得新证据并决定下一步行动。'}
        raw = self._post_json_for_operation(
            messages,
            temperature=0.6,
            operation='chapter_goal_suggestion',
            success_validator=json.loads,
        )
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and 'goal' in parsed:
            return {'goal': parsed['goal']}
        return {'goal': raw}

    @_audit_mock_call('chapter_critique')
    def critique_chapter(self, messages: list[dict[str, str]]) -> CritiqueReport:
        if self.mock:
            contextual = _contextual_mock_critique(messages)
            if contextual is not None:
                return contextual
            _raise_for_unparseable_context(messages)
            return CritiqueReport.model_validate(MOCK_CRITIQUE)
        return parse_critique_report(
            self._post_json_for_operation(
                messages,
                temperature=0.2,
                operation='chapter_critique',
                success_validator=parse_critique_report,
            )
        )

    @_audit_mock_call('literary_critic_report')
    def generate_critic_report(self, messages: list[dict[str, str]]) -> LiteraryCriticReport:
        if self.mock:
            contextual = _contextual_mock_literary_critic(messages)
            if contextual is not None:
                return contextual
            _raise_for_unparseable_context(messages)
            return LiteraryCriticReport.model_validate(MOCK_LITERARY_CRITIC)
        return parse_literary_critic_report(
            self._post_json_for_operation(
                messages,
                temperature=0.2,
                operation='literary_critic_report',
                success_validator=parse_literary_critic_report,
            )
        )

    @_audit_mock_call('character_arc_report')
    def generate_character_arc_report(self, messages: list[dict[str, str]]) -> CharacterArcReport:
        if self.mock:
            contextual = _contextual_mock_character_arc(messages)
            if contextual is not None:
                return contextual
            _raise_for_unparseable_context(messages)
            return CharacterArcReport.model_validate(MOCK_CHARACTER_ARC_REPORT)
        return parse_character_arc_report(
            self._post_json_for_operation(
                messages,
                temperature=0.2,
                operation='character_arc_report',
                success_validator=parse_character_arc_report,
            )
        )
