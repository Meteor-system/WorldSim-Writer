from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow, ForeshadowEvent
from app.narrative.models import Chapter, ChapterDraft
from app.snapshot_export.models import WorldSnapshot
from app.tags.models import ObjectTag, Tag
from app.world.models import World

SAFE_EMAIL_PREFIX = 'e2e-'


def cleanup_e2e_data(db: Session, email_prefix: str = SAFE_EMAIL_PREFIX, dry_run: bool = False) -> dict:
    if not email_prefix.startswith(SAFE_EMAIL_PREFIX):
        raise ValueError('Refusing to cleanup users unless email_prefix starts with e2e-')

    users = list(db.scalars(select(User).where(User.email.like(f'{email_prefix}%')).order_by(User.id)))
    user_ids = [user.id for user in users]
    world_count = 0
    if user_ids:
        world_count = db.scalar(select(func.count()).select_from(World).where(World.owner_id.in_(user_ids))) or 0

    if dry_run:
        return {
            'email_prefix': email_prefix,
            'dry_run': True,
            'users_matched': len(users),
            'users_deleted': 0,
            'worlds_matched': world_count,
            'worlds_deleted': 0,
        }

    if user_ids:
        world_ids = list(db.scalars(select(World.id).where(World.owner_id.in_(user_ids))))
        if world_ids:
            chapter_ids = list(db.scalars(select(Chapter.id).where(Chapter.world_id.in_(world_ids))))
            foreshadow_ids = list(db.scalars(select(Foreshadow.id).where(Foreshadow.world_id.in_(world_ids))))
            if chapter_ids:
                db.execute(delete(ChapterDraft).where(ChapterDraft.chapter_id.in_(chapter_ids)))
            if foreshadow_ids:
                db.execute(delete(ForeshadowEvent).where(ForeshadowEvent.foreshadow_id.in_(foreshadow_ids)))
            db.execute(delete(ObjectTag).where(ObjectTag.world_id.in_(world_ids)))
            db.execute(delete(Tag).where(Tag.world_id.in_(world_ids)))
            db.execute(delete(WorldSnapshot).where(WorldSnapshot.world_id.in_(world_ids)))
            db.execute(delete(EventLog).where(EventLog.world_id.in_(world_ids)))
            db.execute(delete(CharacterRelation).where(CharacterRelation.world_id.in_(world_ids)))
            db.execute(delete(Foreshadow).where(Foreshadow.world_id.in_(world_ids)))
            db.execute(delete(Chapter).where(Chapter.world_id.in_(world_ids)))
            db.execute(delete(Character).where(Character.world_id.in_(world_ids)))
            db.execute(delete(World).where(World.id.in_(world_ids)))
        db.execute(delete(User).where(User.id.in_(user_ids)))

    db.commit()
    db.expire_all()
    return {
        'email_prefix': email_prefix,
        'dry_run': False,
        'users_matched': len(users),
        'users_deleted': len(users),
        'worlds_matched': world_count,
        'worlds_deleted': world_count,
    }
