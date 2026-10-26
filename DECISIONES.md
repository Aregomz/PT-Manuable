# Decisiones — Fase 1

## Administración de datos en dos vistas

La sección interna de Comercial se divide en tres pestañas dentro de **Carga de datos**:

- **Cargar datos:** permite importar y auditar archivos CSV.
- **Datos cargados:** muestra el catálogo y las tarifas que realmente están disponibles en
  PostgreSQL después de aplicar validaciones y correcciones.
- **Leads capturados:** consulta las personas que utilizaron el cotizador y agrupa todas sus
  cotizaciones bajo un único correo electrónico.

El historial no se expande dentro de la tabla de leads. **Ver cotizaciones** abre un modal
con todas las cotizaciones del correo seleccionado, manteniendo una sola fila por lead y
evitando que la tabla cambie de altura durante la consulta.

Se eligió separar la operación de carga de la consulta para que el resultado de una
importación no se confunda con el estado vigente de la base de datos. Una fila rechazada
aparece en el reporte de importación, pero no en la pestaña de datos cargados.

La carga por CSV se conserva para altas y modificaciones masivas. Para ajustes puntuales,
**Datos cargados** permite editar paqueterías y tarifas directamente: Comercial puede
cambiar nombre o servicio, activar o inactivar una paquetería y corregir los campos de una
tarifa sin preparar un archivo nuevo. Las mismas restricciones de integridad se validan en
la API antes de guardar y los cambios afectan las cotizaciones posteriores, no el histórico.

## Importaciones independientes

`paqueterias.csv` y `tarifas.csv` pueden cargarse por separado. Las paqueterías son el
catálogo maestro y deben existir antes de importar sus tarifas. Si una tarifa referencia
una paquetería inexistente, la fila se rechaza y se explica el motivo; no se crea una
paquetería implícitamente.

Cada importación registra filas cargadas, corregidas, rechazadas y duplicadas. El reporte
devuelve el valor original, el valor normalizado, los cambios aplicados y la razón del
rechazo cuando corresponde.

Si se vuelve a seleccionar exactamente el mismo archivo, se identifica por su checksum y
no se procesa nuevamente. La interfaz informa que no hubo cambios, muestra la fecha de la
importación original y conserva disponible el reporte que se generó en esa ocasión.

## Límites de peso

De manera provisional, un peso situado exactamente en un límite pertenece al rango
anterior: `0–1 kg` incluye `1 kg`; el rango `1–3 kg` aplica cuando el peso es mayor que
`1 kg` y hasta `3 kg`, y así sucesivamente. Los límites se conservan como aparecen en el
CSV, pero la consulta prioriza el rango con el menor límite inferior cuando dos rangos se
tocan. Esta interpretación debe confirmarse con el stakeholder.

## Tarifas dudosas

No se inventan ni corrigen importes ambiguos. Precios faltantes, negativos o claramente
atípicos se rechazan y quedan visibles para confirmación de Comercial.

También se rechazan los dos registros cuando sus rangos se traslapan para la misma
paquetería, zona y vigencia y ofrecen precios distintos. No se selecciona uno de manera
arbitraria: ambos quedan pendientes hasta recibir confirmación de Comercial.

## Cotización pública

El código postal se consulta en Zippopotam y la respuesta normalizada se conserva en una
caché de PostgreSQL. Si el código no existe o el servicio externo falla, la API responde
con un mensaje claro; el usuario nunca queda frente a una pantalla vacía.

La distancia se calcula en línea recta entre las coordenadas de origen y destino mediante
la fórmula de Haversine. Con esa distancia se asigna provisionalmente la zona: hasta 100
km es zona 1, hasta 500 km zona 2, hasta 1,000 km zona 3 y el resto zona 4. Estos umbrales
son una decisión técnica para la prueba y deben confirmarse con el stakeholder.

Para ofrecer opciones se consideran únicamente paqueterías activas y tarifas vigentes que
cubran la zona y el peso solicitados. Una tarifa sin precio nunca se ofrece. Si no existe
una tarifa compatible, se guarda el lead y la cotización sin opciones y se informa que se
está trabajando para llegar a ese trayecto.

El tiempo de entrega es informativo y no determina si una tarifa puede cotizarse. Cuando
la tarifa incluye días mínimos y máximos, la opción muestra su entrega estimada. Si ambos
datos están vacíos, no se presenta un texto de entrega para evitar prometer un plazo que
Comercial no confirmó. Actualmente 19 tarifas utilizables carecen de este dato; Comercial
debe completarlo si necesita mostrar una estimación en todas las opciones.

