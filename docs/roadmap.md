# Roadmap

Организован по зрелости системы (Core / Capabilities / Platform), а не по
последовательности разработки — так он отражает архитектуру продукта.

Общий паттерн: `Infrastructure → Capability → Tool → Agent`. Агент работает
только с capabilities через инструменты; инфраструктура скрыта.

## Core

### Foundation
- [x] Core interfaces (ABC)
- [x] Domain models
- [x] Dependency Injection Container
- [x] OpenAIProvider
- [x] ConversationRepository
- [x] Real Agent

### Conversation & Tool Calling
- [x] Tool Interface / ToolManager
- [x] ExecutionContext (реестр capabilities)
- [x] ReAct Loop / ToolConversationEngine

### Context System
- [x] ContextLayer (pipeline contract)
- [x] Layered ContextBuilder (System / Memory / Knowledge / Conversation)
- [ ] Context Composer (порядок / бюджет токенов / приоритеты — когда слоёв станет больше)
- [ ] Token Budget / Context Trimming

### Memory
Полная цепочка: Storage → Retrieval → Ranking → Context → LLM.
- [x] Memory Storage (MemoryProvider ABC, InMemoryMemoryProvider, MemoryEntry)
- [x] Memory Context Integration (автоинъекция в LLM-контекст)
- [x] Persistent Memory (SqliteMemoryProvider)
- [x] Semantic Retrieval (SemanticSqliteMemoryProvider + EmbeddingProvider)
- [x] Memory Ranking (MemoryRanker + ThresholdMemoryRanker)

### Knowledge
Строится по схеме памяти: Storage → Retrieval → Ranking → Context. Доменная
модель организована вокруг `source`.
- [x] KnowledgeProvider (ABC: add / add_batch / search / list_sources / delete_source)
- [x] KnowledgeChunk (доменная модель, отдельная от MemoryEntry)
- [x] InMemoryKnowledgeProvider (substring, retrieval MVP)
- [x] KnowledgeContextLayer (Knowledge → Context → LLM)
- [x] Persistent Knowledge (SqliteKnowledgeProvider + KnowledgeRecord)
- [x] Semantic Knowledge Retrieval (SemanticSqliteKnowledgeProvider, embeddings + cosine)
- [x] Knowledge Ranking (KnowledgeRanker + ThresholdKnowledgeRanker)
- [x] Chunking Engine (Chunker ABC + FixedSizeChunker)
- [x] Document Ingestion (DocumentExtractor ABC + PlainTextExtractor + DocumentIngestionService)
- [x] Knowledge Source Management (list_sources / delete_source — доменная модель вокруг source завершена)
- [x] Extractor Routing (ExtractorRegistry: extension → extractor, default PlainText; сервис-инвариант)
- [x] MarkdownExtractor (markdown-it-py + собственный обход токенов, .md/.markdown) — доказательство горизонтального расширения
- [x] PdfExtractor (pypdf, встроенный текст, без OCR, .pdf) — расширение проверено на бинарном формате

## Capabilities
Возможности агента, открытые через инструменты (Tool → Capability).
- [x] Memory Tools (RememberTool, SearchMemoryTool)
- [x] Knowledge Tools (IngestDocumentTool, SearchKnowledgeTool) — Knowledge MVP замкнут
- [x] Knowledge Source Tools (ListSourcesTool, DeleteSourceTool)
- [x] MarkdownExtractor (.md / .markdown) — подключён чистым адаптером + записью в реестре
- [x] PdfExtractor (.pdf) — первый бинарный формат, подключён так же (регистрация в реестре)
- [ ] Анализ повторяемости extractor'ов (после трёх реализаций: есть ли BaseExtractor / общие утилиты)
- [ ] Additional Extractors (DOCX / HTML / RemoteUrl — чистый адаптер + запись в реестре)

### Extensions (расширения поверх готового ядра, не обязательные этапы)
- [ ] Memory: Recency / Hybrid / MMR / LLM Reranker; Maintenance (rebuild_embeddings, dedup)
- [ ] Knowledge: Chunking-стратегии (sentence / paragraph / recursive / token / semantic)
- [ ] Knowledge Ranking: recency / MMR / citation weight / source priority
- [ ] Knowledge Management: statistics / rename / update (расширение доменной модели)

## Platform
- [ ] Plugins
- [ ] Streaming
- [ ] Observability
- [ ] MCP
- [ ] Multi-Agent / Agent Registry / Task Delegation
- [ ] Web UI
