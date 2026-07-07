# Guia para contribuir como desarrollador

Esta guia describe el patron actual para agregar o modificar CRUDs por agregado. El proyecto usa una separacion cercana a Clean Architecture: la API conoce FastAPI, application orquesta casos de uso, domain define contratos/reglas, e infra implementa persistencia.

## Capas actuales

- `app/api`: routers FastAPI y dependency injection. Solo valida entrada HTTP, arma contratos Pydantic y delega.
- `app/application/usecases`: casos de uso por recurso o relacion. Orquestan reglas, servicios y repositorios.
- `app/domain/schemas/entities.py`: contratos Pydantic base para `Create` y `Update`.
- `app/domain/schemas/resources`: contratos Pydantic especificos por recurso: request, path, repository request, read y response.
- `app/domain/interfaces`: Protocols de repositorio por recurso. Cada metodo espera su contrato especifico.
- `app/domain/services`: reglas de dominio reutilizables por agregado.
- `app/infra/repositories`: implementaciones Supabase por recurso.
- `app/core`: configuracion, logging y excepciones tipadas.
- `tests`: pruebas unitarias y de integracion.

## Regla principal

Cada funcion nueva debe recibir un contrato Pydantic explicito. No usar `dict` como request de entrada en API, use case o repositorio si existe un contrato del recurso.

Correcto:

```python
async def update(self, request: UserRepositoryUpdateRequest) -> dict | None:
    ...
```

Incorrecto:

```python
async def update(self, user_id: str, payload: dict) -> dict | None:
    ...
```

## Patron de archivos por recurso

Para un recurso `books`, el patron esperado es:

```text
app/api/v1/resources/books.py
app/application/usecases/books.py
app/domain/interfaces/books.py
app/domain/schemas/resources/books.py
app/infra/repositories/books.py
```

Si el recurso tiene reglas propias, agregar:

```text
app/domain/services/books.py
```

Tambien se registran imports o providers en:

```text
app/api/v1/resources/__init__.py
app/api/dependencies.py
app/application/usecases/__init__.py
app/domain/interfaces/__init__.py
app/domain/services/__init__.py
app/infra/repositories/__init__.py
```

## Contratos Pydantic

Los contratos se separan por responsabilidad:

- `BookCreate` y `BookUpdate`: viven en `app/domain/schemas/entities.py`.
- `BookRead`: forma del dato que sale en respuesta.
- `BookResponse`: respuesta de item, con `data: BookRead`.
- `BookListResponse`: respuesta de lista, con `data`, `limit` y `offset`.
- `BookListRequest`: query params de lista.
- `BookPath`: parametros de ruta.
- `BookCreateRequest`, `BookUpdateRequest`, `BookDeleteRequest`: contratos que consume el use case.
- `BookRepositoryCreateRequest`, `BookRepositoryUpdateRequest`, etc.: contratos que consume el repositorio.

No crear contratos genericos tipo `CrudItemResponse`, `CrudListResponse` o `RepositoryUpdateRequest` compartidos entre todos los recursos. Cada recurso debe tener su contrato propio aunque el shape sea parecido.

## Flujo de una solicitud

1. Router recibe HTTP y payload tipado.
2. Router construye request del caso de uso.
3. Use case ejecuta reglas y llama al servicio de dominio si aplica.
4. Use case construye request especifico del repositorio.
5. Repositorio persiste en Supabase.
6. Use case devuelve response especifico del recurso.

Ejemplo de direccion de dependencias:

```text
api -> application -> domain interfaces/schemas
infra -> domain interfaces/schemas
domain -> no depende de api, application ni infra
```

La capa `application` no debe conocer detalles de Supabase. La capa `domain` no debe importar FastAPI.

## Use cases

Un use case debe:

- Recibir un repositorio por interfaz de dominio.
- Recibir un servicio de dominio cuando haya reglas de negocio.
- Aceptar contratos Pydantic en cada metodo publico.
- Convertir requests de application a requests de repositorio.
- Levantar errores tipados de `app/core/exceptions.py`.
- Devolver responses especificos del recurso.

Patron:

```python
class BookUseCase:
    def __init__(self, repository: BookRepository, service: BookService | None = None) -> None:
        self.repository = repository
        self.service = service or BookService()

    async def update(self, request: BookUpdateRequest) -> BookResponse:
        payload = self.service.prepare_update(request)
        item = await self.repository.update(
            BookRepositoryUpdateRequest(
                book_id=payload.book_id,
                payload=payload.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if item is None:
            raise ResourceNotFoundError()
        return BookResponse(data=BookRead(**item))
```

