# Cotizador de envíos

Implementación de la fase 1 con frontend React, API FastAPI y PostgreSQL.

## Requisitos

- Git
- Docker con Docker Compose

## Ejecución

```bash
docker compose up --build
```

El comando ejecuta las migraciones y carga de forma idempotente los CSV de ejemplo antes
de iniciar la API. La aplicación queda lista para cotizar sin pasos manuales adicionales:
4 paqueterías y 80 tarifas confiables quedan disponibles; las filas dudosas se conservan
en el reporte de importación, pero no participan en las cotizaciones.

## Pruebas

```bash
docker compose run --rm --build backend sh -c "ruff check . && pytest -q" && docker compose run --rm --build frontend-test
```

Servicios disponibles:

- Aplicación con Docker: <http://localhost:8080>
- API: <http://localhost:8000/api/health>
- Documentación de la API: <http://localhost:8000/docs>

## Acceso comercial

- Usuario: `comercial`
- Contraseña: `comercial123`

Las credenciales pueden cambiarse mediante `COMMERCIAL_USERNAME` y
`COMMERCIAL_PASSWORD`. La sesión se guarda en una cookie firmada y `HttpOnly`. Para un
entorno distinto de desarrollo se debe establecer un `SESSION_SECRET` propio.

## Arquitectura

El backend mantiene un flujo sencillo por capas:

```text
API routes -> services -> repositories -> PostgreSQL
```

- `api/routes`: HTTP, autenticación, archivos y respuestas.
- `services`: reglas de sesión, lectura, limpieza y validación de tarifas.
- `repositories`: consultas SQL mediante Psycopg 3.
- `schemas`: contratos de entrada y salida.

El frontend se organiza por funcionalidad (`auth`, `admin` y `quote`) y consume la API a
través de `/api`.

## Carga de datos

Comercial puede cargar `paqueterias.csv` y `tarifas.csv` de forma independiente. El proceso
es idempotente por contenido y registra cada fila como cargada, corregida, rechazada o
duplicada, junto con el motivo y los cambios aplicados. Los valores ambiguos o sospechosos
se rechazan en lugar de inventar una tarifa.

## Cotización pública

La ruta raíz presenta un cotizador de tres pasos. La API consulta y almacena los códigos
postales, calcula la zona por distancia, busca tarifas activas y devuelve las opciones
disponibles. El lead y cada cotización quedan registrados incluso cuando no existe una
opción compatible, para que Comercial pueda dar seguimiento.

Endpoint público: `POST /api/quotes`.

## Documentación de la entrega

- [`ENTREGA_FASE_1.md`](./ENTREGA_FASE_1.md): mensaje para Comercial.
- [`DATOS_PENDIENTES.md`](./DATOS_PENDIENTES.md): filas que requieren confirmación.
- [`DECISIONES.md`](./DECISIONES.md): supuestos funcionales y técnicos.

