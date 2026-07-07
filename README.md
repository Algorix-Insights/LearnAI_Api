# LearnIA Backend

Backend independiente del MVP de LearnIA, construido con FastAPI y orientado a un dominio modular para RAG, materiales, evaluaciones y progreso.

## Propósito

Este repositorio concentra la logica del servidor, la persistencia, la autenticacion, la integracion con Supabase y los adaptadores hacia proveedores externos de IA.

## Arquitectura

El backend queda configurado como **N-Tier / Layered Architecture** sobre FastAPI, siguiendo el enfoque de capas + Dependency Injection descrito en:

https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo

La prioridad es desarrollar rapido sin perder orden: endpoints delgados, servicios con negocio, DAOs para persistencia y DTOs para mover datos entre capas.

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

- `app/api`: endpoints FastAPI. Deben mapear request/response y delegar a servicios.
- `app/services`: logica de negocio y coordinacion de transacciones.
- `app/daos`: acceso a datos. No hacen commit; eso vive en servicios cuando haya DB.
- `app/dtos`: modelos Pydantic compartidos entre capas.
- `app/dependencies.py`: DependencyService central para armar servicios y DAOs.
- `app/core`: configuracion y settings.
- `tests`: pruebas unitarias, integracion y e2e.

## Flujo recomendado

1. `api` recibe la solicitud HTTP y valida entrada/salida.
2. `dependencies.py` inyecta el servicio con sus DAOs/clientes.
3. `services` ejecuta reglas de negocio y coordina operaciones.
4. `daos` consulta o persiste datos.
5. `dtos` mantiene contratos tipados entre capas.

## Bootstrap actual

- `app/main.py`: punto de entrada ASGI.
- `app/api/v1`: routers versionados.
- `app/dependencies.py`: composicion de servicios.
- `app/core/config.py`: settings desde variables de entorno.
- `app/services/health.py`: ejemplo minimo de servicio.
- `app/dtos/health.py`: ejemplo minimo de DTO.

Health check disponible en:

- `/health`: probes de infraestructura.
- `/api/v1/health`: endpoint versionado.

## Como agregar un modulo rapido

1. Crear DTOs en `app/dtos/<modulo>.py`.
2. Crear servicio en `app/services/<modulo>.py`.
3. Crear DAO en `app/daos/<modulo>.py` solo si usa DB o storage.
4. Registrar constructor en `app/dependencies.py`.
5. Crear router en `app/api/v1/<modulo>.py`.
6. Incluir router en `app/api/v1/router.py`.

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
