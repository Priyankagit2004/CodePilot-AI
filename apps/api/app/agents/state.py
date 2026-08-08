from operator import add
from typing import Annotated, TypedDict

from app.schemas.agents import AgentName, AgentOutput


class AgentGraphState(TypedDict):
    project_id: str
    request: str
    selected_agents: list[AgentName]
    outputs: Annotated[list[AgentOutput], add]
    execution_log: Annotated[list[str], add]
