import os, time, pytest
from app.core.config import get_settings
from app.llm.client import LLMClient
from app.narrative.service import build_writer_only_messages, build_extraction_messages
from app.world.models import World
from app.character.models import Character
from app.foreshadow.models import Foreshadow

@pytest.mark.real_llm
@pytest.mark.skipif(
    not (os.getenv("RUN_REAL_LLM_CANARY") == "1" and os.getenv("LLM_CANARY_ACK_COST") == "1"),
    reason="needs opt-in",
)
def test_save_generated_prose(monkeypatch):
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LLM_MOCK", "false")
    get_settings.cache_clear()
    settings = get_settings()
    w = World(); w.id = 0; w.title = "钟表群岛"
    w.genre_template = "悬疑奇幻"
    w.tone_profile = {"style": "冷峻悬疑", "pacing": "中等", "theme": "秩序与自由"}
    w.truth_canon = "钟表群岛：由发条潮汐维持、每晚会交换岛屿位置的群岛。"
    w.world_version = 1
    c1 = Character(); c1.id = 1; c1.name = "林澜"; c1.role_type = "protagonist"
    c1.public_profile = {"identity": "钟表匠学徒"}
    c1.hidden_traits = {"secret": "听到钟塔心跳"}
    c1.destiny_flag = "钟塔之心"; c1.current_goals = ["查明父亲出海目的"]
    c2 = Character(); c2.id = 2; c2.name = "苏铁"; c2.role_type = "rival"
    c2.public_profile = {"identity": "潮汐调度官"}
    c2.hidden_traits = {"secret": "知道真相"}
    c2.destiny_flag = "潮汐之钥"; c2.current_goals = ["阻止林澜"]
    f1 = Foreshadow(); f1.id = 1; f1.title = "钟塔停摆"; f1.foreshadow_type = "hidden_pattern"
    f1.status = "planted"; f1.urgency_level = 4; f1.expected_resolution_window = "第3-5章"
    f2 = Foreshadow(); f2.id = 2; f2.title = "父亲的怀表"; f2.foreshadow_type = "mystery_clue"
    f2.status = "planted"; f2.urgency_level = 3; f2.expected_resolution_window = "第2-4章"
    client = LLMClient(settings=settings)
    goal = "让林澜在钟塔中发现父亲留下的怀表，并第一次与苏铁对峙。"
    writer_msgs = build_writer_only_messages(w, [c1,c2], [f1,f2], goal)
    extractor_msgs = build_extraction_messages(w, [c1,c2], [f1,f2], goal)
    t0 = time.monotonic()
    ch = client.generate_chapter_two_phase(writer_msgs, extractor_msgs)
    elapsed = time.monotonic() - t0
    NL = chr(10)
    out = os.path.join(os.path.dirname(__file__), "..", "generated_chapter_prose.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(ch.draft_content)
    meta = os.path.join(os.path.dirname(__file__), "..", "generated_chapter_meta.txt")
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write("Model: " + str(settings.llm_model) + NL)
        fh.write("Chars: " + str(len(ch.draft_content)) + NL)
        fh.write("Time: " + str(round(elapsed,1)) + "s" + NL)
        fh.write("Context: " + str(ch.context_summary) + NL)
    assert len(ch.draft_content) > 200
