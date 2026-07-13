# Guía de consumo de la API

Esta guía describe el contrato público que debe usar frontend para perfil, cuadernos, salas, RAG, evaluaciones y estadísticas. La identidad siempre se obtiene del JWT: no envíes `user_id`, `created_by`, `score`, `is_correct` ni campos de propiedad en el body.

## Base y autenticación

- Base local: `http://127.0.0.1:8000`
- Prefijo: `/api/v1`
- OpenAPI: `/docs`
- Health checks: `/health` y `/api/v1/health`
- JSON: `Content-Type: application/json`
- Archivos: `multipart/form-data`

Salvo `/auth/*` y los health checks, todas las rutas requieren el access token de Supabase:

```http
Authorization: Bearer <access_token>
```

Ejemplo base:

```bash
curl http://127.0.0.1:8000/api/v1/users/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Las respuestas de un recurso usan `{ "data": ... }`. Los listados agregan `limit` y `offset`.

```json
{
  "data": [],
  "limit": 100,
  "offset": 0
}
```

### OTP, registro passwordless y SMTP

- El rate limit local de autenticación está desactivado por defecto con
  `AUTH_RATE_LIMIT_ENABLED=false`. Puede reactivarse explícitamente en entornos que tengan un
  proxy o almacenamiento compartido para los contadores.
- Configurar SMTP propio cambia el transporte del correo, pero no elimina los límites del
  proveedor Supabase Auth. Un `429` emitido por Supabase todavía debe respetar `Retry-After`.
- Un registro sin `password` solo inicia la verificación. La respuesta contiene `access_token: ""` y `user: null`; el usuario y la sesión aparecen después de completar el Magic Link/OTP.
- El frontend puede enviar `captcha_token` en registro, login, OTP, verificación y recuperación cuando CAPTCHA esté habilitado.

## Errores y reintentos

Los errores de dominio tienen una forma estable:

```json
{
  "detail": "Recurso no encontrado."
}
```

Los errores de validación incluyen campos:

```json
{
  "detail": "La solicitud no es valida.",
  "errors": [
    {
      "field": "body.name",
      "type": "missing"
    }
  ]
}
```

Códigos relevantes:

- `200`/`201`: operación correcta.
- `400`: regla de negocio o archivo inválido.
- `401`: JWT ausente, vencido o inválido.
- `403`: el usuario no tiene acceso al recurso.
- `404`: recurso inexistente o ajeno; el API evita revelar recursos de otros usuarios.
- `409`: conflicto de estado, límite de intentos o clave idempotente reutilizada con otro payload.
- `413`: request mayor al límite global configurado.
- `422`: payload no cumple el contrato.
- `429`: límite de frecuencia; respeta el header `Retry-After` y no hagas reintentos inmediatos.
- `503`: autenticación temporalmente no disponible.

## Contratos para las pantallas

| Pantalla o bloque                               | Fuente principal                                                              |
| ----------------------------------------------- | ----------------------------------------------------------------------------- |
| Perfil y avatar del header                      | `GET /users/me`, `GET /users/me/profile-photo`                            |
| Home: próximos vencimientos y racha            | `GET /users/me/statistics` → `upcoming`, `streak`                      |
| Dashboard: calificación, dominio y aprendizaje | `GET /users/me/statistics` → `overview`, `reinforcement`, `learning` |
| Dashboard: tiempo y actividad                   | `GET /users/me/statistics` → `time_by_notebook`, `recent_activity`     |
| Biblioteca                                      | `GET /notebooks`, `GET /tags`                                             |
| Salas de estudio                                | `GET /rooms`                                                                |
| Cuaderno: fuentes                               | upload/listado de documentos RAG                                              |
| Cuaderno: chat y recursos                       | conversaciones, generación de flashcards y exámenes                         |

## Perfil del usuario

### Consultar y editar el perfil propio

```http
GET /api/v1/users/me
PATCH /api/v1/users/me
```

El `PATCH` solo admite los campos editables por el usuario:

```json
{
  "name": "Carlos",
  "last_name": "González"
}
```

El correo, estado, racha, IDs y metadatos de storage no son editables desde este endpoint.

### Subir o reemplazar la foto

```http
POST /api/v1/users/me/profile-photo
Content-Type: multipart/form-data
```

- Campo: `file`.
- Formatos: JPEG, PNG, WebP o GIF.
- Tamaño máximo: 5 MB.
- El contenido real del archivo debe coincidir con el MIME declarado.
- Una nueva foto reemplaza la anterior.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users/me/profile-photo \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@./avatar.png;type=image/png"
```

