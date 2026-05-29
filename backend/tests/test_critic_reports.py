from sqlalchemy import func, select

from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter
from app.world.models import World


CRITIC_DIMENSIONS = [
    'pacing',
    'tension',
    'character_consistency',
    'dialogue_quality',
    'structure',
    'world_continuity',
    'readability',
]


class CriticReportLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content='第一段：林砚停在雨巷口。\n\n第二段：沈微霜递来一封湿透的信。',
            context_summary='林砚与沈微霜在雨巷交换线索。',
            review_hints=['确认第二段的信息揭示是否过快'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
        )

    def generate_critic_report(self, messages):
        return {
            'overall_score': 78,
            'summary': '章节冲突清晰，但第二段信息揭示偏快，对白可更有潜台词。',
            'dimensions': {
                'pacing': {
                    'score': 72,
                    'summary': '中段推进略快。',
                    'issues': [],
                    'suggestions': ['放慢第二段的信息揭示。'],
                },
                'tension': {
                    'score': 82,
                    'summary': '雨巷会面有悬念。',
                    'issues': [],
                    'suggestions': ['让信件内容更晚揭示。'],
                },
                'character_consistency': {
                    'score': 85,
                    'summary': '林砚目标与当前状态一致。',
                    'issues': [],
                    'suggestions': ['保留林砚的谨慎反应。'],
                },
                'dialogue_quality': {
                    'score': 68,
                    'summary': '对白略偏解释性。',
                    'issues': [
                        {
                            'severity': 'medium',
                            'dimension': 'dialogue_quality',
                            'message': '第二段对白解释性较强。',
                            'paragraph_index': 1,
                            'suggested_action': '润色本段对白，增加潜台词。',
                        }
                    ],
                    'suggestions': ['减少直白解释。'],
                },
                'structure': {
                    'score': 80,
                    'summary': '开端清晰。',
                    'issues': [],
                    'suggestions': ['章末保留更强钩子。'],
                },
                'world_continuity': {
                    'score': 90,
                    'summary': '未发现世界观冲突。',
                    'issues': [],
                    'suggestions': ['保持伏笔推进与玉佩线索一致。'],
                },
                'readability': {
                    'score': 76,
                    'summary': '可读性良好。',
                    'issues': [],
                    'suggestions': ['压缩重复意象。'],
                },
            },
            'issues': [
                {
                    'severity': 'medium',
                    'dimension': 'dialogue_quality',
                    'message': '第二段对白解释性较强。',
                    'paragraph_index': 1,
                    'suggested_action': '润色本段对白，增加潜台词。',
                }
            ],
            'suggestions': ['优先润色第二段对白。'],
        }


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'critic-report@example.com', 'password': 'strongpass123'}).json()[
        'access_token'
    ]
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def create_reviewing_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: CriticReportLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    return response.json()


def test_post_critic_report_generates_structured_report_without_mutating_world(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/critic-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['chapter_id'] == draft['chapter_id']
    assert payload['draft_version'] == 1
    assert payload['overall_score'] == 78
    assert payload['summary'] == '章节冲突清晰，但第二段信息揭示偏快，对白可更有潜台词。'
    assert sorted(payload['dimensions']) == sorted(CRITIC_DIMENSIONS)
    assert payload['dimensions']['dialogue_quality']['score'] == 68
    assert payload['issues'][0]['severity'] == 'medium'
    assert payload['issues'][0]['paragraph_index'] == 1
    assert payload['suggestions'] == ['优先润色第二段对白。']
    assert isinstance(payload['created_at'], str)

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    event_count = db_session.scalar(select(func.count()).select_from(EventLog))
    assert world.world_version == 1
    assert chapter.critique_report['draft_version'] == 1
    assert chapter.critique_report['overall_score'] == 78
    assert event_count == 0


def test_get_critic_report_returns_saved_report_and_marks_stale_after_draft_version_changes(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    post_response = client.post(
        f"/chapters/{draft['chapter_id']}/critic-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert post_response.status_code == 200

    get_response = client.get(
        f"/chapters/{draft['chapter_id']}/critic-report",
        headers={'Authorization': f'Bearer {token}'},
    )
    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload['draft_version'] == 1
    assert payload['is_stale'] is False

    edit_response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': '第一段：林砚停在雨巷口，玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert edit_response.status_code == 200

    stale_response = client.get(
        f"/chapters/{draft['chapter_id']}/critic-report",
        headers={'Authorization': f'Bearer {token}'},
    )
    assert stale_response.status_code == 200
    stale_payload = stale_response.json()
    assert stale_payload['draft_version'] == 1
    assert stale_payload['current_draft_version'] == 2
    assert stale_payload['is_stale'] is True


def test_get_critic_report_returns_404_when_report_is_missing(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.get(
        f"/chapters/{draft['chapter_id']}/critic-report",
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'NOT_FOUND'
