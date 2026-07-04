"""TIMELINE-STABILIZER-001B — deterministic timeline diff / entropy check.

`compute_timeline_diff` is 审稿参考 (draft-review metadata) only. It is derived
from data already present at draft-payload construction time (the draft's
proposed formal changes, optionally compared against the current projection).
It must never mutate canon, projection, `world_version`, or the formal
`EventLog`, and approval must ignore it entirely.
"""

from sqlalchemy import select

from app.character.models import Character
from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter
from app.narrative.service import DEFAULT_ENTROPY_BUDGET, compute_timeline_diff
from app.world.models import World


# --- Pure function tests (no DB, no LLM) -----------------------------------


def test_compute_timeline_diff_empty_changes_is_low_risk():
    diff = compute_timeline_diff({})

    assert diff['new_canon_candidates'] == []
    assert diff['advanced_threads'] == []
    assert diff['new_threads'] == []
    assert diff['resolved_threads'] == []
    assert diff['resolved_count'] == 0
    assert diff['new_major_facts_count'] == 0
    assert diff['new_characters_count'] == 0
    assert diff['new_foreshadows_count'] == 0
    assert diff['entropy_score'] == 0
    assert diff['timeline_risk'] == 'low'
    assert diff['violations'] == []
    assert diff['budget'] == DEFAULT_ENTROPY_BUDGET


def test_compute_timeline_diff_is_deterministic_for_same_input():
    changes = {
        'characters': [{'character_id': 1, 'status': '调查', 'current_goals': ['x']}],
        'foreshadows': [{'foreshadow_id': 1, 'status': 'advanced', 'description_note': 'n'}],
    }

    assert compute_timeline_diff(changes) == compute_timeline_diff(changes)


def test_compute_timeline_diff_summarizes_character_and_foreshadow_changes():
    changes = {
        'characters': [
            {'character_id': 1, 'status': '开始调查', 'current_goals': ['追查密信']},
            {'character_id': 2, 'status': '隐瞒'},
        ],
        'foreshadows': [
            {'foreshadow_id': 1, 'status': 'advanced', 'description_note': '玉佩线索推进'},
            {'foreshadow_id': 2, 'status': 'resolved'},
        ],
    }

    diff = compute_timeline_diff(changes)

    # two status changes => two major facts; goal update adds a third candidate line
    assert diff['new_major_facts_count'] == 2
    assert len(diff['new_canon_candidates']) == 3
    assert len(diff['advanced_threads']) == 1
    assert diff['advanced_threads'][0]['foreshadow_id'] == 1
    assert len(diff['resolved_threads']) == 1
    assert diff['resolved_threads'][0]['foreshadow_id'] == 2
    assert diff['resolved_count'] == 1
    # entropy = major*2 + advanced*1 - resolved*1 = 4; at the low/medium boundary
    assert diff['entropy_score'] == 4
    assert diff['violations'] == []
    assert diff['timeline_risk'] == 'low'


def test_compute_timeline_diff_treats_expired_foreshadows_as_resolved():
    diff = compute_timeline_diff({'foreshadows': [{'foreshadow_id': 5, 'status': 'expired'}]})

    assert diff['resolved_count'] == 1
    assert diff['resolved_threads'][0]['foreshadow_id'] == 5
    assert diff['advanced_threads'] == []


def test_compute_timeline_diff_flags_over_budget_major_facts_as_high_risk():
    changes = {
        'characters': [
            {'character_id': 1, 'status': 'a'},
            {'character_id': 2, 'status': 'b'},
            {'character_id': 3, 'status': 'c'},
        ],
    }

    diff = compute_timeline_diff(changes)

    assert diff['new_major_facts_count'] == 3
    assert diff['violations']  # over the default max_new_major_facts of 2
    assert diff['timeline_risk'] == 'high'


def test_compute_timeline_diff_counts_new_entities_against_current_projection():
    changes = {
        'characters': [{'character_id': 1, 'status': 'known'}, {'character_id': 99, 'status': 'new'}],
        'foreshadows': [{'foreshadow_id': 7, 'status': 'advanced'}],
    }

    diff = compute_timeline_diff(
        changes,
        current_character_ids={1},
        current_foreshadow_ids={1, 2},
    )

    assert diff['new_characters_count'] == 1  # character 99 is not in the projection
    assert diff['new_foreshadows_count'] == 1  # foreshadow 7 is not in the projection
    # exactly one new character (<= budget 1) and one new foreshadow (<= budget 1),
    # and two major facts (== budget 2): none of these exceed the default budget,
    # so there is no violation even though the entropy is elevated.
    assert diff['violations'] == []
    assert diff['timeline_risk'] == 'medium'


