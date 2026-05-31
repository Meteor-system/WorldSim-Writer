WORLD_SEEDS = [
    {
        'key': 'forgotten-sun-city',
        'label': '无日城',
        'genre_template': 'weird_fantasy',
        'hook': '一座所有人都忘记太阳存在过的城市，只有主角会在梦中被日光灼伤。',
        'tension_profile': ['集体失忆', '禁忌天象', '城市阴谋'],
        'payload': {
            'title': '无日城',
            'genre_template': 'weird_fantasy',
            'truth_canon': '无日城的天空永远是灰蓝色，居民相信世界从未有过太阳。城中的钟塔每天正午敲响十三次，敲声会抹去人们关于光的记忆。',
            'tone_profile': {'style': '诡秘奇幻、城市悬疑', 'pacing': '每章揭开一层被删除的常识'},
            'starter_assets': {
                'characters': [
                    {
                        'name': '沈昼',
                        'role_type': 'protagonist',
                        'status': '梦中被日光灼伤的抄钟员',
                        'public_profile': {'identity': '钟塔抄钟员', 'skill': '辨认被改写的钟声'},
                        'hidden_traits': {'secret': '他的影子会在正午指向不存在的太阳'},
                        'destiny_flag': '失落日光见证者',
                        'current_goals': ['查明正午第十三声钟响的来源'],
                    },
                    {
                        'name': '陆鸦',
                        'role_type': 'rival',
                        'status': '守夜局审查官',
                        'public_profile': {'identity': '守夜局审查官', 'skill': '清除异常记忆'},
                        'hidden_traits': {'fear': '害怕城市重新看见太阳'},
                        'destiny_flag': '记忆封锁执行者',
                        'current_goals': ['阻止沈昼传播日光梦境'],
                    },
                ],
                'relations': [
                    {'source_index': 0, 'target_index': 1, 'relation_type': 'mutual_suspicion', 'intensity': 4, 'visibility': 'private'}
                ],
                'foreshadows': [
                    {
                        'title': '空白日晷',
                        'description': '旧广场中央有一座没有刻度的日晷，阴影只在无人观看时移动。',
                        'foreshadow_type': 'world_rule_clue',
                        'status': 'planted',
                        'urgency_level': 4,
                        'related_character_indexes': [0, 1],
                        'expected_resolution_window': '第3-6章',
                    }
                ],
            },
        },
    },
    {
        'key': 'dead-god-oracle',
        'label': '死神谕教廷',
        'genre_template': 'dark_fantasy',
        'hook': '神明已经死亡三十年，但教廷每天仍准时收到新的神谕。',
        'tension_profile': ['死亡神明', '虚假神谕', '教廷权力'],
        'payload': {
            'title': '死神谕教廷',
            'genre_template': 'dark_fantasy',
            'truth_canon': '白烬神在三十年前的黑月战争中死亡，但祂的教廷仍每天收到神谕。只有少数高阶祭司知道，神谕从神尸所在的地下圣棺中传出。',
            'tone_profile': {'style': '黑暗奇幻、宗教悬疑', 'pacing': '以神谕矛盾推动政治与信仰危机'},
            'starter_assets': {
                'characters': [
                    {
                        'name': '伊莱恩',
                        'role_type': 'protagonist',
                        'status': '新任听谕修女',
                        'public_profile': {'identity': '听谕修女', 'skill': '记录神谕原文'},
                        'hidden_traits': {'secret': '她能听见神谕中的第二个声音'},
                        'destiny_flag': '圣棺真相发现者',
                        'current_goals': ['查明神谕为何互相矛盾'],
                    },
                    {
                        'name': '马洛枢机',
                        'role_type': 'antagonist',
                        'status': '教廷摄政枢机',
                        'public_profile': {'identity': '摄政枢机', 'skill': '解释神谕与清洗异端'},
                        'hidden_traits': {'guilt': '亲手封存了神尸'},
                        'destiny_flag': '信仰秩序守门人',
                        'current_goals': ['维持神谕权威不被动摇'],
                    },
                ],
                'relations': [
                    {'source_index': 0, 'target_index': 1, 'relation_type': 'public_opponents', 'intensity': 3, 'visibility': 'public'}
                ],
                'foreshadows': [
                    {
                        'title': '圣棺回声',
                        'description': '伊莱恩在抄写神谕时听见圣棺深处传来一句“不许相信我”。',
                        'foreshadow_type': 'oracle_clue',
                        'status': 'planted',
                        'urgency_level': 5,
                        'related_character_indexes': [0, 1],
                        'expected_resolution_window': '第2-5章',
                    }
                ],
            },
        },
    },
    {
        'key': 'generation-ship-myth',
        'label': '舱壁神话',
        'genre_template': 'sci_fi',
        'hook': '一艘世代航行的星舰上，所有人都被教育说“外面没有宇宙”。',
        'tension_profile': ['世代星舰', '封闭真相', '宇宙禁令'],
        'payload': {
            'title': '舱壁神话',
            'genre_template': 'sci_fi',
            'truth_canon': '方舟号已经航行两百年，管理层把外部宇宙称作古代迷信。真实星图被封存在舰首礼拜堂，舰体正在偏离原定航线。',
            'tone_profile': {'style': '硬科幻、密闭社会悬疑', 'pacing': '每章揭露一条星舰制度裂缝'},
            'starter_assets': {
                'characters': [
                    {
                        'name': '林舷',
                        'role_type': 'protagonist',
                        'status': '外壁维修学徒',
                        'public_profile': {'identity': '外壁维修学徒', 'skill': '舱外结构维护'},
                        'hidden_traits': {'secret': '曾在裂缝中看见星光'},
                        'destiny_flag': '真实星图开启者',
                        'current_goals': ['证明舱壁之外存在空间'],
                    },
                    {
                        'name': '赫尔曼舰牧',
                        'role_type': 'antagonist',
                        'status': '舰首礼拜堂守护者',
                        'public_profile': {'identity': '舰牧', 'skill': '维护方舟神话'},
                        'hidden_traits': {'fear': '知道航线已经无法抵达目的地'},
                        'destiny_flag': '星图封印者',
                        'current_goals': ['阻止外宇宙传闻扩散'],
                    },
                ],
                'relations': [
                    {'source_index': 0, 'target_index': 1, 'relation_type': 'enemy', 'intensity': 4, 'visibility': 'private'}
                ],
                'foreshadows': [
                    {
                        'title': '裂缝星光',
                        'description': '维修记录显示，只有林舷值班时，十三号外壁裂缝会出现不属于舰内灯光的蓝白光。',
                        'foreshadow_type': 'space_clue',
                        'status': 'planted',
                        'urgency_level': 4,
                        'related_character_indexes': [0, 1],
                        'expected_resolution_window': '第3-5章',
                    }
                ],
            },
        },
    },
    {
        'key': 'assigned-death-kingdom',
        'label': '死因王国',
        'genre_template': 'political_fantasy',
        'hook': '每个孩子出生时都会被国家分配一个未来死因，死因越荣耀，家族地位越高。',
        'tension_profile': ['命运官僚制', '贵族阴谋', '死亡阶级'],
        'payload': {
            'title': '死因王国',
            'genre_template': 'political_fantasy',
            'truth_canon': '赫洛王国用命簿为每个新生儿分配死因，贵族以荣耀死因为荣，平民常被分配为灾荒与矿难。命簿从未出错，但它最近开始出现空白页。',
            'tone_profile': {'style': '政治奇幻、命运反抗', 'pacing': '以制度压迫与个人选择交替推进'},
            'starter_assets': {
                'characters': [
                    {
                        'name': '莉塔',
                        'role_type': 'protagonist',
                        'status': '命簿抄录员',
                        'public_profile': {'identity': '王国命簿抄录员', 'skill': '解读死因文书'},
                        'hidden_traits': {'secret': '她的死因栏是空白'},
                        'destiny_flag': '空白死因持有者',
                        'current_goals': ['查清空白死因是否意味着不受命簿管辖'],
                    },
                    {
                        'name': '维克托公爵',
                        'role_type': 'rival',
                        'status': '荣耀死因贵族',
                        'public_profile': {'identity': '王国公爵', 'skill': '操控命簿审判'},
                        'hidden_traits': {'secret': '他的荣耀死因被篡改过'},
                        'destiny_flag': '命簿利益维护者',
                        'current_goals': ['夺回空白命簿页'],
                    },
                ],
                'relations': [
                    {'source_index': 0, 'target_index': 1, 'relation_type': 'rival', 'intensity': 4, 'visibility': 'public'}
                ],
                'foreshadows': [
                    {
                        'title': '空白命簿页',
                        'description': '命簿中出现没有名字也没有死因的空白页，但每晚都会多出一道血痕。',
                        'foreshadow_type': 'fate_clue',
                        'status': 'planted',
                        'urgency_level': 4,
                        'related_character_indexes': [0, 1],
                        'expected_resolution_window': '第2-5章',
                    }
                ],
            },
        },
    },
    {
        'key': 'world-bug-sect',
        'label': '漏洞宗门',
        'genre_template': 'xianxia',
        'hook': '一个修仙宗门把主角当成天才培养，只有主角知道自己是世界运行错误。',
        'tension_profile': ['世界漏洞', '修仙秩序', '天道追捕'],
        'payload': {
            'title': '漏洞宗门',
            'genre_template': 'xianxia',
            'truth_canon': '玄衡界由天道法则维持，所有修士突破都必须被天命册记录。主角没有天命册条目，却能绕过境界限制，被宗门误认为万年一遇的天才。',
            'tone_profile': {'style': '修仙悬疑、元叙事压力', 'pacing': '每章让主角使用一次漏洞并付出代价'},
            'starter_assets': {
                'characters': [
                    {
                        'name': '谢无缺',
                        'role_type': 'protagonist',
                        'status': '无册天才弟子',
                        'public_profile': {'identity': '青衡宗新弟子', 'skill': '跳过小境界突破'},
                        'hidden_traits': {'secret': '他不是天才，而是天道记录缺失的漏洞'},
                        'destiny_flag': '世界漏洞本体',
                        'current_goals': ['找出自己为何不在天命册中'],
                    },
                    {
                        'name': '闻照雪',
                        'role_type': 'mentor',
                        'status': '青衡宗执法长老',
                        'public_profile': {'identity': '执法长老', 'skill': '天命册校验'},
                        'hidden_traits': {'doubt': '怀疑谢无缺会引来天罚'},
                        'destiny_flag': '秩序与保护之间摇摆者',
                        'current_goals': ['确认谢无缺是否会毁掉宗门气运'],
                    },
                ],
                'relations': [
                    {'source_index': 0, 'target_index': 1, 'relation_type': 'mentor', 'intensity': 3, 'visibility': 'private'}
                ],
                'foreshadows': [
                    {
                        'title': '缺页天命册',
                        'description': '天命册在谢无缺名字应出现的位置缺了一页，缺口边缘仍在不断长出新墨。',
                        'foreshadow_type': 'heaven_rule_clue',
                        'status': 'planted',
                        'urgency_level': 5,
                        'related_character_indexes': [0, 1],
                        'expected_resolution_window': '第3-6章',
                    }
                ],
            },
        },
    },
]


def seed_summary(seed: dict) -> dict:
    payload = seed['payload']
    starter_assets = payload['starter_assets']
    return {
        'key': seed['key'],
        'label': seed['label'],
        'genre_template': seed['genre_template'],
        'hook': seed['hook'],
        'tension_profile': seed['tension_profile'],
        'starter_summary': {
            'character_count': len(starter_assets['characters']),
            'relation_count': len(starter_assets.get('relations') or []),
            'foreshadow_count': len(starter_assets.get('foreshadows') or []),
            'character_names': [item['name'] for item in starter_assets['characters']],
            'foreshadow_titles': [item['title'] for item in starter_assets.get('foreshadows') or []],
        },
    }


def seed_detail(seed: dict) -> dict:
    return {**seed_summary(seed), 'payload': seed['payload']}
