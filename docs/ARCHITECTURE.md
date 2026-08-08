# Architecture

```mermaid
flowchart TB
  Web[React 19 / Vite / Tailwind] -->|REST| FastAPI
  FastAPI --> RepositoryService
  RepositoryService --> SafeUpload[Safe ZIP validation and storage]
  SafeUpload --> Parser[Tree-sitter parser services]
  Parser --> Intelligence[Structured repository intelligence]
  Intelligence --> Dashboard[Dashboard metrics service]
  Intelligence --> Knowledge[LangChain splitter and embedding service]
  Knowledge --> Vectors[(Persistent ChromaDB)]
  Vectors --> Gemini[Gemini grounded answers]
  Gemini --> Agents[LangGraph specialist agents]
```

The API persists repositories under `REPOSITORY_STORAGE_DIR` and vector data under `CHROMA_STORAGE_DIR`. The intelligence model is the boundary between parsing and retrieval, so embeddings and LLM behavior can evolve without changing parser output.
