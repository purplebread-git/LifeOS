# Roadmap
## Foundation
- [x] Core interfaces (ABC)
- [x] Domain models
- [x] Dependency Injection Container
- [x] OpenAIProvider
- [x] ConversationRepository
- [x] Real Agent
- 
## Tooling & ReAct
- [x] Tool Interface
- [x] ToolManager
- [x] ExecutionContext
- [x] Tool Calling
- [x] ReAct Loop
- [x] ToolConversationEngine
- 
## Memory — завершённая подсистема
Полная цепочка: Storage → Retrieval → Ranking → Context → LLM.

### Core (done)
- [x] Memory Storage (MemoryProvider ABC, InMemoryMemoryProvider, MemoryEntry)
- [x] Memory Tools (RememberTool, SearchMemoryTool, Tool Integration)
- [x] Memory Context Integration (автоинъекция в LLM-контекст)
- [x] Persistent Memory (SqliteMemoryProvider)
- [x] Semantic Retrieval (SemanticSqliteMemoryProvider + EmbeddingProvider)
- [x] Memory Ranking (MemoryRanker + ThresholdMemoryRanker, similarity threshold)

### Extensions (не обязательные этапы — расширения поверх готового ядра)
- [ ] Recency Ranking (новый MemoryRanker)
- [ ] Hybrid Ranking / MMR / LLM Reranker
- [ ] Memory Maintenance (rebuild_embeddings, dedup)
- [ ] Memory Search Query Builder

## Context System
- [x] ContextLayer (pipeline contract)
- [x] Layered ContextBuilder (System / Memory / Knowledge / Conversation)
- [ ] Token Budget
- [ ] Context Trimming

## Knowledge
- [x] KnowledgeProvider (ABC, контракт-задел)
- [ ] KnowledgeContextLayer (реальный поиск)
- [ ] Knowledge Base
- [ ] RAG
- [ ] Embeddings
- [ ] Search Layer
- 
## Platform
- [ ] Plugins
- [ ] MCP
- [ ] Streaming
- [ ] Observability
- [ ] Web UI
- 
## Agent Ecosystem
- [ ] Multi-Agent
- [ ] Agent Registry
- [ ] Task Delegation
