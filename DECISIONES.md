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
