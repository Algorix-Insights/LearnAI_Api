# Guia de consumo de API

Estado actual: la aplicacion expone CRUD, relaciones entre agregados, upload de archivos, vectorizacion RAG sincrona y conversaciones con LLM por notebook. La autenticacion fina todavia no forma parte de esta guia; los endpoints multitenant reciben `user_id` para validar acceso a notebooks personales o notebooks de study rooms.

## Base

- Base local: `http://127.0.0.1:8000`
- Prefijo versionado: `/api/v1`
- Swagger/OpenAPI: `/docs`
- Health checks: `/health` y `/api/v1/health`
- Content-Type esperado: `application/json`
- Uploads: `multipart/form-data`

Ejemplo:

```bash
curl http://127.0.0.1:8000/api/v1/users?limit=20&offset=0
```

## Respuestas

Las respuestas de item usan el contrato especifico del recurso:

```json
{
  "data": {
    "user_id": "00000000-0000-0000-0000-000000000000",
    "name": "Carlos",
    "last_name": "Gonzalez",
    "email": "carlos@example.com",
    "streak": 0,
    "status": "active"
  }
}
```

Las respuestas de lista incluyen paginacion:

```json
{
  "data": [],
  "limit": 100,
  "offset": 0
}
```

Los endpoints `DELETE` devuelven el registro eliminado cuando la base de datos lo retorna.

## Errores

Los mensajes de error del API se devuelven en espanol.

Errores de dominio o repositorio:

```json
{
  "detail": "Recurso no encontrado."
}
```

Errores de validacion:

```json
{
  "detail": "La solicitud no es valida.",
  "errors": [
    {
      "field": "body.email",
      "type": "missing"
    }
  ]
}
```

Codigos principales:

- `200`: consulta, actualizacion o eliminacion correcta.
- `201`: creacion correcta.
- `400`: payload vacio en operaciones `PATCH`.
- `403`: usuario sin acceso al notebook solicitado.
- `404`: recurso no encontrado.
- `422`: request invalido por contrato Pydantic.
- `500`: error de persistencia.

## Paginacion

Los listados aceptan query params:

- `limit`: entero entre `1` y `500`. Default: `100`.
- `offset`: entero mayor o igual a `0`. Default: `0`.
- `page`: entero mayor o igual a `1`. Si se envia, calcula `offset`.
- `per_page`: entero entre `1` y `500`. Alias de `limit` cuando se usa con `page`.

Ejemplo:

```bash
curl "http://127.0.0.1:8000/api/v1/notebooks?limit=50&offset=0"
```

Tambien se puede paginar por pagina:

```bash
curl "http://127.0.0.1:8000/api/v1/notebooks?page=2&per_page=25"
```

## Filtros

Los listados aceptan filtros genericos por query params. El filtro simple usa igualdad:

```bash
curl "http://127.0.0.1:8000/api/v1/users?status=active"
```

Los operadores soportados usan el formato `campo__operador=valor`:

- `eq`: igual. Tambien es el default si no se envia operador.
- `neq`: distinto.
- `gt`, `gte`, `lt`, `lte`: comparaciones.
- `like`, `ilike`: patrones PostgREST.
- `in`: lista separada por coma.
- `is`: `null`, `true` o `false`.

Ejemplos:

```bash
curl "http://127.0.0.1:8000/api/v1/notebooks?grade__gte=3&status__in=active,draft"
curl "http://127.0.0.1:8000/api/v1/users?email__ilike=%25@example.com"
```

## CRUD por recurso

Todos estos recursos siguen el mismo patron REST:

