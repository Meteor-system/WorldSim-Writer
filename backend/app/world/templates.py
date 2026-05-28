SAMPLE_WORLD = {
    'title': '青岚城风云',
    'genre_template': 'xianxia_intrigue',
    'truth_canon': '青岚城由城主府、云河剑宗与地下商盟共同影响。灵脉衰退正在改变各方力量平衡，主角必须查清城主府叛乱传闻的真相。',
    'tone_profile': {'style': '克制、悬疑、东方玄幻', 'pacing': '章节末保留明确推进'},
    'characters': [
        {
            'name': '林砚',
            'role_type': 'protagonist',
            'status': 'active',
            'public_profile': {'identity': '云河剑宗外门弟子', 'skill': '擅长阵纹推演'},
            'hidden_traits': {'fear': '害怕牵连师门'},
            'destiny_flag': '灵脉异动见证者',
            'current_goals': ['调查青岚城灵脉衰退'],
        },
        {
            'name': '沈微霜',
            'role_type': 'ally',
            'status': 'active',
            'public_profile': {'identity': '城主府书记官', 'skill': '熟悉卷宗与密道'},
            'hidden_traits': {'secret': '曾替叛乱嫌疑人销毁证据'},
            'destiny_flag': '关键证人',
            'current_goals': ['保住城主府档案'],
        },
    ],
    'relations': [
        {'source_index': 0, 'target_index': 1, 'relation_type': 'uneasy_alliance', 'intensity': 2, 'visibility': 'public'},
    ],
    'foreshadows': [
        {
            'title': '裂纹玉佩',
            'description': '林砚在废弃灵井旁拾到一枚带城主府纹章的裂纹玉佩。',
            'foreshadow_type': 'object_clue',
            'status': 'planted',
            'urgency_level': 3,
            'related_character_indexes': [0, 1],
            'expected_resolution_window': '第2-4章',
        }
    ],
}
