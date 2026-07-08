from app.narrative import service as narrative_service


def _style_execution_context() -> dict:
    return {
        'source': 'manual',
        'source_world_version': 1,
        'recommended_pov': {'character_id': None, 'name': None},
        'priority_characters': [],
        'priority_foreshadows': [],
        'progression_hints': [],
        'continuity_warnings': [],
        'recent_events': [],
        'material_references': [],
        'style_handbook_reference': {
            'source_title': '参考片段',
            'source_rights': 'general_reference',
            'handbook': {
                'narrative_pacing': {'label': '叙事节奏', 'value': '中速推进。', 'evidence': '雨夜里，旧城门缓慢打开。'},
                'language_density': {'label': '语言密度', 'value': '中等语言密度。', 'evidence': None},
                'dialogue_ratio': {'label': '对白比例', 'value': '对白与叙述交替。', 'evidence': None},
                'scene_progression': {'label': '场景推进', 'value': '用意象带动转场。', 'evidence': None},
                'suspense_structure': {'label': '悬念结构', 'value': '每节保留待解问题。', 'evidence': None},
                'relationship_tension': {'label': '人物关系张力', 'value': '围绕亏欠推进。', 'evidence': None},
                'foreshadowing_pattern': {'label': '伏笔埋设/回收方式', 'value': '先给异常，再延迟解释。', 'evidence': None},
                'do_guidelines': ['保留抽象节奏。'],
                'avoid_guidelines': ['不要复用原文句子、人物名、专有设定或标志性桥段。'],
                'originality_guidelines': ['正式章节仍需 Studio 审稿。'],
            },
            'safety_notes': ['风格手册只是写作参考，不写入 canon。'],
        },
    }


def test_prompt_injects_abstract_style_handbook_dimensions_without_reusing_original_text():
    prompt = narrative_service.format_execution_context_for_prompt(_style_execution_context())

    assert '写作风格参考（来源：参考片段，仅抽象维度，禁止照抄原文）' in prompt
    assert '叙事节奏：中速推进。' in prompt
    assert '关系张力：围绕亏欠推进。' in prompt
    assert '需避免：不要复用原文句子、人物名、专有设定或标志性桥段。' in prompt
    # 只带入抽象维度，不把参考原文证据注入 prompt
    assert '雨夜里，旧城门缓慢打开。' not in prompt


def test_prompt_omits_style_reference_when_absent():
    context = _style_execution_context()
    context['style_handbook_reference'] = None
    prompt = narrative_service.format_execution_context_for_prompt(context)

    assert '写作风格参考' not in prompt
