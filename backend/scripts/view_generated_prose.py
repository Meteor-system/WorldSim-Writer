"""Quick script to generate and view chapter prose from real LLM.
Usage: set LLM_MOCK=false && python scripts/view_generated_prose.py
"""
import os, sys, time

os.environ.setdefault('LLM_MOCK', 'false')
os.environ.setdefault('SECRET_KEY', 'view-script-key-12345678')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import get_settings
from app.llm.client import LLMClient
from app.narrative.service import build_writer_only_messages, build_extraction_messages
from app.world.models import World
from app.character.models import Character
from app.foreshadow.models import Foreshadow


def make_world():
    w = World()
    w.id = 0
    w.title = "钟表群岛"
    w.genre_template = "悬疑奇幻"
    w.tone_profile = {"style": "冷峻悬疑", "pacing": "中等", "theme": "秩序与自由"}
    w.truth_canon = "钟表群岛：由发条潮汐维持、每晚会交换岛屿位置的群岛。每个岛屿有一个钟塔，钟塔停摆则岛屿沉没。"
    w.world_version = 1
    return w


def make_characters():
    c1 = Character()
    c1.id = 1
    c1.name = "林澜"
    c1.role_type = "protagonist"
    c1.public_profile = {"identity": "钟表匠学徒", "skill": "听潮辨位", "public_motivation": "修复家族钟塔"}
    c1.hidden_traits = {"secret": "能够听到钟塔的心跳", "fear": "深海", "private_agenda": "找到父亲失踪的真相"}
    c1.destiny_flag = "钟塔之心"
    c1.current_goals = ["查明父亲最后一次出海的目的", "阻止钟塔停摆"]

    c2 = Character()
    c2.id = 2
    c2.name = "苏铁"
    c2.role_type = "rival"
    c2.public_profile = {"identity": "潮汐调度官", "skill": "操控潮汐流向", "public_motivation": "维持群岛秩序"}
    c2.hidden_traits = {"secret": "知道父亲失踪的真相", "fear": "秩序崩溃", "private_agenda": "用潮汐掩盖旧案"}
    c2.destiny_flag = "潮汐之钥"
    c2.current_goals = ["阻止林澜调查旧案"]
    return [c1, c2]


def make_foreshadows():
    f1 = Foreshadow()
    f1.id = 1
    f1.title = "钟塔停摆的规律"
    f1.description = "林澜发现钟塔停摆并非随机，而是按照某种顺序进行。"
    f1.foreshadow_type = "hidden_pattern"
    f1.status = "planted"
    f1.urgency_level = 4
    f1.expected_resolution_window = "第3-5章"

    f2 = Foreshadow()
    f2.id = 2
    f2.title = "父亲的怀表"
    f2.description = "林澜在旧物中发现父亲留下的一只不会走的怀表。"
    f2.foreshadow_type = "mystery_clue"
    f2.status = "planted"
    f2.urgency_level = 3
    f2.expected_resolution_window = "第2-4章"
    return [f1, f2]


def main():
    settings = get_settings()
    print(f"Provider: {settings.llm_model} @ {settings.llm_base_url}")
    client = LLMClient(settings=settings)

    world = make_world()
    characters = make_characters()
    foreshadows = make_foreshadows()
    chapter_goal = "让林澜在钟塔中发现父亲留下的怀表，并第一次与苏铁对峙。"

    writer_msgs = build_writer_only_messages(
        world, characters, foreshadows, chapter_goal,
        outline_context={"opening_contract": {
            "inciting_incident": "林澜在擦拭钟塔齿轮时发现了刻有父亲名字的怀表",
            "prior_state": "林澜日复一日地做着钟表匠学徒的日常工作",
            "grounded_emotion": "对亲人的思念和不敢追问真相的压抑",
        }},
    )
    extractor_msgs = build_extraction_messages(
        world, characters, foreshadows, chapter_goal,
    )

    t0 = time.monotonic()
    chapter = client.generate_chapter_two_phase(writer_msgs, extractor_msgs)
    elapsed = time.monotonic() - t0

    # Save to files (avoids Windows console encoding issues)
    base = os.path.join(os.path.dirname(__file__), '..')
    
    prose_path = os.path.join(base, 'generated_chapter_prose.txt')
    with open(prose_path, 'w', encoding='utf-8') as f:
        f.write(chapter.draft_content)
    
    meta_path = os.path.join(base, 'generated_chapter_meta.txt')
    with open(meta_path, 'w', encoding='utf-8') as f:
        f.write(f"GENERATED CHAPTER ({len(chapter.draft_content)} chars, {elapsed:.1f}s)
")
        f.write(f"Model: {settings.llm_model} @ {settings.llm_base_url}
")
        f.write("=" * 60 + "
")
        f.write(f"CONTEXT: {chapter.context_summary}
")
        f.write(f"HINTS: {chapter.review_hints}
")
        f.write(f"CHARACTER CHANGES: {len(chapter.proposed_character_changes)}
")
        f.write(f"FORESHADOW CHANGES: {len(chapter.proposed_foreshadow_changes)}
")
        f.write(f"OPENING EVIDENCE: {len(chapter.opening_evidence)} items
")
        for e in chapter.opening_evidence:
            f.write(f"  [{e.check}] para={e.paragraph_index} quote={e.quote[:120]}...
")
    
    print(f"Prose -> {prose_path}")
    print(f"Meta -> {meta_path}")


if __name__ == "__main__":
    main()