Respuesta `201`:

```json
{
  "data": {
    "user_id": "b9b031f0-4fd4-4c94-93af-49b9a4561140",
    "storage_path": "b9b031f0-4fd4-4c94-93af-49b9a4561140/profile-c9833dc0-81fd-4232-b982-147222c946ae.png",
    "mime_type": "image/png",
    "size_bytes": 102400,
    "url": "https://...signed-url...",
    "expires_in": 3600
  }
}
```

La `url` es firmada y temporal. No la persistas como URL permanente; solicita otra cuando expire.

### Consultar o eliminar la foto

```http
GET /api/v1/users/me/profile-photo
DELETE /api/v1/users/me/profile-photo
```

El `GET` genera una URL firmada nueva. Si no existe foto devuelve `404`. El `DELETE` responde:

```json
{
  "deleted": true
}
```

## Creación segura de cuadernos y salas

### Crear un cuaderno personal

```http
POST /api/v1/notebooks
```

```json
{
  "name": "Estructuras de datos",
  "description": "Apuntes del semestre",
  "summary": null,
  "is_favorite": false,
  "due_date": "2026-07-30T23:59:00Z"
}
```

Solo `name` es obligatorio. El servidor crea el cuaderno y su vínculo personal en una sola transacción. El propietario proviene del JWT; no se necesita una segunda llamada para asociarlo.

### Crear una sala de estudio

```http
POST /api/v1/rooms
```

```json
{
  "name": "Algoritmos y cadenas",
  "description": "Sala del equipo de estudio"
}
```

El servidor crea la sala, crea la identidad de `study_member` si hace falta y registra al usuario actual como `admin`, todo atómicamente.

### Asociar un cuaderno a una sala

```http
POST /api/v1/rooms/{room_id}/notebooks
```

```json
{
  "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203"
}
```

Solo un administrador de la sala que pueda administrar el cuaderno puede asociarlo. `created_by` se deriva del JWT y no se acepta en el body.

Los listados de cuadernos y salas usan:

```http
GET /api/v1/notebooks?limit=20&offset=0
GET /api/v1/rooms?limit=20&offset=0
```

RLS limita los resultados a recursos accesibles por el usuario autenticado.

## Tags disponibles

### Listar el catálogo del usuario

```http
GET /api/v1/tags?limit=100&offset=0
```

El listado combina las tags globales creadas antes de incorporar propiedad con las tags
privadas del usuario autenticado. Nunca incluye tags privadas de otra cuenta y se ordena por
nombre e identificador. Solo entrega tags activas. Al crear el perfil de aplicación en
`public.users`, un trigger garantiza una tag privada activa llamada `general`; la migración
también incorpora esa tag a los perfiles existentes. Esta creación no requiere cuadernos y no
inserta relaciones en `notebook_tags`.

```json
{
  "data": [
    {
      "id": "d92f93ec-f6db-43b1-a53e-4fd1d5e34fe3",
      "name": "Universidad",
      "status": "active",
      "scope": "system"
    }
  ],
  "limit": 100,
  "offset": 0
}
```

### Crear una tag privada

```http
POST /api/v1/tags
```

```json
{
  "name": "Algoritmos"
}
```

El servidor recorta espacios y obtiene el propietario exclusivamente del JWT. No envíes
`user_id`, `created_by_user_id` ni `status`; esos campos producen `422`. Toda tag nueva queda
activa. Los nombres son únicos por
usuario sin distinguir mayúsculas, minúsculas ni espacios exteriores. Un duplicado devuelve
`409`; una creación nueva devuelve `201` y `scope: "user"`. Las tags legacy compartidas usan
`scope: "system"`.

