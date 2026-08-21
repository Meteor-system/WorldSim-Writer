import os, time, re, pytest
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
def test_ten_chapter_zombie(monkeypatch):
    for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LLM_MOCK", "false")
    get_settings.cache_clear()
    s = get_settings()
    client = LLMClient(settings=s)

    w = World()
    w.id = 0
    w.title = "末世的解药"
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
        "方凛截住准备逃离的陈默兄妹，拿出调查报告：解药是谎言。方凛当面确认陈默假身份被查清（伏笔4号应在此时 resolved），两人合作揭露真相。",
    ]

    out_lines = []
    total_t = 0
    NL = chr(10)
    gender_bad = 0
    recent_memories = []

    for i, goal in enumerate(goals):
        n = i + 1
        print("=== Chapter", n, "/10 ===")
        print("Goal:", goal)
        oc = None
        if n == 1:
            oc = {"opening_contract": {
                "backstory": "2024年，陈默是USC联合生存署病毒研究所的军医，参与K7病毒的分离与疫苗研发。2027年春，K7样本意外泄漏，研究所24小时内沦陷。陈默在混乱中带着妹妹陈曦逃离，目睹同事逐个变异。USC对外宣布启动黎明计划研发解药，但陈默在离开前发现原始实验数据被篡改——K7每72小时变异一次，解药在生物学上不可能成立。他带着这个秘密和妹妹在废城中躲藏了三年。",
                "inciting_incident": "陈默兄妹途中遭遇丧尸群，军医身份暴露",
                "prior_state": "陈默独自带妹妹在废城生存三年",
                "grounded_emotion": "对妹妹安全的焦虑和对解药的复杂希望",
            }}
        t0 = time.monotonic()
        ch = client.generate_chapter_two_phase(
            build_writer_only_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n, recent_memories=recent_memories),
            build_extraction_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n),
        )
        # Retry up to 3 times on extraction failure (transient LLM JSON parse failure)
        retries = 0
        while ch.memory_card is None and "自动提取失败" in ch.context_summary and retries < 3:
            retries += 1
            print("  RETRY chapter", n, f"(extraction failed, attempt {retries})")
            ch = client.generate_chapter_two_phase(
                build_writer_only_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n, recent_memories=recent_memories),
                build_extraction_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n),
            )
        dt = time.monotonic() - t0
        total_t += dt
        out_lines.append("=== Chapter " + str(n) + " ===" + NL + ch.draft_content + NL)
        print("  chars:", len(ch.draft_content), "time:", round(dt, 1))
        print("  context:", ch.context_summary)

        # === MEMORY CARD ASSERTIONS ===
        mc = ch.memory_card
        assert mc is not None, f"Chapter {n}: memory_card must not be None"
        assert isinstance(mc.facts, list) and len(mc.facts) >= 2, f"Chapter {n}: facts >=2, got {mc.facts}"
        assert isinstance(mc.emotional_arc, str) and len(mc.emotional_arc) > 0, f"Chapter {n}: emotional_arc non-empty"
        assert isinstance(mc.causal_links, list) and len(mc.causal_links) >= 1, f"Chapter {n}: causal_links >=1"
        assert isinstance(mc.characters_present, list) and len(mc.characters_present) >= 1, f"Chapter {n}: characters_present >=1"
        for cid in mc.characters_present:
            assert isinstance(cid, int), f"Chapter {n}: characters_present must be int IDs"
        for fact in mc.facts:
            assert isinstance(fact, str) and len(fact.strip()) > 0, f"Chapter {n}: fact non-empty"
        print(f"  memory_card: facts={len(mc.facts)}, arc={mc.emotional_arc!r}, links={mc.causal_links!r}, chars={mc.characters_present}")

        recent_memories.append({
            "chapter_number": n,
            "facts": mc.facts,
            "emotional_arc": mc.emotional_arc,
        })
        if len(recent_memories) > 5:
            recent_memories.pop(0)

        if n >= 2:
            wm = build_writer_only_messages(w, chars, fores, goal, outline_context=oc, chapter_number=n, recent_memories=recent_memories)
            user_content = wm[1]["content"]
            assert "近期已批准章节记忆" in user_content, f"Chapter {n}: writer prompt must contain memory header"
            oldest_in_window = recent_memories[0]["chapter_number"]
            assert f"第{oldest_in_window}章:" in user_content, f"Chapter {n}: writer prompt must reference chapter {oldest_in_window} memory"
        bad = re.findall(r"陈默.{0,10}她", ch.draft_content)
        if bad:
            gender_bad += 1
            print("  GENDER ERROR: 陈默->她", bad)
        bad2 = re.findall(r"陈曦.{0,10}他", ch.draft_content)
        if bad2:
            gender_bad += 1
            print("  GENDER ERROR: 陈曦->他", bad2)
        for cc in ch.proposed_character_changes:
            for c in chars:
                if c.id == cc.character_id:
                    if cc.status: c.public_profile["identity"] = cc.status
                    if cc.current_goals: c.current_goals = cc.current_goals
                    print("  Updated", c.name, "->", c.current_goals)
        for fc in ch.proposed_foreshadow_changes:
            for f in fores:
                if f.id == fc.foreshadow_id:
                    old = f.status
                    f.status = fc.status
                    if fc.description_note: f.description = fc.description_note
                    print("  Updated", f.title, ":", old, "->", f.status)
        w.world_version += 1

    out = os.path.join(os.path.dirname(__file__), "..", "ten_chapters_zombie.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("ZOMBIE 10 CHAPTERS (" + str(round(total_t)) + "s, model=" + str(s.llm_model) + ")" + NL + NL)
        fh.write("".join(out_lines))
    print("Saved to", out)
    print("Total time:", round(total_t))
    print("Gender errors:", gender_bad)
    print("Memory cards:", len(recent_memories))
    assert len(out_lines) == 10
    assert 1 <= len(recent_memories) <= 5, f"Expected 1-5 memories in window, got {len(recent_memories)}"
