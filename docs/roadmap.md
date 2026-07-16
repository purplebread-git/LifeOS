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
## Memory
### Done
- [x] MemoryProvider
- [x] InMemoryMemoryProvider
- [x] MemoryEntry
- [x] RememberTool
- [x] SearchMemoryTool
- [x] Memory Tool Integration
- [x] Memory Context Integration
- [x] Persistent MemoryProvider (SQLite)
- [x] Semantic Search (SemanticSqliteMemoryProvider + EmbeddingProvider)

### Next
- [ ] Memory Ranking (similarity threshold / weighting — score уже считается)
- [ ] rebuild_embeddings() (reindex при смене модели / после сбоя embeddings)
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
