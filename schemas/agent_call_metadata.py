from pydantic import BaseModel


class AgentCallMetadata(BaseModel):

    class Config:
        arbitrary_types_allowed = True

    call_id: str
    call_classification: str = None
    required_auth_level: str = None
    current_auth_level: str = None
    card_number: str = None
    customer_address: str = None