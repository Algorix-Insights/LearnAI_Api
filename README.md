# LearnIA Backend

Backend independiente del MVP de LearnIA, construido con FastAPI y orientado a un dominio modular para RAG, materiales, evaluaciones y progreso.

## Propósito
Este repositorio concentra la logica del servidor, la persistencia, la autenticacion, la integracion con Supabase y los adaptadores hacia proveedores externos de IA.

## Arquitectura
Se recomienda una arquitectura de **monolito modular** con **Clean Architecture** y bordes **hexagonales**.

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
- `src/domain`: reglas de negocio puras, entidades y value objects.
- `src/application`: casos de uso, puertos y DTOs.
- `src/infrastructure`: adaptadores, persistencia e integraciones.
- `src/presentation`: API REST, routers y middleware.
- `src/shared`: utilidades comunes, errores y tipos compartidos.
- `src/config`: configuracion, settings y bootstrap.
- `tests`: pruebas unitarias, integracion y e2e.

## Flujo recomendado
1. La capa `presentation` recibe y valida la solicitud.
2. `application` coordina el caso de uso.
3. `domain` aplica reglas y validaciones de negocio.
4. `infrastructure` persiste o consulta sistemas externos.

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

## Notas utiles
- El backend debe exponer health checks.
- La ingesta de archivos debe ser asíncrona si el volumen crece.
- RLS y autorización deben tratarse como requisitos de primera clase.