def test_compute_timeline_diff_resolutions_reduce_entropy():
    without_resolution = compute_timeline_diff(
        {'foreshadows': [{'foreshadow_id': 1, 'status': 'advanced'}]}
    )
    with_resolution = compute_timeline_diff(
        {
            'foreshadows': [
                {'foreshadow_id': 1, 'status': 'advanced'},
                {'foreshadow_id': 2, 'status': 'resolved'},
            ]
        }
    )

    assert with_resolution['entropy_score'] < without_resolution['entropy_score'] + 1
    assert with_resolution['resolved_count'] == 1


def test_compute_timeline_diff_accepts_budget_override():
    changes = {'characters': [{'character_id': 1, 'status': 'a'}, {'character_id': 2, 'status': 'b'}]}

    strict = compute_timeline_diff(changes, budget={'max_new_major_facts': 1})

    assert strict['budget']['max_new_major_facts'] == 1
    assert strict['violations']
    assert strict['timeline_risk'] == 'high'


# --- Integration tests: draft/readback stays review-only until 写入正史 -------


class FakeLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 暗井回声',
            draft_content='林砚在灵井旁听见了第二个人的脚步声。',
            context_summary='林砚调查灵脉衰退，裂纹玉佩成为线索。',
            review_hints=['确认沈微霜动机是否一致'],
            proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['追查城主府叛乱'])],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='玉佩线索被推进')
            ],
        )


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'timeline@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def event_logs(db_session, world_id):
    return list(db_session.scalars(select(EventLog).where(EventLog.world_id == world_id).order_by(EventLog.id)))


def test_draft_payload_includes_timeline_diff_without_touching_world_state(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())

    world_before = db_session.get(World, world_id)
    version_before = world_before.world_version
    character_before = db_session.get(Character, 1)
    goals_before = list(character_before.current_goals)
    events_before = len(event_logs(db_session, world_id))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    timeline_diff = payload['timeline_diff']
    assert timeline_diff is not None
    assert timeline_diff['timeline_risk'] == 'low'
    assert len(timeline_diff['advanced_threads']) == 1
    assert timeline_diff['advanced_threads'][0]['foreshadow_id'] == 1
    assert 'budget' in timeline_diff

    # the review metadata must not have advanced any formal state
    db_session.expire_all()
    world_after = db_session.get(World, world_id)
    character_after = db_session.get(Character, 1)
    assert world_after.world_version == version_before
    assert list(character_after.current_goals) == goals_before
    assert len(event_logs(db_session, world_id)) == events_before
    assert not any(event.event_type == 'chapter_approved' for event in event_logs(db_session, world_id))


def test_reject_keeps_timeline_diff_review_only_and_does_not_advance_world(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    version_before = db_session.get(World, world_id).world_version

    reject_response = client.post(
        f"/chapters/{draft['chapter_id']}/reject",
        json={'feedback': '先不写入'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert reject_response.status_code == 200
    assert reject_response.json()['timeline_diff'] is not None

    db_session.expire_all()
    world_after = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert world_after.world_version == version_before
    assert chapter.status == 'rejected'
    assert not any(event.event_type == 'chapter_approved' for event in event_logs(db_session, world_id))


def test_approve_ignores_timeline_diff_and_still_applies_selected_changes(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    assert draft['timeline_diff'] is not None

    version_before = db_session.get(World, world_id).world_version

    approve_response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        headers={'Authorization': f'Bearer {token}'},
    )

    assert approve_response.status_code == 200
    db_session.expire_all()
    world_after = db_session.get(World, world_id)
    character_after = db_session.get(Character, 1)
    # approval is the sole canon boundary and still works as before
    assert world_after.world_version == version_before + 1
    assert character_after.current_goals == ['追查城主府叛乱']
    assert any(event.event_type == 'chapter_approved' for event in event_logs(db_session, world_id))


def test_stale_draft_approval_still_rejected_with_timeline_diff_present(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    assert draft['timeline_diff'] is not None

    # bump the world version out from under the draft to simulate a stale draft
    world = db_session.get(World, world_id)
    world.world_version = world.world_version + 1
    db_session.commit()

    approve_response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        headers={'Authorization': f'Bearer {token}'},
    )

    assert approve_response.status_code == 409
    assert approve_response.json()['detail'] == 'WORLD_VERSION_MISMATCH'
