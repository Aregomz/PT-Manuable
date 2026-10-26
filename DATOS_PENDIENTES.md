# Datos pendientes de confirmación

Estas filas de `tarifas.csv` no se cargan porque corregirlas implicaría inventar información.
Los números corresponden a la fila del archivo original, incluida la cabecera.

| Fila | Paquetería | Zona | Peso | Precio | Motivo / confirmación requerida |
|---:|---|---|---|---:|---|
| 6 | Estafeta | 3 | 3–5 kg | $42,237.00 | Precio atípico; confirmar importe. |
| 16 | Estafeta | 3 | 5–10 kg | -$703.95 | Precio negativo; confirmar importe. |
| 18 | DHL | 3 | 1–3 kg | Vacío | Falta el precio. |
| 22 | FedEx | 7 | 0–1 kg | $240.00 | La zona 7 no existe en el modelo 1–4. |
| 24 | Redpack | 2 | 5–10 kg | Vacío | Falta el precio. |
| 31 | DHL | 4 | 1–3 kg | Vacío | Falta el precio. |
| 35 | Estafeta | 1 | 5–3 kg | $260.00 | Rango invertido; confirmar límites. |
| 44 | FedEx | 1 | 20–30 kg | Vacío | Falta el precio. |
| 53 | DHL | 4 | 10–20 kg | $217,672.00 | Precio atípico; confirmar importe. |
| 55 | FedEx | 3 | 3–5 kg | Vacío | Falta el precio. |
| 56 | DHL | 1 | 1–3 kg | $34,320.00 | Precio atípico; confirmar importe. |
| 57 | FedEx | 2 | 1–3 kg | Vacío | Falta el precio. |
| 63 | Estafeta | 2 | 10–20 kg | $10.40 | Precio atípico; confirmar importe. |
| 70 | Estafeta | 1 | 20–30 kg | $117,325.00 | Precio atípico; confirmar importe. |
| 83 | Redpack | 2 | 10–20 kg | $9.68 | Precio atípico; confirmar importe. |
| 87 | FedEx | 2 | 10–20 kg | Vacío | Falta el precio. |
| 90 | Paquetería Rayo | 1 | 0–1 kg | $99.00 | No existe en el catálogo de paqueterías. |
| 92 | DHL | 2 | 1000–3000 | $439.30 | Falta confirmar si la unidad es g o kg. |
| 99 | Estafeta | 4 | 10–20 kg | Vacío | Falta el precio. |
| 103 | Estafeta | 1 | 5000–10000 | $451.25 | Falta confirmar si la unidad es g o kg. |

## Rangos DHL traslapados

Las siguientes dos filas tienen la misma paquetería, zona y vigencia, pero se traslapan y
ofrecen precios distintos. Ambas se rechazan hasta recibir confirmación:

| Fila | Paquetería | Zona | Peso | Precio | Vigencia |
|---:|---|---:|---|---:|---|
| 40 | DHL | 2 | 3–6 kg | $470.00 | 2026-01-01 |
| 74 | DHL | 2 | 3–5 kg | $565.76 | 2026-01-01 |

Se necesita confirmar cuál rango e importe debe conservarse.
