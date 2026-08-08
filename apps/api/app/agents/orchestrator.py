import logging
from collections.abc import Callable

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from app.agents.state import AgentGraphState
from app.core.config import Settings
from app.models.repository import RepositoryRecord
from app.schemas.agents import AgentExecutionResponse, AgentName, AgentOutput
from app.schemas.assistant import AssistantRequest, AssistantTask
from app.services.gemini_assistant import GeminiAssistantService
from app.services.repository import RepositoryService
from app.services.repository_intelligence import RepositoryIntelligenceService
from app.services.repository_knowledge import RepositoryKnowledgeService


logger = logging.getLogger(__name__)


SPECIALISTS: tuple[AgentName, ...] = (
    "repository_analysis",
    "architecture",
    "code_review",
    "security",
    "documentation",
    "testing",
)


class PlannerAgent:
    """Routes requests to specialist agents using explicit, explainable rules."""

    KEYWORDS: dict[AgentName, tuple[str, ...]] = {
        "architecture": (
            "architecture",
            "design",
            "pattern",
            "component",
            "flow",
        ),
        "code_review": (
            "review",
            "quality",
            "bug",
            "refactor",
            "improve",
            "smell",
        ),
        "security": (
            "security",
            "vulnerability",
            "secure",
            "secret",
            "auth",
            "injection",
        ),
        "documentation": (
            "document",
            "readme",
            "onboard",
            "api docs",
            "guide",
        ),
        "testing": (
            "test",
            "unit",
            "edge case",
            "coverage",
            "pytest",
        ),
    }

    def plan(self, request: str) -> list[AgentName]:
        text = request.lower()

        selected: list[AgentName] = ["repository_analysis"]

        for agent, keywords in self.KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                selected.append(agent)

        if len(selected) > 1:
            return list(dict.fromkeys(selected))

        return list(SPECIALISTS)


class MultiAgentOrchestrator:
    """Extensible LangGraph coordinator for repository-specialist agents."""

    def __init__(self, settings: Settings) -> None:
        self._repositories = RepositoryService(settings)
        self._knowledge = RepositoryKnowledgeService(settings)
        self._assistant = GeminiAssistantService(
            settings,
            self._knowledge,
        )
        self._planner = PlannerAgent()
        self._graph = self._build_graph()

    def execute(
        self,
        project_id: str,
        request: str,
    ) -> AgentExecutionResponse:
        result = self._graph.invoke(
            {
                "project_id": project_id,
                "request": request,
                "selected_agents": [],
                "outputs": [],
                "execution_log": [],
            }
        )

        return AgentExecutionResponse(
            project_id=project_id,
            request=request,
            selected_agents=result["selected_agents"],
            outputs=result["outputs"],
            execution_log=result["execution_log"],
        )

    def _build_graph(self):
        graph = StateGraph(AgentGraphState)

        retry = RetryPolicy(max_attempts=3)

        graph.add_node(
            "planner",
            self._plan,
            retry_policy=retry,
        )

        for agent in SPECIALISTS:
            graph.add_node(
                agent,
                self._specialist_node(agent),
                retry_policy=retry,
            )

            graph.add_edge("planner", agent)
            graph.add_edge(agent, "finalize")

        graph.add_node(
            "finalize",
            self._finalize,
        )

        graph.add_edge(START, "planner")
        graph.add_edge("finalize", END)

        return graph.compile()

    def _plan(
        self,
        state: AgentGraphState,
    ) -> dict:
        selected = self._planner.plan(
            state["request"]
        )

        logger.info(
            "agent_plan_created",
            extra={
                "project_id": state["project_id"],
                "selected_agents": selected,
            },
        )

        return {
            "selected_agents": selected,
            "execution_log": [
                f"Planner selected: {', '.join(selected)}"
            ],
        }

    def _specialist_node(
        self,
        agent: AgentName,
    ) -> Callable[[AgentGraphState], dict]:

        def node(
            state: AgentGraphState,
        ) -> dict:

            if agent not in state["selected_agents"]:
                return {
                    "outputs": [
                        AgentOutput(
                            agent=agent,
                            status="skipped",
                            content="Planner did not select this agent.",
                        )
                    ],
                    "execution_log": [
                        f"{agent}: skipped"
                    ],
                }

            try:
                record = self._repositories.get_record(
                    state["project_id"]
                )

                output = self._run_specialist(
                    agent,
                    record,
                    state["request"],
                )

                logger.info(
                    "agent_completed",
                    extra={
                        "agent": agent,
                        "project_id": state["project_id"],
                    },
                )

                return {
                    "outputs": [output],
                    "execution_log": [
                        f"{agent}: completed"
                    ],
                }

            except Exception as error:
                logger.exception(
                    "agent_failed",
                    extra={
                        "agent": agent,
                        "project_id": state["project_id"],
                    },
                )

                return {
                    "outputs": [
                        AgentOutput(
                            agent=agent,
                            status="failed",
                            content="",
                            error=str(error),
                        )
                    ],
                    "execution_log": [
                        f"{agent}: failed"
                    ],
                }

        return node

    def _run_specialist(
        self,
        agent: AgentName,
        record: RepositoryRecord,
        request: str,
    ) -> AgentOutput:

        # -------------------------------------------------------------
        # Repository analysis agent
        # -------------------------------------------------------------

        if agent == "repository_analysis":
            intelligence = RepositoryIntelligenceService().load(
                record
            )

            if intelligence is None:
                return AgentOutput(
                    agent=agent,
                    status="failed",
                    content="",
                    error=(
                        "Repository intelligence has not been generated."
                    ),
                )

            summary = (
                f"Repository contains "
                f"{intelligence.total_files} indexed files. "
                f"Languages: "
                f"{', '.join(intelligence.language_statistics) or 'none'}. "
                f"Frameworks: "
                f"{', '.join(intelligence.frameworks) or 'none'}."
            )

            return AgentOutput(
                agent=agent,
                status="completed",
                content=summary,
            )

        # -------------------------------------------------------------
        # Tasks handled by Gemini
        # -------------------------------------------------------------

        tasks: dict[
            AgentName,
            tuple[AssistantTask, ...],
        ] = {
            "architecture": (
                "architecture-explanation",
            ),
            "code_review": (
                "code-review",
                "bug-detection",
                "refactoring-suggestions",
            ),
            "security": (
                "security-analysis",
            ),
            "documentation": (
                "documentation-generation",
            ),
            "testing": (
                "testing-generation",
            ),
            "repository_analysis": (
                "repository-summary",
            ),
        }

        # -------------------------------------------------------------
        # Use a larger context window for architecture questions.
        #
        # Architecture needs information from several files:
        # application entry points, routes, services, configuration,
        # models, agents, etc.
        # -------------------------------------------------------------

        context_limit = 8

        if agent == "architecture":
            context_limit = 10

        elif agent == "documentation":
            context_limit = 10

        elif agent == "security":
            context_limit = 10

        elif agent == "testing":
            context_limit = 10

        responses = []

        for task in tasks[agent]:
            assistant_request = AssistantRequest(
                question=request,
                context_limit=context_limit,
            )

            response = self._assistant.answer(
                record,
                task,
                assistant_request,
            )

            responses.append(response)

        return AgentOutput(
            agent=agent,
            status="completed",
            content="\n\n---\n\n".join(
                response.answer
                for response in responses
            ),
        )

    @staticmethod
    def _finalize(
        _: AgentGraphState,
    ) -> dict:
        return {
            "execution_log": [
                "Agent workflow finalized"
            ]
        }