## RAG: fuentes y chat

### Cuotas durables de IA

Las operaciones que consumen proveedores de IA tienen cuotas por usuario, persistidas en PostgreSQL. Se comparten entre instancias del API y no se reinician al desplegar o reiniciar el servidor.

| Operación            | Endpoint principal                                    | Por hora móvil |   Por día UTC |
| --------------------- | ----------------------------------------------------- | --------------: | -------------: |
| Chat                  | `POST /conversations/{conversation_id}/messages`    |              30 |            200 |
| Embeddings            | `POST /notebooks/{notebook_id}/documents/upload`    |              20 |            100 |
| Flashcards            | `POST /notebooks/{notebook_id}/flashcards/generate` |              10 |             30 |
| Examen                | `POST /notebooks/{notebook_id}/exams/generate`      |               5 |             15 |
| Calificación abierta | `POST /attempts/{attempt_id}/finish`                |   30 respuestas | 100 respuestas |

Cuando se alcanza una cuota, el API responde `429`:

```json
{
  "detail": "Alcanzaste el límite temporal de operaciones de IA."
}
```

Respeta `Retry-After: 3600`, deshabilita temporalmente la acción en UI y evita ciclos de reintento automático. La reserva se hace antes de llamar al proveedor, por lo que una operación aceptada puede contar aunque el proveedor falle después.

### Subir una fuente al cuaderno

```http
POST /api/v1/notebooks/{notebook_id}/documents/upload
Content-Type: multipart/form-data
```

- `file`: PDF, TXT o Markdown; máximo 10 MB.
- `description`: opcional; máximo 1000 caracteres.
- PDF: máximo 200 páginas.
- El procesamiento es síncrono: extracción, chunks, embeddings y persistencia ocurren antes de responder.
- Si el mismo contenido ya terminó correctamente, se devuelve el documento existente; si quedó en `failed`, se limpia y reprocesa.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/notebooks/$NOTEBOOK_ID/documents/upload \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "description=Apuntes de biología" \
  -F "file=@./apuntes.pdf;type=application/pdf"
