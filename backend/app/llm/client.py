import httpx

from app.core.config import Settings, get_settings
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange, parse_chapter_generation


MOCK_CHAPTER = {
    "title": "雨夜书阁",
    "draft_content": "暮色四合，秋雨如丝。\\n\\n林砚裹紧了外袍，踏过泥泞的青石巷。城主府的灯火在远处明灭不定，像是一只只窥探的眼睛。他已经三天没有合眼了，裂纹玉佩上的纹路日夜在脑海中盘旋。\\n\\n\"这里……\"他停下脚步，看见巷尾有一间从未见过的阁楼。匾额上写着\"忘归书阁\"三个古字，门扉半掩，透出暖黄色的光。\\n\\n推门而入，书卷的气味扑面而来。四面墙壁嵌满了竹简和线装书，中央的檀木桌上，一本古书正散发着幽幽青光。\\n\\n林砚的心跳骤然加快。他伸出手，指尖触碰到书封的瞬间，一股温热的气流顺着手臂涌入胸口。古书自动翻开，第一页赫然写着——\\n\\n\"青岚灵脉，将于三日后断绝。\"\\n\\n他猛地后退一步，目光却被下一页吸引：一幅精细的城主府地图，标注着一条从未见过的密道，直通地下深处。\\n\\n\"你是谁？\"身后传来一个苍老的声音。\\n\\n林砚转身，看见一位白发老者站在门口，手中提着一盏纸灯笼。老人的眼睛浑浊却锐利，仿佛能看穿一切。\\n\\n\"我……我只是避雨。\"林砚下意识地握紧了怀中的玉佩。\\n\\n老者微微一笑：\"避雨的人，不会走进忘归书阁。你身上有它的召唤。\"他指了指桌上的古书，\"拿走吧。它会告诉你真相——关于城主府，关于灵脉，也关于你自己。\"\\n\\n林砚犹豫了片刻，最终还是将古书收入怀中。青光透过衣襟，隐隐可见。\\n\\n\"记住，\"老者在他身后说道，\"三日之后，一切都会改变。选择权在你手中。\"\\n\\n走出书阁时，雨已经停了。林砚回头望去——巷尾空空荡荡，仿佛那间阁楼从未存在过。\\n\\n他深吸一口气，快步消失在夜色中。怀中的古书微微发烫，像是在催促他做出决定。",
    "context_summary": "林砚在雨夜发现神秘书阁，获得一本预言古书。古书记载青岚灵脉将在三日后断绝，并包含城主府密道地图。神秘老者暗示林砚被古书选中，将真相与选择权交到他手中。",
    "review_hints": [
        "裂纹玉佩线索推进：林砚三天未眠，持续关注玉佩纹路",
        "新伏笔引入：忘归书阁和预言古书，三日倒计时开始",
        "城主府叛乱传闻新证据：古书中的密道地图",
        "角色状态变化：林砚从调查者变为被选中者"
    ],
    "proposed_character_changes": [
        {"character_id": 1, "status": "获得预言古书，面临三日抉择", "current_goals": ["破解古书预言", "探查城主府密道", "保护灵脉"]}
    ],
    "proposed_foreshadow_changes": [
        {"foreshadow_id": 1, "status": "advanced", "description_note": "玉佩与古书产生共鸣，暗示两者关联"}
    ]
}


class LLMClient:
    def __init__(self, settings: Settings | None = None, mock: bool = False) -> None:
        self.settings = settings or get_settings()
        self.mock = mock

    def generate_chapter(self, messages: list[dict[str, str]]) -> ChapterGeneration:
        if self.mock:
            # Extract character and foreshadow IDs from the messages
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
        
        base_url = str(self.settings.llm_base_url).rstrip('/')
        try:
            response = httpx.post(
                f'{base_url}/chat/completions',
                headers={'Authorization': f'Bearer {self.settings.llm_api_key}'},
                json={
                    'model': self.settings.llm_model,
                    'messages': messages,
                    'temperature': 0.7,
                    'response_format': {'type': 'json_object'},
                },
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
        return parse_chapter_generation(content)
