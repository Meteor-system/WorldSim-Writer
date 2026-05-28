from pydantic import BaseModel

from app.character.schemas import CharacterRelationResponse, CharacterResponse
from app.event.schemas import EventLogResponse
from app.foreshadow.schemas import ForeshadowResponse


class WorldResponse(BaseModel):
    id: int
    title: str
    genre_template: str
    truth_canon: str
    truth_canon_version: int
    world_version: int
    status: str
    tone_profile: dict

    model_config = {'from_attributes': True}


class WorldOverviewResponse(WorldResponse):
    characters: list[CharacterResponse]
    relations: list[CharacterRelationResponse]
    foreshadows: list[ForeshadowResponse]
    recent_events: list[EventLogResponse]
