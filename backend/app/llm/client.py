import json

import httpx

from app.core.config import Settings, get_settings
from app.llm.schemas import (
    ChapterGeneration,
    ChapterOutline,
    CritiqueReport,
    StoryArcChapter,
    parse_chapter_generation,
    parse_chapter_outline,
    parse_critique_report,
    parse_story_arc,
)


MOCK_CHAPTER = {
    "title": "雨夜书阁",
    "draft_content": "暮色四合，秋雨如丝。\n\n林砚裹紧了外袍，踏过泥泞的青石巷。城主府的灯火在远处明灭不定，像是一只只窥探的眼睛。他已经三天没有合眼了，裂纹玉佩上的纹路日夜在脑海中盘旋。\n\n\"这里……\"他停下脚步，看见巷尾有一间从未见过的阁楼。匾额上写着\"忘归书阁\"三个古字，门扉半掩，透出暖黄色的光。\n\n推门而入，书卷的气味扑面而来。四面墙壁嵌满了竹简和线装书，中央的檀木桌上，一本古书正散发着幽幽青光。\n\n林砚的心跳骤然加快。他伸出手，指尖触碰到书封的瞬间，一股温热的气流顺着手臂涌入胸口。古书自动翻开，第一页赫然写着——\n\n\"青岚灵脉，将于三日后断绝。\"\n\n他猛地后退一步，目光却被下一页吸引：一幅精细的城主府地图，标注着一条从未见过的密道，直通地下深处。\n\n\"你是谁？\"身后传来一个苍老的声音。\n\n林砚转身，看见一位白发老者站在门口，手中提着一盏纸灯笼。老人的眼睛浑浊却锐利，仿佛能看穿一切。\n\n\"我……我只是避雨。\"林砚下意识地握紧了怀中的玉佩。\n\n老者微微一笑：\"避雨的人，不会走进忘归书阁。你身上有它的召唤。\"他指了指桌上的古书，\"拿走吧。它会告诉你真相——关于城主府，关于灵脉，也关于你自己。\"\n\n林砚犹豫了片刻，最终还是将古书收入怀中。青光透过衣襟，隐隐可见。\n\n\"记住，\"老者在他身后说道，\"三日之后，一切都会改变。选择权在你手中。\"\n\n走出书阁时，雨已经停了。林砚回头望去——巷尾空空荡荡，仿佛那间阁楼从未存在过。\n\n他深吸一口气，快步消失在夜色中。怀中的古书微微发烫，像是在催促他做出决定。",
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


class LLMClient:
    def __init__(self, settings: Settings | None = None, mock: bool = False) -> None:
        self.settings = settings or get_settings()
        self.mock = mock

    def _post_json(self, messages: list[dict[str, str]], temperature: float = 0.7, json_object: bool = True) -> str:
        base_url = str(self.settings.llm_base_url).rstrip('/')
        request_payload = {
            'model': self.settings.llm_model,
            'messages': messages,
            'temperature': temperature,
        }
        if json_object:
            request_payload['response_format'] = {'type': 'json_object'}
        try:
            response = httpx.post(
                f'{base_url}/chat/completions',
                headers={'Authorization': f'Bearer {self.settings.llm_api_key}'},
                json=request_payload,
                timeout=self.settings.llm_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError('MODEL_TIMEOUT') from exc
        except httpx.HTTPError as exc:
            raise RuntimeError('MODEL_REQUEST_FAILED') from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError('MODEL_RESPONSE_INVALID') from exc
        if not isinstance(payload, dict):
            raise ValueError('MODEL_RESPONSE_INVALID')
        choices = payload.get('choices', [])
        if not choices or not isinstance(choices[0], dict):
            raise ValueError('MODEL_RESPONSE_INVALID')
        content = choices[0].get('message', {}).get('content')
        if not isinstance(content, str):
            raise ValueError('MODEL_RESPONSE_INVALID')
        return content

    def generate_story_arc(self, messages: list[dict[str, str]]) -> list[StoryArcChapter]:
        if self.mock:
            return parse_story_arc(json.dumps(MOCK_STORY_ARC, ensure_ascii=False))
        return parse_story_arc(self._post_json(messages, temperature=0.4, json_object=False))

    def generate_outline(self, messages: list[dict[str, str]]) -> ChapterOutline:
        if self.mock:
            return ChapterOutline.model_validate(MOCK_OUTLINE)
        return parse_chapter_outline(self._post_json(messages, temperature=0.4))

    def generate_chapter(self, messages: list[dict[str, str]]) -> ChapterGeneration:
        if self.mock:
            import re

            user_msg = messages[-1]['content'] if messages else ''
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
        return parse_chapter_generation(self._post_json(messages, temperature=0.7))

    def critique_chapter(self, messages: list[dict[str, str]]) -> CritiqueReport:
        if self.mock:
            return CritiqueReport.model_validate(MOCK_CRITIQUE)
        return parse_critique_report(self._post_json(messages, temperature=0.2))
