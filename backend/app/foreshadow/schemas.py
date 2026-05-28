from pydantic import BaseModel


class ForeshadowResponse(BaseModel):
    id: int
    title: str
    description: str
    foreshadow_type: str
    status: str
    urgency_level: int
    related_character_ids: list[int]
    expected_resolution_window: str | None

    model_config = {'from_attributes': True}
