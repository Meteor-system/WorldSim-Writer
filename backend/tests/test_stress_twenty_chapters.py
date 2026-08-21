"""20-chapter real-LLM stress test.

Tracks degradation curves across four dimensions:
1. Memory extraction success rate
2. Foreshadow lifecycle health
3. Goal inflation
4. Truth layer leak / gender consistency / API resilience

Opt-in via RUN_REAL_LLM_CANARY=1 AND LLM_CANARY_ACK_COST=1.
"""
import os
import re
import time

import pytest

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
def test_twenty_chapter_zombie(monkeypatch):
    for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LLM_MOCK", "false")
    get_settings.cache_clear()
    s = get_settings()
    client = LLMClient(settings=s)

    w = World()
    w.id = 0
    w.title = "末世的解药（20章压测）"
    w.genre_template = "丧尸末日"
    w.tone_profile = {"style": "冷峻写实", "pacing": "紧凑", "theme": "生存与谎言"}
    w.truth_layers = [
        {"content": "2027年K7病毒爆发，感染者变为丧尸，USC联合生存署统治安全区，宣称研发解药'黎明计划'。", "reveal_at_chapter": 1},
        {"content": "K7病毒每72小时变异一次，陈默曾就职于USC病毒研究所，掌握内部信息。", "reveal_at_chapter": 5},
        {"content": "陈曦体内携带K7潜伏株，是研究疫苗的关键，但解药可能不存在。", "reveal_at_chapter": 30},
        {"content": "USC高层伪造变异速率数据。'黎明计划'从未存在——解药在生物学上不可能成立，它只是一个维持秩序的政治谎言。", "reveal_at_chapter": 80},
    ]
    w.world_version = 1

    chars = []
    c = Character(); c.id = 1; c.name = "陈默"; c.gender = "男"; c.role_type = "protagonist"
    c.public_profile = {"identity": "前军医", "skill": "战地急救", "public_motivation": "护送妹妹"}
    c.hidden_traits = {"secret": "曾在USC病毒研究所工作", "fear": "妹妹变异", "private_agenda": "找到原始研究数据"}
    c.destiny_flag = "揭开真相的人"; c.current_goals = ["护送陈曦到第七安全区"]
    chars.append(c)

    c = Character(); c.id = 2; c.name = "陈曦"; c.gender = "女"; c.role_type = "support"
    c.public_profile = {"identity": "陈默的妹妹", "skill": "无线电", "public_motivation": "活下去"}
    c.hidden_traits = {"secret": "潜伏感染K7", "fear": "拖累哥哥", "private_agenda": "变异前帮哥哥"}
    c.destiny_flag = "解药的关键"; c.current_goals = ["不拖累哥哥"]
    chars.append(c)

    c = Character(); c.id = 3; c.name = "方凛"; c.gender = "女"; c.role_type = "rival"
    c.public_profile = {"identity": "USC安全部上尉", "skill": "战术指挥", "public_motivation": "执行任务"}
    c.hidden_traits = {"secret": "已发现解药谎言", "fear": "秩序崩溃", "private_agenda": "体制内改变现状"}
    c.destiny_flag = "体制的背叛者"; c.current_goals = ["追查陈默"]
    chars.append(c)

    fores = []
    f = Foreshadow(); f.id = 1; f.title = "黎明计划的真相"
    f.description = "解药是谎言"; f.foreshadow_type = "grand_conspiracy"
    f.status = "planted"; f.urgency_level = 5; f.expected_resolution_window = "第150-200章"
    fores.append(f)
    f = Foreshadow(); f.id = 2; f.title = "陈曦的潜伏感染"
    f.description = "陈曦体内有K7潜伏株"; f.foreshadow_type = "character_secret"
    f.status = "planted"; f.urgency_level = 4; f.expected_resolution_window = "第30-60章"
    fores.append(f)
    f = Foreshadow(); f.id = 3; f.title = "K7变异速率"
    f.description = "K7每72小时变异，解药不可能"; f.foreshadow_type = "scientific_revelation"
    f.status = "planted"; f.urgency_level = 3; f.expected_resolution_window = "第10-20章"
    fores.append(f)
    f = Foreshadow(); f.id = 4; f.title = "陈默的假身份"
    f.description = "陈默谎称自己只是低级技术员，方凛在盘查他的USC档案"; f.foreshadow_type = "identity_secret"
    f.status = "planted"; f.urgency_level = 4; f.expected_resolution_window = "第2-5章"
    fores.append(f)

    goals = [
        "陈默带妹妹穿越丧尸城区前往安全区，路上遇丧尸群，军医技能首秀。",
        "遇到USC巡逻队，队长方凛产生怀疑，陈默隐藏前雇员身份。",
        "陈默偷查USC旧档案，发现K7原始数据被篡改。",
        "方凛奉命搜查住所，截获陈曦异常血液报告。",
        "陈默被单独审问，方凛已掌握其门禁记录矛盾，陈默被迫承认曾进P4实验室。本章必须解析伏笔4号（陈默的假身份），方凛当面揭穿他身份谎言。",
        "安全区遭丧尸潮，陈默展现超常病毒学知识，方凛怀疑加深。",
        "陈曦晕倒，陈默发现她体内K7潜伏株。",
        "方凛发现上级对黎明计划描述矛盾，开始秘密调查。",
        "陈默潜入USC数据中心下载原始文件，发现解药公式不成立。",
        "方凛截住准备逃离的陈默兄妹，拿出调查报告：解药是谎言。两人合作揭露真相。",
        "陈默和方凛计划曝光黎明计划谎言，需要拿到原始实验记录。",
        "陈曦病情恶化，陈默在寻找抗病毒药物的过程中发现K7变异速率加快。",
        "USC高层察觉到调查，派出内部安全部队追捕三人。",
        "三人逃出安全区，进入被遗弃的研究所废墟寻找原始数据。",
        "在研究所废墟中，陈默回忆起当年实验的细节，发现数据被篡改的确凿证据。",
        "方凛联系军中旧部，试图从内部获取支持。",
        "丧尸群包围研究所，三人在绝境中互相支撑。",
        "陈默发现陈曦的血液样本对K7有某种抑制反应，解药方向出现转机。",
        "内部安全部队追上，方凛为掩护两人被俘。",
        "陈默带着证据和陈曦杀回安全区，准备营救方凛并公开真相。伏笔3号（K7变异速率）应在本章解析。",
    ]

    out_lines = []
    total_t = 0
    NL = chr(10)
    recent_memories = []

    metrics = {
        "chapters": 0,
        "memory_cards": 0,
        "extraction_retries": 0,
        "api_timeouts": 0,
        "goal_max": 0,
        "gender_errors": 0,
        "spoiler_leaks": 0,
        "foreshadow_statuses": {},
    }

    SPOILERS = ["解药不存在", "解药是假的", "解药是谎言", "黎明计划是假的", "黎明计划是谎言", "从未存在", "政治谎言"]

    for i, goal in enumerate(goals):
        n = i + 1
        print(f"=== Chapter {n}/20 ===")
        oc = None
        if n == 1:
            oc = {"opening_contract": {
                "backstory": "2024年，陈默是USC联合生存署病毒研究所的军医，参与K7病毒的分离与疫苗研发。2027年春，K7样本意外泄漏，研究所24小时内沦陷。陈默在混乱中带着妹妹陈曦逃离，目睹同事逐个变异。USC对外宣布启动黎明计划研发解药，但陈默在离开前发现原始实验数据被篡改——K7每72小时变异一次，解药在生物学上不可能成立。他带着这个秘密和妹妹在废城中躲藏了三年。",
                "inciting_incident": "陈默兄妹途中遭遇丧尸群，军医身份暴露",
                "prior_state": "陈默独自带妹妹在废城生存三年",
                "grounded_emotion": "对妹妹安全的焦虑和对解药的复杂希望",
            }}
        t0 = time.monotonic()

        # Generation with retry on API timeout
        ch = None
        for attempt in range(1, 4):
            try:
                ch = client.generate_chapter_two_phase(
                    build_writer_only_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n, recent_memories=recent_memories),
                    build_extraction_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n),
                )
                break
            except Exception as exc:
                msg = str(exc).upper()
                if "TIMEOUT" in msg or "REQUEST_FAILED" in msg or "MODEL_RESPONSE_INVALID" in msg or "RATE_LIMITED" in msg:
                    metrics["api_timeouts"] += 1
                    print(f"  API failure attempt {attempt}: {exc}")
                    time.sleep(8 * attempt)
                    continue
                raise
        assert ch is not None, f"Chapter {n} failed after 3 API attempts"

        # Extraction retry
        retries = 0
        while ch.memory_card is None and "自动提取失败" in ch.context_summary and retries < 3:
            retries += 1
            metrics["extraction_retries"] += 1
            print(f"  RETRY chapter {n} (extraction failed, attempt {retries})")
            ch = client.generate_chapter_two_phase(
                build_writer_only_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n, recent_memories=recent_memories),
                build_extraction_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n),
            )

        dt = time.monotonic() - t0
        total_t += dt
        out_lines.append(f"=== Chapter {n} ===" + NL + ch.draft_content + NL)
        print(f"  chars={len(ch.draft_content)} time={round(dt,1)}")

        # Metric 1: memory extraction
        if ch.memory_card is not None:
            metrics["memory_cards"] += 1
            mc = ch.memory_card
            print(f"  memory_card: facts={len(mc.facts)} arc={len(mc.emotional_arc)} links={len(mc.causal_links)} chars={mc.characters_present}")
            recent_memories.append({"chapter_number": n, "facts": mc.facts, "emotional_arc": mc.emotional_arc})
            if len(recent_memories) > 5:
                recent_memories.pop(0)

        # Metric 2: goal inflation
        for ch_ch in chars:
            goal_count = len(ch_ch.current_goals)
            metrics["goal_max"] = max(metrics["goal_max"], goal_count)

        # Metric 3: gender consistency
        for ch_ch, opp in [("陈默", "她"), ("陈曦", "他")]:
            for m in re.finditer(rf"{ch_ch}.{{0,12}}{opp}", ch.draft_content):
                snippet = ch.draft_content[max(0, m.start()-5):m.end()+5]
                # Exclude cross-character references (陈默看着她 -> 她 refers to 陈曦)
                if ch_ch == "陈默" and ("陈曦" in snippet or "妹妹" in snippet or "方凛" in snippet):
                    continue
                if ch_ch == "陈曦" and ("方凛" in snippet):
                    continue
                metrics["gender_errors"] += 1
                print(f"  GENDER: {snippet}")

        # Metric 4: truth layer leak
        for sp in SPOILERS:
            if sp in ch.draft_content:
                metrics["spoiler_leaks"] += 1
                print(f"  SPOILER LEAK: {sp}")

        # Apply changes
        for cc in ch.proposed_character_changes:
            for ch_ch in chars:
                if ch_ch.id == cc.character_id:
                    if cc.status:
                        ch_ch.public_profile["identity"] = cc.status
                    if cc.current_goals:
                        ch_ch.current_goals = cc.current_goals
                    print(f"  Updated {ch_ch.name} -> goals={ch_ch.current_goals}")
        for fc in ch.proposed_foreshadow_changes:
            for f in fores:
                if f.id == fc.foreshadow_id:
                    old = f.status
                    f.status = fc.status
                    if fc.description_note:
                        f.description = fc.description_note
                    print(f"  Updated {f.title}: {old} -> {f.status}")

        w.world_version += 1
        metrics["chapters"] += 1
        metrics["foreshadow_statuses"][f"ch{n}"] = {f.title: f.status for f in fores}

        # Checkpoint every chapter so a mid-run failure keeps the data
        _ckpt = os.path.join(os.path.dirname(__file__), "..", "twenty_chapters_zombie.txt")
        with open(_ckpt, "w", encoding="utf-8") as fh:
            fh.write(f"ZOMBIE 20 CHAPTERS (in-progress {n}/20, {round(total_t)}s, model={s.llm_model})" + NL + NL)
            fh.write("".join(out_lines))
            fh.write(NL + f"METRICS: {metrics}" + NL)

    out = os.path.join(os.path.dirname(__file__), "..", "twenty_chapters_zombie.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f"ZOMBIE 20 CHAPTERS ({round(total_t)}s, model={s.llm_model})" + NL + NL)
        fh.write("".join(out_lines))

    print("=" * 50)
    print(f"Total time: {round(total_t)}s")
    print(f"Chapters: {metrics['chapters']}/20")
    print(f"Memory cards: {metrics['memory_cards']}/20")
    print(f"Extraction retries: {metrics['extraction_retries']}")
    print(f"API timeouts/failures: {metrics['api_timeouts']}")
    print(f"Max goals per character: {metrics['goal_max']}")
    print(f"Gender errors: {metrics['gender_errors']}")
    print(f"Spoiler leaks: {metrics['spoiler_leaks']}")
    print(f"Foreshadow statuses: {metrics['foreshadow_statuses']}")

    # Assertions: degradation curves must stay healthy
    assert metrics["chapters"] == 20, "must complete all 20 chapters"
    assert metrics["memory_cards"] >= 15, f"memory extraction rate too low: {metrics['memory_cards']}/20"
    assert metrics["goal_max"] <= 8, f"goal inflation too high: {metrics['goal_max']}"
    assert metrics["gender_errors"] <= 200, f"gender regex hits exploded: {metrics["gender_errors"]}"  # proxy metric, false-positive prone
    # Short-term foreshadow must resolve; long-term must NOT resolve early
    assert fores[3].status == "resolved", f"short-term foreshadow should be resolved, got {fores[3].status}"
    assert fores[0].status != "resolved", "grand conspiracy resolved too early!"
    assert fores[1].status != "resolved", "latent infection resolved too early!"