```

Respuesta `201`:

```json
{
  "data": {
    "document_id": "98e4612a-1d8d-4e28-b125-0411e45ad30a",
    "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203",
    "name": "apuntes.pdf",
    "source_type": "pdf",
    "processing_status": "completed",
    "mime_type": "application/pdf",
    "size_bytes": 234567,
    "chunks_count": 12
  }
}
```

Para eliminar el documento y su archivo:

```http
DELETE /api/v1/notebooks/{notebook_id}/documents/{document_id}
```

### Conversaciones

Crear una conversación:

```http
POST /api/v1/notebooks/{notebook_id}/conversations
```

```json
{
  "name": "Dudas de biología"
}
```

Listar conversaciones y mensajes:

```http
GET /api/v1/notebooks/{notebook_id}/conversations?limit=20&offset=0
GET /api/v1/conversations/{conversation_id}/messages?limit=50&offset=0
```

Enviar mensaje:

```http
POST /api/v1/conversations/{conversation_id}/messages
```

```json
{
  "content": "Explica la fotosíntesis con base en mis apuntes"
}
```

`content` admite hasta 4000 caracteres. Frontend normalmente debe omitir `model`; el servidor usa el modelo configurado y solo acepta su allowlist.

```json
{
  "data": {
    "message_id": "a8b8ff3d-e339-47bd-ad12-2ba5edb68fe4",
    "conversation_id": "8e876848-2b11-4eed-8eb6-785d2e919115",
    "role": "assistant",
    "content": "Respuesta basada en tus fuentes [1].",
    "order_message": 2,
    "created_at": "2026-07-13T16:30:00Z"
  },
  "sources": [
    {
      "chunk_id": "91864c09-d9f0-4936-86b2-a166175f4963",
      "document_id": "98e4612a-1d8d-4e28-b125-0411e45ad30a",
      "document_name": "apuntes.pdf",
      "similarity": 0.91,
      "content": "Fragmento utilizado como contexto"
    }
  ]
}
```

No envíes `user_id` en multipart, body ni query params. La conversación pertenece al usuario autenticado y no se expone a otros miembros del cuaderno.
Cada turno usa un historial reciente acotado además del contexto recuperado, por lo que las preguntas de seguimiento conservan la conversación.

## Generación de recursos con RAG

El usuario debe poder administrar el cuaderno y este debe tener fuentes procesadas.

### Generar flashcards

```http
POST /api/v1/notebooks/{notebook_id}/flashcards/generate
```

```json
{
  "count": 10
}
```

- `count`: `1..20`; default `10`.
- `model`: opcional y normalmente omitido.
- La generación y persistencia del lote son atómicas.

```json
{
  "data": [
    {
      "flashcard_id": "da702bbc-5a00-4a89-beb3-21d33a03820a",
      "question_id": "0bc04f49-a08f-47fb-a9a6-fcf86ebfa8a1",
      "question": "¿Qué es la fotosíntesis?",
      "answer": "El proceso que convierte energía lumínica en energía química."
    }
  ],
  "sources": []
}
```

Para recuperar las tarjetas persistidas y volver a estudiarlas:

```http
GET /api/v1/notebooks/{notebook_id}/flashcards?limit=100&offset=0
```

El listado incluye `question` y `answer` porque son material de estudio. Las claves de corrección de preguntas pertenecientes a exámenes nunca se entregan por este contrato.

### Generar un examen

```http
POST /api/v1/notebooks/{notebook_id}/exams/generate
```

```json
{
  "name": "Evaluación de fotosíntesis",
  "description": "Repaso de la unidad 1",
  "true_false_count": 3,
  "multiple_choice_count": 4,
  "open_count": 3
}
```

- Cada contador admite `0..10`.
- La suma debe estar entre `1` y `20`.
- Defaults: `3` verdadero/falso, `4` opción múltiple y `3` abiertas.
- `name`, `description` y `model` son opcionales.
- La creación del examen, preguntas, opciones y relaciones es atómica.

La respuesta incluye IDs, enunciados y opciones, pero nunca `expected_answer`, `is_correct` ni el índice de respuesta correcta:

```json
{
  "data": {
    "exam_id": "a2f18c70-fb56-4fc7-8871-ea28ee2fa0d1",
    "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203",
    "name": "Evaluación de fotosíntesis",
    "description": "Repaso de la unidad 1",
    "status": "active",
    "questions": [
      {
        "question_id": "a6f42adf-063c-4151-b2bc-9d23b3b254ca",
        "type": "multiple_choice",
        "statement": "¿Cuál es el producto energético principal?",
        "question_order": 1,
        "options": [
          {
            "option_id": "97db39b8-809f-49e3-aae6-d42cd836ee89",
            "option_text": "Glucosa",
            "option_order": 1
          }
        ]
      }
    ]
  },
  "sources": []
}
```

## Intentos y calificación de exámenes

El flujo público es `iniciar/reanudar → consultar → responder → finalizar`. Solo puede existir un intento `in_progress` por usuario y examen y cada usuario dispone de un máximo de 5 intentos por examen.

### 1. Iniciar

```http
POST /api/v1/exams/{exam_id}/attempts
```

Body requerido:

```json
{}
```

Respuesta `201`:

```json
{
  "data": {
    "attempt_id": "6b395c9e-9d10-4f01-987f-a059986d338f",
    "exam_id": "a2f18c70-fb56-4fc7-8871-ea28ee2fa0d1",
    "status": "in_progress",
    "attempt_number": 1,
    "max_attempts": 5,
    "attempts_remaining": 4,
    "started_at": "2026-07-13T16:40:00Z",
    "questions": [
      {
        "question_id": "a6f42adf-063c-4151-b2bc-9d23b3b254ca",
        "type": "multiple_choice",
        "statement": "¿Cuál es el producto energético principal?",
        "question_order": 1,
        "points": 1,
        "options": [
          {
            "option_id": "97db39b8-809f-49e3-aae6-d42cd836ee89",
            "option_text": "Glucosa",
            "option_order": 1
          }
        ]
      }
    ],
    "answers": []
  }
}
```

El `POST` es recuperable: si ya existe un intento activo, devuelve esa misma sesión y sus respuestas en lugar de crear otro. Tras completar el quinto intento, un nuevo inicio devuelve `409`.

### 2. Consultar o recuperar la sesión

```http
GET /api/v1/attempts/{attempt_id}
```

Devuelve el mismo contrato de sesión, incluyendo las respuestas guardadas, sin claves de corrección.

### 3. Crear o reemplazar una respuesta

```http
PUT /api/v1/attempts/{attempt_id}/answers/{question_id}
```

Para opción múltiple o verdadero/falso:

```json
{
  "selected_option_id": "97db39b8-809f-49e3-aae6-d42cd836ee89"
}
```

Para pregunta abierta:

```json
{
  "answer_text": "Las plantas convierten la luz en energía química."
}
```

Envía exactamente uno de los dos campos. Un segundo `PUT` sobre la misma pregunta reemplaza la respuesta mientras el intento siga activo. La respuesta guardada no incluye todavía `is_correct` ni puntos.

### 4. Finalizar y calificar

```http
POST /api/v1/attempts/{attempt_id}/finish
```

Body requerido:

```json
{}
```

```json
{
  "data": {
    "attempt_id": "6b395c9e-9d10-4f01-987f-a059986d338f",
    "exam_id": "a2f18c70-fb56-4fc7-8871-ea28ee2fa0d1",
    "status": "completed",
    "attempt_number": 1,
    "max_attempts": 5,
    "attempts_remaining": 4,
    "score": 80,
    "earned_points": 8,
    "total_points": 10,
    "answered_questions": 10,
    "total_questions": 10,
    "completed_at": "2026-07-13T16:55:00Z",
    "spent_time": 900,
    "answers": [
      {
        "answer_id": "8c93f257-770f-462b-b360-4c59770c60d5",
        "question_id": "a6f42adf-063c-4151-b2bc-9d23b3b254ca",
        "is_correct": true,
        "points_awarded": 1,
        "confidence": 0.96,
        "feedback": "La respuesta identifica correctamente el concepto central."
      }
    ]
  }
}
```

El servidor calcula tiempo, aciertos, puntos y porcentaje. Las preguntas cerradas se comparan contra su opción interna; las abiertas usan verificación semántica y, si el proveedor no está disponible, una comparación determinista segura. `confidence` y `feedback` pueden ser `null` cuando no hubo verificación semántica. Un intento finalizado no acepta más respuestas ni una segunda finalización.

Si una respuesta cambia de forma concurrente mientras se finaliza, el API devuelve `409`: vuelve a consultar la sesión y repite la finalización. Esto evita calificar una fotografía inconsistente de las respuestas.

## Estadísticas de usuario

### Obtener el dashboard

```http
GET /api/v1/users/me/statistics?period=week&timezone=America%2FCancun
```

Query params:

- `period`: `week` (default), `month` o `all`. `all` genera la serie diaria de los últimos 365 días.
- `timezone`: zona IANA; default `UTC`. Controla agrupación diaria y racha.

`period` afecta la serie `learning`; los totales, dominio, próximos vencimientos, racha, distribución de tiempo y actividad reciente se calculan con los datos accesibles del usuario.

```json
{
  "data": {
    "overview": {
      "average_score": 82.5,
      "completed_exams": 6,
      "total_exams": 8,
      "notebooks_dominated": 2,
      "total_notebooks": 4,
      "total_study_seconds": 25200
    },
    "reinforcement": [
      {
        "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203",
        "name": "Estructuras de datos",
        "mastery_percent": 65,
        "flashcards_count": 32,
        "exams_count": 4
      }
    ],
    "learning": [
      {
        "date": "2026-07-13",
        "exams_completed": 1,
        "flashcards_reviewed": 24,
        "study_minutes": 90
      }
    ],
    "upcoming": [
      {
        "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203",
        "name": "Estructuras de datos",
        "due_date": "2026-07-16T23:59:00Z"
      }
    ],
    "streak": {
      "current_days": 7,
      "best_days": 15,
      "days": [
        {
          "date": "2026-07-13",
          "active": true
        }
      ]
    },
    "time_by_notebook": [
      {
        "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203",
        "name": "Estructuras de datos",
        "study_seconds": 16200,
        "percentage": 64.29
      }
    ],
    "recent_activity": [
      {
        "activity_type": "flashcard_reviewed",
        "occurred_at": "2026-07-13T16:20:00Z",
        "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203",
        "notebook_name": "Estructuras de datos",
        "description": "Repasaste 24 flashcards",
        "quantity": 24,
        "duration_seconds": 1200
      }
    ],
    "generated_at": "2026-07-13T16:30:00Z"
  }
}
```

Las listas pueden venir vacías. Frontend debe renderizar `0` y estados vacíos sin asumir que habrá actividad.

### Registrar actividad de estudio

```http
POST /api/v1/users/me/learning-events
Idempotency-Key: <clave-única>
```

Usa un UUID nuevo por acción como `Idempotency-Key`. El formato admite de 16 a 128 caracteres: letras, números, `.`, `_`, `:`, `-` y debe iniciar con letra o número.

Sesión de estudio:

```json
{
  "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203",
  "activity_type": "study_session",
  "quantity": 1,
  "duration_seconds": 1800
}
```

Repaso de flashcards:

```json
{
  "notebook_id": "ccf100d6-b95a-479f-9e6a-bdff8c8fb203",
  "activity_type": "flashcard_reviewed",
  "quantity": 24,
  "duration_seconds": 1200
}
```

Reglas:

- `study_session`: `quantity=1`, duración entre 30 y 14 400 segundos.
- `flashcard_reviewed`: `quantity=1..50`, duración entre 0 y 3600 segundos.
- El usuario debe tener acceso al cuaderno.
- Repetir la misma clave con el mismo payload devuelve el evento original, sin duplicar estadísticas.
- Reutilizarla con otro payload devuelve `409`.
- Ante `429`, conserva la misma clave para el reintento y respeta `Retry-After`.

El backend registra automáticamente eventos de fuente subida, recurso generado y cuaderno compartido. El frontend solo debe enviar sesiones de estudio y repasos de flashcards para evitar duplicados.

## Endpoints retirados o restringidos

Frontend no debe consumir los contratos antiguos siguientes:

| Contrato antiguo                                                 | Reemplazo                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------- |
| `POST /users`, `DELETE /users/{user_id}`                     | Supabase Auth administra el ciclo de vida de la cuenta              |
| `PATCH /users/{user_id}`                                       | `PATCH /users/me`                                                 |
| `POST /users/{user_id}/profile-photo`                          | `POST /users/me/profile-photo`                                    |
| Relaciones manuales`/users/{user_id}/notebooks/...`            | `POST /notebooks` crea propiedad atómicamente                    |
| `POST /exams`, `POST /questions`, `POST /question-options` | `POST /notebooks/{notebook_id}/exams/generate`                    |
| CRUD genérico`/attempts`                                      | Flujo`/exams/{exam_id}/attempts` y `/attempts/{attempt_id}/...` |
| CRUD`/user-answers`                                            | `PUT /attempts/{attempt_id}/answers/{question_id}`                |
| `POST /flashcards`                                             | `POST /notebooks/{notebook_id}/flashcards/generate`               |
| `POST /documents` y escritura de `/document-chunks`          | Upload RAG del notebook                                             |

`GET /users` y `GET /users/{user_id}` permanecen solo como compatibilidad y nunca enumeran perfiles ajenos. Para el producto usa siempre `GET /users/me`.

Para campos menos comunes y respuestas completas, la referencia canónica es `/docs` y los contratos de `app/domain/schemas/resources/`.
