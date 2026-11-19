-- Sustituye los estados de asignacion por una cola compartida de revision.

CREATE TABLE aportes_nuevos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    autor_id INTEGER NOT NULL REFERENCES estudiantes(id),
    ramo_id INTEGER NOT NULL REFERENCES ramos(id),
    periodo_id INTEGER NOT NULL REFERENCES periodos_academicos(id),
    tema_id INTEGER NOT NULL REFERENCES temas_unidad(id),
    procedencia TEXT NOT NULL CHECK (length(trim(procedencia)) > 0),
    fecha_envio TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN (
        'PendienteRevision', 'RequiereCorreccion',
        'Publicado', 'Rechazado', 'CorreccionSolicitada'
    ))
);

INSERT INTO aportes_nuevos
SELECT id, autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio,
       CASE WHEN estado IN ('PendienteAsignacion', 'Asignado') THEN 'PendienteRevision' ELSE estado END
FROM aportes;
DELETE FROM sqlite_sequence WHERE name = 'aportes_nuevos';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'aportes_nuevos', seq FROM sqlite_sequence WHERE name = 'aportes';
DROP TABLE aportes;
ALTER TABLE aportes_nuevos RENAME TO aportes;
CREATE INDEX idx_aportes_autor ON aportes (autor_id);

UPDATE versiones_apunte SET estado = 'PendienteRevision'
WHERE estado = 'EnRevision'
  AND aporte_id IN (SELECT id FROM aportes WHERE estado = 'PendienteRevision');
