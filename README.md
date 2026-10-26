# Cotizador de envíos

Implementación de las fases 1 y 2 con frontend React, API FastAPI y PostgreSQL.

## Requisitos

- Git
- Docker con Docker Compose

## Ejecución

```bash
docker compose up --build
```

El comando ejecuta las migraciones y carga de forma idempotente los CSV de ejemplo antes
de iniciar la API. La aplicación queda lista sin pasos manuales adicionales con 4
paqueterías, 104 tarifas versionadas y 40 cotizaciones históricas. Las filas dudosas de la
fase 1 se conservan en su reporte, pero no participan en nuevas cotizaciones.

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

Comercial puede cargar paqueterías, tarifas y cotizaciones históricas de forma independiente.
El importador de tarifas acepta el formato original y el formato versionado de fase 2 con
`peso_min_kg`, `peso_max_kg`, `precio_mxn` y `vigencia_desde`. El proceso es idempotente por
contenido y registra cada fila como cargada, corregida, rechazada o duplicada, junto con el
motivo y los cambios aplicados. Los valores ambiguos o sospechosos se rechazan en lugar de
inventar una tarifa.

## Cotización pública

La ruta raíz presenta un cotizador de tres pasos. La API normaliza espacios en códigos
postales, calcula la zona por distancia y solicita peso y dimensiones. Desde el 1 de
diciembre de 2026 DHL y FedEx cotizan con el mayor entre peso real y peso volumétrico
(`largo × ancho × alto / 5000`); Estafeta conserva peso real. Las opciones mostradas se
guardan como una copia inmutable con vigencia de 30 días, por lo que un cambio posterior de
tarifas no modifica una cotización existente.

El lead y cada intento quedan registrados incluso cuando no existe una opción compatible.
La vista de Comercial muestra cotizaciones por día, intentos sin opciones, su origen
(público o histórico) y el detalle del precio que se ofreció.

Endpoint público: `POST /api/quotes`.

## Documentación de la entrega

- [`ENTREGA_FASE_1.md`](./ENTREGA_FASE_1.md): mensaje para Comercial.
- [`ENTREGA_FASE_2.md`](./ENTREGA_FASE_2.md): resumen de mantenimiento para stakeholders.
- [`DATOS_PENDIENTES.md`](./DATOS_PENDIENTES.md): filas que requieren confirmación.
- [`DECISIONES.md`](./DECISIONES.md): supuestos funcionales y técnicos.

