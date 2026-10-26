# Entrega — Fase 1

Hola, Comercial:

Quedó listo el cotizador público: captura el correo, muestra opciones y guarda cada
cotización. Pueden consultar leads, tarifas e importaciones en
`http://localhost:8080/admin/login` con usuario `comercial` y contraseña `comercial123`.

Los datos confiables se cargan al iniciar. En **Cargar datos** pueden importar CSV y auditar
resultados; en **Datos cargados** pueden editar tarifas y activar o inactivar paqueterías.

Excluimos 20 filas inválidas y dos tarifas DHL traslapadas; el detalle está en
[`DATOS_PENDIENTES.md`](./DATOS_PENDIENTES.md). Confirmen cuál tarifa DHL de zona 2 y
vigencia `2026-01-01` es correcta: `3–6 kg por $470.00` o `3–5 kg por $565.76`.

La cotización muestra la entrega estimada cuando existe. Para mostrarla siempre, deben
completar los días faltantes en 19 tarifas.
