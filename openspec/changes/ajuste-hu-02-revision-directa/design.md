# Diseño de la revisión directa

El estado vigente del aporte y su última versión validada determinan la cola. Una consulta GET no reserva ni cambia la versión. El POST de decisión usa una transacción de escritura SQLite, verifica versión y estado, y conserva la identidad del Moderador activo. EnRevision es una transición interna de esa misma transacción. La primera decisión válida es definitiva para la versión.

La migración 004 normaliza los estados anteriores y conserva las asignaciones históricas, versiones y decisiones. Los flujos de envío y reenvío usan PendienteRevision. HU-10 mide la demora desde el ingreso a la cola cuando se implemente.
