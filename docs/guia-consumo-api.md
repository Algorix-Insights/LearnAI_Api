# Guia de consumo de API

Estado actual: la aplicacion expone solamente CRUD y operaciones de relacion entre agregados. Las rutas de RAG, generacion con IA, autenticacion fina y flujos asincronos todavia no forman parte de esta guia.

## Base

- Base local: `http://127.0.0.1:8000`
- Prefijo versionado: `/api/v1`
- Swagger/OpenAPI: `/docs`
- Health checks: `/health` y `/api/v1/health`
- Content-Type esperado: `application/json`

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
  "role": "member"
}
```

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
- `limit`, `offset`, ordenes, puntajes y tiempos respetan limites definidos en Pydantic.

Para el detalle exacto de campos por recurso, usar `/docs` o revisar los contratos en `app/domain/schemas/entities.py` y `app/domain/schemas/resources/`.