| Recurso | Listar | Crear | Obtener | Actualizar | Eliminar |
| --- | --- | --- | --- | --- | --- |
| Users | `GET /api/v1/users` | `POST /api/v1/users` | `GET /api/v1/users/{user_id}` | `PATCH /api/v1/users/{user_id}` | `DELETE /api/v1/users/{user_id}` |
| Notebooks | `GET /api/v1/notebooks` | `POST /api/v1/notebooks` | `GET /api/v1/notebooks/{notebook_id}` | `PATCH /api/v1/notebooks/{notebook_id}` | `DELETE /api/v1/notebooks/{notebook_id}` |
| Rooms | `GET /api/v1/rooms` | `POST /api/v1/rooms` | `GET /api/v1/rooms/{room_id}` | `PATCH /api/v1/rooms/{room_id}` | `DELETE /api/v1/rooms/{room_id}` |
| Study members | `GET /api/v1/study-members` | `POST /api/v1/study-members` | `GET /api/v1/study-members/{member_id}` | `PATCH /api/v1/study-members/{member_id}` | `DELETE /api/v1/study-members/{member_id}` |
| Exams | `GET /api/v1/exams` | `POST /api/v1/exams` | `GET /api/v1/exams/{exam_id}` | `PATCH /api/v1/exams/{exam_id}` | `DELETE /api/v1/exams/{exam_id}` |
| Questions | `GET /api/v1/questions` | `POST /api/v1/questions` | `GET /api/v1/questions/{question_id}` | `PATCH /api/v1/questions/{question_id}` | `DELETE /api/v1/questions/{question_id}` |
| Question options | `GET /api/v1/question-options` | `POST /api/v1/question-options` | `GET /api/v1/question-options/{option_id}` | `PATCH /api/v1/question-options/{option_id}` | `DELETE /api/v1/question-options/{option_id}` |
| Attempts | `GET /api/v1/attempts` | `POST /api/v1/attempts` | `GET /api/v1/attempts/{attempt_id}` | `PATCH /api/v1/attempts/{attempt_id}` | `DELETE /api/v1/attempts/{attempt_id}` |
| User answers | `GET /api/v1/user-answers` | `POST /api/v1/user-answers` | `GET /api/v1/user-answers/{answer_id}` | `PATCH /api/v1/user-answers/{answer_id}` | `DELETE /api/v1/user-answers/{answer_id}` |
| Flashcards | `GET /api/v1/flashcards` | `POST /api/v1/flashcards` | `GET /api/v1/flashcards/{flashcard_id}` | `PATCH /api/v1/flashcards/{flashcard_id}` | `DELETE /api/v1/flashcards/{flashcard_id}` |
| Documents | `GET /api/v1/documents` | `POST /api/v1/documents` | `GET /api/v1/documents/{document_id}` | `PATCH /api/v1/documents/{document_id}` | `DELETE /api/v1/documents/{document_id}` |
| Document chunks | `GET /api/v1/document-chunks` | `POST /api/v1/document-chunks` | `GET /api/v1/document-chunks/{chunk_id}` | `PATCH /api/v1/document-chunks/{chunk_id}` | `DELETE /api/v1/document-chunks/{chunk_id}` |
| Tags | `GET /api/v1/tags` | `POST /api/v1/tags` | `GET /api/v1/tags/{tag_id}` | `PATCH /api/v1/tags/{tag_id}` | `DELETE /api/v1/tags/{tag_id}` |

## Relaciones REST

Estas rutas modelan relaciones entre agregados:

| Relacion | Crear relacion | Eliminar relacion |
| --- | --- | --- |
| Usuario - notebook personal | `POST /api/v1/users/{user_id}/notebooks/{notebook_id}` | `DELETE /api/v1/users/{user_id}/notebooks/{notebook_id}` |
| Notebook - tag | `POST /api/v1/notebooks/{notebook_id}/tags/{tag_id}` | `DELETE /api/v1/notebooks/{notebook_id}/tags/{tag_id}` |
| Room - member | `POST /api/v1/rooms/{room_id}/members` | `DELETE /api/v1/rooms/{room_id}/members/{member_id}` |
| Room - notebook | `POST /api/v1/rooms/{room_id}/notebooks` | `DELETE /api/v1/rooms/{room_id}/notebooks/{notebook_id}` |
| Exam - question | `POST /api/v1/exams/{exam_id}/questions` | `DELETE /api/v1/exams/{exam_id}/questions/{question_id}` |

Body para `POST /rooms/{room_id}/members`:

```json
{
  "member_id": "00000000-0000-0000-0000-000000000000",
  "role": "user"
}
```

Roles de study rooms:

- `admin`: administra la sala y sus notebooks.
- `user`: miembro regular de la sala.

Body para `POST /rooms/{room_id}/notebooks`:

```json
{
  "notebook_id": "00000000-0000-0000-0000-000000000000",
  "created_by": "00000000-0000-0000-0000-000000000000"
}
```

Body para `POST /exams/{exam_id}/questions`:

```json
{
  "question_id": "00000000-0000-0000-0000-000000000000",
  "question_order": 1,
  "points": 1
}
```

## Ejemplos de consumo

Crear usuario:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Carlos",
    "last_name": "Gonzalez",
    "email": "carlos@example.com",
    "hash_password": "hash-seguro",
    "streak": 0,
    "status": "active"
  }'
```

Actualizar notebook:

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/notebooks/00000000-0000-0000-0000-000000000000 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Biologia",
    "is_favorite": true
  }'
```

Crear documento tipo nota:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "00000000-0000-0000-0000-000000000000",
    "name": "Apuntes",
    "source_type": "note",
    "content_text": "Contenido del apunte",
    "content_hash": "hash-del-contenido"
  }'
