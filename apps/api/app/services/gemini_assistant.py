from google import genai

from app.agents.prompts import PROMPT_TEMPLATES, render_prompt
from app.core.config import Settings
from app.core.exceptions import APIException
from app.models.repository import RepositoryRecord
from app.schemas.assistant import (
    AssistantRequest,
    AssistantResponse,
    AssistantTask,
)
from app.services.repository_knowledge import RepositoryKnowledgeService


class GeminiAssistantService:
    """Gemini generation layer grounded in repository knowledge retrieval."""

    def __init__(
        self,
        settings: Settings,
        knowledge_service: RepositoryKnowledgeService,
    ) -> None:
        self._settings = settings
        self._knowledge_service = knowledge_service

        api_key = settings.gemini_api_key

        if api_key is None or not api_key.get_secret_value():
            self._client = None
        else:
            self._client = genai.Client(
                api_key=api_key.get_secret_value()
            )

    def answer(
        self,
        record: RepositoryRecord,
        task: AssistantTask,
        request: AssistantRequest,
    ) -> AssistantResponse:

        if task not in PROMPT_TEMPLATES:
            raise APIException(
                422,
                "unknown_assistant_task",
                "Unsupported assistant task.",
            )

        if self._client is None:
            raise APIException(
                503,
                "gemini_not_configured",
                "Gemini is not configured. Set GEMINI_API_KEY to enable AI responses.",
            )

        retrieval_query = " ".join(
            part
            for part in [
                request.file_path,
                request.question,
                task.replace("-", " "),
            ]
            if part
        ).strip()

        context = self._knowledge_service.search(
            record,
            retrieval_query,
            request.context_limit,
        ).results

        prompt = render_prompt(
            task,
            project_id=record.project_id,
            question=request.question or retrieval_query,
            file_path=request.file_path or "the retrieved file",
            context=self._format_context(context),
        )

        try:
            response = self._client.interactions.create(
                model=self._settings.gemini_model,
                input=prompt,
            )
        except Exception as error:
            print("GEMINI ERROR:", repr(error))
            raise APIException(
                502,
                "gemini_request_failed",
                "Gemini could not process this request.",
            ) from error

        answer = getattr(response, "output_text", None)

        if not answer:
            # Newer SDK responses expose outputs directly.
            outputs = getattr(response, "outputs", None)

            if outputs:
                text_outputs = [
                    getattr(output, "text", None)
                    for output in outputs
                    if getattr(output, "text", None)
                ]

                if text_outputs:
                    answer = text_outputs[-1]

        if not answer:
            raise APIException(
                502,
                "gemini_empty_response",
                "Gemini returned no text response.",
            )

        return AssistantResponse(
            project_id=record.project_id,
            task=task,
            answer=answer,
            context=context,
        )

    @staticmethod
    def _format_context(context) -> str:
        if not context:
            return "No matching repository context was retrieved."

        return "\n\n---\n\n".join(
            f"File: {item.file_path}\n{item.content}"
            for item in context
        )