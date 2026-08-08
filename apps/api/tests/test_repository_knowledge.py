from app.schemas.knowledge import RetrievedContext
from app.services.repository_knowledge import RepositoryKnowledgeService


def test_answer_is_grounded_in_retrieved_context() -> None:
    context = [RetrievedContext(file_path="src/api.py", chunk_id="chunk-1", content="@app.get('/health')", relevance_score=0.98)]
    answer = RepositoryKnowledgeService._format_answer(context)

    assert "src/api.py" in answer
    assert context[0].content in answer


def test_code_splitter_is_available_for_python() -> None:
    from langchain_text_splitters import Language

    splitter = RepositoryKnowledgeService._splitter(Language.PYTHON)

    assert splitter.chunk_size == 1_500
