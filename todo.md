# TODO: LearnIA Development Modules

## 1. Authentication Module (REST)
- [ ] POST `/auth/register`: User registration.
- [ ] POST `/auth/login`: User authentication.
- [ ] POST `/auth/logout`: End session.
- [ ] GET `/auth/session`: Validate session.

## 2. Personal Documents & RAG (REST)
- [ ] POST `/notebooks/{notebookId}/documents`: Upload PDF/Text.
- [ ] GET `/documents/{documentId}`: Document details.
- [ ] PATCH `/documents/{documentId}`: Update metadata.
- [ ] DELETE `/documents/{documentId}`: Remove document.
- [ ] POST `/documents/{documentId}/processing-jobs`: Start extraction, chunking, vectorization.
- [ ] GET `/documents/{documentId}/processing-jobs/{jobId}`: Check processing status.

## 3. Study Rooms & Collaborative RAG (REST)
- [ ] POST `/study-rooms/{studyRoomId}/documents`: Upload shared docs.
- [ ] GET `/study-room-documents/{studyRoomDocumentId}`: Doc details.
- [ ] PATCH `/study-room-documents/{studyRoomDocumentId}`: Update metadata.
- [ ] DELETE `/study-room-documents/{studyRoomDocumentId}`: Remove shared doc.
- [ ] POST `/study-room-documents/{studyRoomDocumentId}/processing-jobs`: Start collaborative RAG processing.
- [ ] GET `/study-room-documents/{studyRoomDocumentId}/processing-jobs/{jobId}`: Check status.

## 4. GraphQL Module (Queries)
- [ ] `me`: Authenticated user info.
- [ ] `notebooks`: List user notebooks.
- [ ] `notebook(id)`: Detailed notebook view (docs, chats, tests, progress).
- [ ] `chatMessages(chatId)`: personal AI chat history.
- [ ] `studyRooms`: List available rooms.
- [ ] `studyRoom(id)`: Detailed room view (members, docs, channels).
- [ ] `studyRoomChannelMessages(channelId)`: Room chat history.
- [ ] `studyRoomAiChatMessages(chatId)`: Room AI chat history.
- [ ] `progressDashboard`: Learning metrics (mastered topics, performance).

## 5. GraphQL Module (Mutations)
### Notebooks & Tags
- [ ] `createNotebook`
- [ ] `updateNotebook`
- [ ] `deleteNotebook`
- [ ] `createNotebookTag`
- [ ] `updateNotebookTag`
- [ ] `deleteNotebookTag`

### AI & Generative (Personal)
- [ ] `createNotebookChat`: New AI conversation.
- [ ] `sendNotebookChatMessage`: Send message + RAG response.
- [ ] `createLearningResource`: Generate summary, flashcards, or tests.
- [ ] `submitMockTestResult`: Grade and store test results.

### Study Rooms & Collaboration
- [ ] `createStudyRoom`
- [ ] `updateStudyRoom`
- [ ] `deleteStudyRoom`
- [ ] `addStudyRoomMember`
- [ ] `updateStudyRoomMember`
- [ ] `createStudyRoomChannel`
- [ ] `sendStudyRoomChannelMessage`

### AI & Generative (Collab)
- [ ] `createStudyRoomAiChat`
- [ ] `sendStudyRoomAiChatMessage`: Validated member message + RAG.
- [ ] `createStudyRoomLearningResource`: Shared summary/flashcards/tests.

## 6. Infrastructure & Data Models
- [ ] Database Schema Setup (PostgreSQL + pgvector).
- [ ] Vector Embedding Integration (OpenAI/Ollama/HuggingFace).
- [ ] RAG Engine (Chunking, Retrieval).
- [ ] Supabase Configuration & Integration.
- [ ] Global Logging System (Request ID, Traceability).
- [ ] Rate Limiting (Prevent abuse).

## 7. Security & Protection
- [ ] SQL Injection Protection (Parameterized queries/ORM).
- [ ] XSS Protection (Output sanitization).
- [ ] CSRF Protection (Standard middleware).
- [ ] IDOR Protection (Resource ownership validation).
- [ ] Secure Authentication (JWT, MFA, Password hashing).
- [ ] Configuration Protection (Env vars, secrets management).
- [ ] Security Headers (HSTS, CSP, X-Frame-Options).
- [ ] HTTPS Enforcement.