```

## RAG y archivos

Variables requeridas:

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `OPENROUTER_API_KEY`

Variables opcionales:

- `OPENROUTER_CHAT_MODEL`: default `openai/gpt-5.2`
- `OPENROUTER_EMBEDDING_MODEL`: default `openai/text-embedding-3-small`
- `DOCUMENTS_BUCKET`: default `documents`
- `PROFILE_BUCKET`: default `profile`
- `RAG_MATCH_LIMIT`: default `6`

La migracion `003_rag_storage_multitenant.sql` crea los buckets `documents` y `profile`, agrega metadata de foto en `users`, normaliza roles `user/admin` y crea `match_document_chunks` para pgvector.

### Subir documento a notebook

`POST /api/v1/notebooks/{notebook_id}/documents/upload`

Formato: `multipart/form-data`

Campos:

- `user_id`: UUID del usuario que sube el documento.
- `file`: archivo `.pdf`, `.txt` o `.md`.
- `description`: opcional.

Flujo interno:

1. Valida acceso del usuario al notebook.
2. Sube archivo al bucket `documents`.
3. Extrae texto.
4. Divide en chunks.
5. Genera embeddings con OpenRouter.
6. Guarda chunks en `document_chunks`.
7. Marca documento como `completed` o `failed`.

Ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/notebooks/00000000-0000-0000-0000-000000000000/documents/upload \
  -F "user_id=00000000-0000-0000-0000-000000000001" \
  -F "description=Apuntes de biologia" \
  -F "file=@./apuntes.md;type=text/markdown"
```

Respuesta:

```json
{
  "data": {
    "document_id": "00000000-0000-0000-0000-000000000000",
    "notebook_id": "00000000-0000-0000-0000-000000000000",
    "name": "apuntes.md",
    "source_type": "markdown",
    "storage_path": "00000000-0000-0000-0000-000000000000/archivo-apuntes.md",
    "processing_status": "completed",
    "mime_type": "text/markdown",
    "content_hash": "hash",
    "size_bytes": 1200,
    "chunks_count": 3
  }
}
```

### Subir foto de perfil

`POST /api/v1/users/{user_id}/profile-photo`

Formato: `multipart/form-data`

Archivos permitidos: `image/jpeg`, `image/png`, `image/webp`, `image/gif`.

Ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users/00000000-0000-0000-0000-000000000001/profile-photo \
  -F "file=@./avatar.png;type=image/png"
```

Respuesta:

```json
{
  "data": {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "profile_image_path": "00000000-0000-0000-0000-000000000001/profile.png",
    "profile_image_mime_type": "image/png",
    "profile_image_size_bytes": 102400
  }
}
```

## Conversaciones RAG

Cada notebook puede tener varias conversaciones. Cada mensaje del usuario busca contexto en los documentos vectorizados de ese notebook y el LLM responde con base en esos chunks.

Crear conversacion:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/notebooks/00000000-0000-0000-0000-000000000000/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "name": "Dudas de biologia"
  }'
```

Listar conversaciones de notebook:

```bash
curl "http://127.0.0.1:8000/api/v1/notebooks/00000000-0000-0000-0000-000000000000/conversations?user_id=00000000-0000-0000-0000-000000000001&limit=20&offset=0"
```

Enviar mensaje al LLM:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/conversations/00000000-0000-0000-0000-000000000000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "content": "Explica la fotosintesis con base en mis apuntes"
  }'
```

Respuesta:

```json
{
  "data": {
    "message_id": "00000000-0000-0000-0000-000000000000",
    "conversation_id": "00000000-0000-0000-0000-000000000000",
    "role": "assistant",
    "content": "Respuesta del modelo con citas [1].",
    "order_message": 2
  },
  "sources": [
    {
      "chunk_id": "00000000-0000-0000-0000-000000000000",
      "document_id": "00000000-0000-0000-0000-000000000000",
      "document_name": "apuntes.md",
      "similarity": 0.91,
      "content": "Fragmento usado como contexto"
    }
  ]
}
```

Listar mensajes:

```bash
curl "http://127.0.0.1:8000/api/v1/conversations/00000000-0000-0000-0000-000000000000/messages?user_id=00000000-0000-0000-0000-000000000001&limit=50&offset=0"
```

Crear pregunta abierta:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "open",
    "statement": "Explica la fotosintesis.",
    "expected_answer": "Proceso por el cual las plantas convierten luz en energia quimica."
  }'
```

## Reglas de validacion relevantes

- Los ids de ruta y relacion deben ser UUID validos.
- Los `PATCH` no aceptan payload vacio.
- Las preguntas abiertas requieren `expected_answer`.
- Las preguntas `multiple_choice` y `true_false` no aceptan `expected_answer`.
- Un `user-answer` debe tener `selected_option_id` o `answer_text`, pero no ambos.
- En documentos tipo `note`, `content_text` es obligatorio.
- En documentos con origen distinto de `note`, `storage_path` es obligatorio.
- Upload RAG solo acepta `pdf`, `txt` y `md`.
- Chat RAG requiere que el usuario tenga acceso al notebook de la conversacion.
- Fotos de perfil solo aceptan `jpeg`, `png`, `webp` y `gif`.
- `limit`, `offset`, ordenes, puntajes y tiempos respetan limites definidos en Pydantic.

Para el detalle exacto de campos por recurso, usar `/docs` o revisar los contratos en `app/domain/schemas/entities.py` y `app/domain/schemas/resources/`.
