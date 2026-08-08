from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["repository_analysis", "architecture", "code_review", "security", "documentation", "testing"]
AgentStatus = Literal["completed", "skipped", "failed"]


class AgentExecutionRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=128)
    request: str = Field(min_length=2, max_length=4_000)


class AgentOutput(BaseModel):
    agent: AgentName
    status: AgentStatus
    content: str
    error: str | None = None


class AgentExecutionResponse(BaseModel):
    project_id: str
    request: str
    selected_agents: list[AgentName]
    outputs: list[AgentOutput]
    execution_log: list[str]
