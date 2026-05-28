from pydantic import BaseModel


class CharacterResponse(BaseModel):
    id: int
    name: str
    role_type: str
    status: str
    public_profile: dict
    hidden_traits: dict
    destiny_flag: str | None
    current_goals: list[str]

    model_config = {'from_attributes': True}


class CharacterRelationResponse(BaseModel):
    id: int
    source_character_id: int
    target_character_id: int
    relation_type: str
    intensity: int
    visibility: str

    model_config = {'from_attributes': True}
