# LearnIA Backend

Backend independiente del MVP de LearnIA, construido con FastAPI y orientado a un dominio modular para RAG, materiales, evaluaciones y progreso.

## Propósito

Este repositorio concentra la logica del servidor, la persistencia, la autenticacion, la integracion con Supabase y los adaptadores hacia proveedores externos de IA.

## Documentacion actual

La API expone flujos autenticados y aislados por usuario para perfil, cuadernos, salas, RAG, evaluaciones y progreso. Para consumir o extender esta versión, usa estas guías:

- [Guía de consumo de API](docs/guia-consumo-api.md): contratos para frontend, avatar, RAG, generación, intentos, calificación y estadísticas.
- [Guia para contribuir como desarrollador](docs/guia-contribucion-desarrollador.md): patron de desarrollo por recurso con Clean Architecture, contratos Pydantic, use cases, servicios y repositorios.

## Arquitectura

El backend queda configurado como **Clean Architecture / Layered Architecture** sobre FastAPI, siguiendo separacion de API, casos de uso, dominio e infraestructura.

La prioridad es desarrollar rapido sin perder orden: endpoints delgados, use cases por agregado, servicios de dominio para reglas de negocio, repositorios para persistencia y contratos Pydantic especificos por recurso.

## Patrones de diseño usados

- **Repository Pattern**: abstrae el acceso a datos y desacopla los casos de uso de Postgres/Supabase.
- **Factory Pattern**: construye examenes, flashcards o salidas generadas segun tipo de contenido.
- **Strategy Pattern**: permite intercambiar estrategias de chunking, retrieval o generacion sin tocar el flujo principal.
- **Dependency Injection**: facilita testing y desacople entre application e infrastructure.
- **Adapter**: normaliza la comunicacion con Supabase, LLMs y otros servicios externos.
- **Facade**: expone casos de uso de alto nivel como ingestado de material o generacion de contenido.

## Justificacion

El backend maneja reglas de negocio sensibles y varias integraciones externas. Separar dominio, casos de uso e infraestructura reduce acoplamiento, mejora testabilidad y permite evolucionar el RAG sin rehacer la base del sistema.

## Estructura base

- `app/api`: endpoints FastAPI. Deben mapear request/response y delegar a casos de uso.
- `app/application/usecases`: casos de uso por agregado o relacion REST.
- `app/domain/schemas`: contratos Pydantic de entidades, requests, responses y repositorios.
- `app/domain/interfaces`: contratos `Protocol` de repositorios por recurso.
- `app/domain/services`: reglas de dominio y normalizacion.
- `app/infra/repositories`: acceso a datos con Supabase.
- `app/api/dependencies.py`: providers de dependency injection para armar casos de uso.
- `app/core`: configuracion y settings.
- `tests`: pruebas unitarias, integracion y e2e.

## Flujo recomendado

1. `api` recibe la solicitud HTTP y valida entrada/salida.
2. `app/api/dependencies.py` inyecta el use case con sus repositorios.
3. `application/usecases` orquesta reglas y persistencia.
4. `domain/services` ejecuta reglas de negocio cuando aplica.
5. `infra/repositories` consulta o persiste datos.
6. `domain/schemas` mantiene contratos tipados entre capas.

## Bootstrap actual

- `app/main.py`: punto de entrada ASGI.
- `app/api/v1`: routers versionados.
- `app/api/dependencies.py`: composicion de use cases.
- `app/core/config.py`: settings desde variables de entorno.
- `app/application/services/health.py`: servicio minimo de health.
- `app/domain/schemas`: contratos Pydantic.

Health check disponible en:

- `/health`: probes de infraestructura.
- `/api/v1/health`: endpoint versionado.

## Como agregar un modulo rapido

1. Crear contratos en `app/domain/schemas/entities.py` y `app/domain/schemas/resources/<modulo>.py`.
2. Crear interfaz en `app/domain/interfaces/<modulo>.py`.
3. Crear servicio de dominio en `app/domain/services/<modulo>.py` si hay reglas.
4. Crear use case en `app/application/usecases/<modulo>.py`.
5. Crear repositorio en `app/infra/repositories/<modulo>.py`.
6. Registrar provider en `app/api/dependencies.py`.
7. Crear router en `app/api/v1/resources/<modulo>.py`.
8. Incluir router en `app/api/v1/resources/__init__.py`.

## Git Flow

Se usa **git flow** para ordenar el trabajo por etapas y reducir riesgo en cambios que afectan varias capas del backend.

### Por que usarlo

- **Aisla features**: cada funcionalidad entra en una rama propia, sin mezclar trabajo incompleto con `main`.
- **Protege releases**: `develop` concentra integracion estable antes de promover cambios a produccion.
- **Facilita hotfixes**: correcciones criticas salen rapido desde una rama dedicada sin romper el flujo normal.
- **Mejora revision**: los PR quedan mas pequenos y mas faciles de auditar.
- **Reduce regresiones**: separa desarrollo, preparacion de release y correccion urgente.

### Ramificaciones basicas

- `main`: codigo listo para produccion.
- `develop`: integracion continua del trabajo aprobado.
- `feature/*`: nuevas funcionalidades.
- `release/*`: estabilizacion previa a salida.
- `hotfix/*`: correcciones urgentes sobre produccion.

## Convenciones tecnicas

- Mantener `domain` libre de dependencias de framework.
- No acceder a ORM o storage desde `application` directamente.
- Encapsular llamadas a proveedores externos en `infrastructure`.
- Manejar errores de forma tipada y con mensajes seguros.

## Arranque sugerido

- Instalar dependencias desde `pyproject.toml`.
- Configurar variables en `.env`.
- Ejecutar pruebas y lint antes de abrir PR.

## Guía de Inicio

### Requisitos

- Python 3.12+
- Pip o similar

### Instalación

1. Clonar el repositorio.
2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```bash
   pip install .
   ```

### Ejecución

Para iniciar el servidor de desarrollo:

```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`. Puedes acceder a la documentación interactiva en `/docs`.

### Base de datos Supabase

Las migraciones versionadas viven en `supabase/migrations/`. Esta entrega contiene 12 migraciones timestamped, de `20260713000100_initial_schema.sql` a `20260713001200_ai_usage_quotas.sql`. Antes de aplicar cambios a un proyecto existente, ejecuta `scripts/security_preflight.sql` y revisa cualquier policy ajena a `learnia_*`.

```bash
npx supabase db push --dry-run --db-url "$SUPABASE_SESSION_URL" --include-all
npx supabase db push --db-url "$SUPABASE_SESSION_URL" --include-all
```

El segundo comando modifica la base de datos; úsalo solo después de validar el dry-run en staging.

### Pruebas

```bash
pytest
```

## Notas utiles

- El backend debe exponer health checks.
- La ingesta de archivos debe ser asíncrona si el volumen crece.
- RLS y autorización deben tratarse como requisitos de primera clase.

## Entornos

Staging: [learnaiapistaging.algorixinsights.com](https://learnaiapistaging.algorixinsights.com/health)

Produccion: [learnaiapi.algorixinsights.com](https://learnaiapi.algorixinsights.com/health)