## Servicios de dominio

Crear un servicio cuando exista regla de negocio, normalizacion o validacion que no sea solo persistencia.

Ejemplos actuales:

- `UserService`: normaliza email y evita updates vacios.
- `NotebookService`: normaliza nombre y evita updates vacios.
- `DocumentService`: reglas de documento y update no vacio.
- `ExamService`: normaliza examen y reglas al asociar preguntas.
- `AttemptService`: valida updates.

No meter reglas de negocio en routers ni repositorios.

## Repositorios

Cada repositorio debe implementar su `Protocol` especifico y recibir contratos propios del recurso.

Reglas:

- No depender de contratos genericos.
- No recibir payloads sueltos como `dict`.
- No aplicar reglas de negocio.
- Traducir contratos Pydantic a payload Supabase con `model_dump`.
- Mantener nombres de tabla e ids cerca del repositorio del recurso.

`app/infra/repositories/base.py` solo contiene helpers de infraestructura. No es contrato de dominio.

## Routers REST

Los routers deben ser delgados.

Patron CRUD:

```python
@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate,
    use_case: Annotated[BookUseCase, Depends(get_books_use_case)],
) -> BookResponse:
    return await use_case.create(BookCreateRequest(payload=payload))
```

Para relaciones, preferir rutas anidadas cuando el recurso padre sea parte natural de la operacion:

```text
POST /rooms/{room_id}/members
DELETE /rooms/{room_id}/members/{member_id}
POST /notebooks/{notebook_id}/tags/{tag_id}
DELETE /notebooks/{notebook_id}/tags/{tag_id}
```

No crear endpoints planos para relaciones si la relacion se entiende mejor desde el agregado padre.

## Errores

Los errores expuestos por API deben estar en espanol.

Usar excepciones de `app/core/exceptions.py`:

- `ResourceNotFoundError`: recurso no encontrado.
- `EmptyPayloadError`: `PATCH` sin campos.
- `RepositoryError`: fallo de persistencia.
- `UnknownResourceError`: ruta o recurso no soportado por logica.

Si agregas un error nuevo, debe tener mensaje seguro en espanol y handler compatible con `ApiError`.

## Responses

Cada endpoint debe usar `response_model` especifico:

Correcto:

```python
@router.get("", response_model=UserListResponse)
@router.get("/{user_id}", response_model=UserResponse)
```

Incorrecto:

```python
@router.get("", response_model=CrudListResponse)
@router.get("/{user_id}", response_model=CrudItemResponse)
```

Los responses deben vivir en `app/domain/schemas/resources/<recurso>.py`.

## Checklist para agregar CRUD

1. Revisar migracion y confirmar tabla, llave primaria, campos requeridos, defaults y relaciones.
2. Crear `Create` y `Update` en `app/domain/schemas/entities.py`.
3. Crear schemas del recurso en `app/domain/schemas/resources/<recurso>.py`.
4. Crear `Protocol` en `app/domain/interfaces/<recurso>.py`.
5. Crear servicio de dominio si hay reglas.
6. Crear use case en `app/application/usecases/<recurso>.py`.
7. Crear repositorio en `app/infra/repositories/<recurso>.py`.
8. Crear router en `app/api/v1/resources/<recurso>.py`.
9. Registrar providers en `app/api/dependencies.py`.
10. Registrar router en `app/api/v1/resources/__init__.py`.
11. Exportar clases en los `__init__.py` necesarios.
12. Agregar tests del use case y del contrato relevante.
13. Ejecutar verificacion.

## Verificacion local

Comandos esperados antes de abrir PR:

```bash
python -m compileall app tests
uv run pytest
uv run ruff check app tests
```

Si cambias contratos HTTP, revisar tambien `/docs` o el OpenAPI generado para confirmar que los `response_model` sean especificos del recurso.

## Convenciones

- Mantener archivos separados por recurso.
- Mantener mensajes de API en espanol.
- Usar UUID para ids.
- Usar `extra="forbid"` en requests para bloquear campos no esperados.
- No exponer campos sensibles en responses. Ejemplo: `hash_password`.
- Evitar refactors ajenos al recurso que se esta tocando.
- Mantener tests enfocados al comportamiento agregado.