El correo identifica al lead: un mismo correo puede realizar varias cotizaciones. Cada
cotización guarda una copia de las opciones y precios mostrados para preservar el histórico
aunque posteriormente cambie el catálogo de tarifas.

Después de cotizar, el usuario puede seleccionar una de las tarifas. Los botones
**Continuar al pago** y **Enviar cotización por correo** representan, de manera hipotética,
la conexión con los procesos que Manuable ya utiliza para cobrar y entregar cotizaciones.
Esas integraciones quedan fuera del alcance de la fase 1 y los botones no ejecutan
operaciones externas en esta prueba.

# Decisiones — Fase 2

## Tarifas versionadas y vigencia

Las nuevas tarifas de DHL se guardan como registros adicionales con vigencia desde el 1 de
diciembre de 2026. No se sobrescriben las anteriores: al cotizar se elige la versión más
reciente cuya fecha de inicio no sea posterior a la fecha de la cotización. El importador
acepta el nuevo formato CSV para que futuros cambios de precios o fechas puedan cargarse
sin modificar código.

Cada cotización guarda una referencia externa, fecha de creación, vencimiento a 30 días y
una copia de las opciones, precios, tiempos de entrega y peso facturable mostrados. Por eso
un cambio en el catálogo nunca recalcula ni altera una cotización ya entregada.

## Peso volumétrico

La regla se configura por paquetería con divisor y fecha de inicio. DHL y FedEx usan divisor
5000 desde el 1 de diciembre de 2026; Estafeta no tiene regla activa y continúa con peso
real. El cotizador solicita largo, ancho y alto en centímetros y guarda tanto peso real como
volumétrico. Para una paquetería con la regla activa se busca la tarifa usando el mayor de
ambos. Si una llamada antigua a la API omite dimensiones, esa paquetería no se ofrece desde
la fecha de activación, pero las paqueterías que cobran por peso real siguen disponibles.
El resultado volumétrico se redondea hacia arriba a tres decimales para ajustarse a la
precisión almacenada sin cobrar por debajo del valor calculado.

La configuración aparece en **Datos cargados** y puede editarse junto con la paquetería. La
semilla inicial solo establece la regla una vez; reiniciar el sistema no revierte ajustes
posteriores de Comercial.

## Cotizaciones históricas

Las 40 cotizaciones telefónicas se importan con su identificador, correo, fecha, ruta,
paquetería y precio como snapshots independientes del catálogo. Se mantienen incluso si el
precio histórico no coincide con una tarifa maestra; intentar deducir o sustituir el precio
rompería el compromiso de respetar lo ya ofrecido. Al 20 de noviembre de 2026, 26 siguen
dentro de sus 30 días y 14 ya vencieron.

La comparación encontró 36 precios coincidentes y cuatro cotizaciones con importes que no
coinciden con el catálogo actual. Esos cuatro registros corresponden a tres valores que
antes aparecieron como tarifas dudosas: Estafeta zona 3 de 3–5 kg por $422.37 (dos casos),
Estafeta zona 3 de 5–10 kg por $703.95 y DHL zona 4 de 10–20 kg por $2,176.72. Se preservan
como evidencia histórica, pero no se promueven automáticamente al catálogo de tarifas.

## Reportes de Customer Care

El espacio final en `06600 ` era un problema de normalización: ahora frontend y API eliminan
espacios externos antes de validar. Escribir una ciudad no es un código postal válido; el
formulario acepta únicamente cinco dígitos y lo explica junto al campo, evitando una falla
silenciosa.

Dos personas con el mismo CP pueden ver paqueterías distintas si cambian peso, dimensiones,
destino, fecha de vigencia o estado de la paquetería. Con exactamente los mismos datos y el
mismo catálogo, el resultado es determinista; el CP por sí solo no define la opción.

## Métricas para Growth

La vista **Leads capturados** se divide en **Resumen** y **Directorio de leads**. El resumen
muestra las últimas 30 fechas con actividad, el total de cotizaciones de cada día, cuántas
terminaron sin opciones y la proporción entre cotizaciones públicas e históricas. El
directorio conserva una fila por correo y abre el historial detallado en un modal. Se
cuentan ambos orígenes, y una cotización sin filas en su snapshot de opciones se considera
sin resultado.

La tarjeta **Sin opciones** funciona también como acceso de seguimiento. **Ver casos** abre
el directorio filtrado a los leads que tienen al menos una cotización sin alternativas. El
historial del lead marca la cotización específica que requiere atención y permite volver al
directorio completo sin perder el contexto de la sección.
