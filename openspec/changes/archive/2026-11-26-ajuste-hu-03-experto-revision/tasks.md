# Cierre de tareas

- [x] 1. Crear la tabla `expertos`, distinguir el tipo de revisor y permitir `EnRevisionExperto` en la migración 005. Persistir especialidad solicitada y comunidad solicitante en la migración 006.
- [x] 2. Derivar y registrar una única decisión válida por versión. SQLite serializa la escritura con `BEGIN IMMEDIATE` y exige una decisión por versión.
- [x] 3. Incorporar rutas separadas para derivar, consultar el panel, descargar el apunte y evaluar con el perfil Experto de demostración.
- [x] 4. Mostrar la evaluación en el catálogo si se aprueba y el feedback al autor si se rechaza o pide corrección.
- [x] 5. Verificar aprobación, rechazo, corrección, autorización, especialidad solicitada y segunda decisión mediante HTTP y ejecutar la regresión.
- [x] 6. Sincronizar los artefactos afectados, regenerar las exportaciones UML y validar el cambio de OpenSpec.

El selector de rol y la identidad precargada pertenecen a la demo. El envío de correo de HU-05 y la autenticación institucional corresponden a entregas posteriores.
