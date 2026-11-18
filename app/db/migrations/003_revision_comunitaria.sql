-- HU-03, P06/P09/P10: revisión académica y publicación de la versión aprobada.

CREATE TABLE aportes_nuevos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    autor_id INTEGER NOT NULL REFERENCES estudiantes(id),
    ramo_id INTEGER NOT NULL REFERENCES ramos(id),
    periodo_id INTEGER NOT NULL REFERENCES periodos_academicos(id),
    tema_id INTEGER NOT NULL REFERENCES temas_unidad(id),
    procedencia TEXT NOT NULL CHECK (length(trim(procedencia)) > 0),
    fecha_envio TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN (
        'PendienteAsignacion', 'RequiereCorreccion', 'Asignado',
        'Publicado', 'Rechazado', 'CorreccionSolicitada'
    ))
);

INSERT INTO aportes_nuevos
SELECT id, autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio, estado
FROM aportes;
DELETE FROM sqlite_sequence WHERE name = 'aportes_nuevos';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'aportes_nuevos', seq FROM sqlite_sequence WHERE name = 'aportes';
DROP TABLE aportes;
ALTER TABLE aportes_nuevos RENAME TO aportes;
CREATE INDEX idx_aportes_autor ON aportes (autor_id);

CREATE TABLE versiones_apunte_nuevas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aporte_id INTEGER NOT NULL REFERENCES aportes(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL CHECK (numero >= 1),
    nombre_archivo TEXT NOT NULL,
    referencia_archivo TEXT,
    hash_archivo TEXT,
    tamano_bytes INTEGER CHECK (tamano_bytes IS NULL OR tamano_bytes >= 0),
    tipo_mime TEXT,
    estado TEXT NOT NULL CHECK (estado IN (
        'Recibida', 'PendienteRevision', 'RequiereCorreccion', 'Final',
        'EnRevision', 'Aprobada', 'Publicada', 'Rechazada'
    )),
    fecha_creacion TEXT NOT NULL,
    UNIQUE (aporte_id, numero),
    CHECK (hash_archivo IS NULL OR referencia_archivo IS NOT NULL)
);

INSERT INTO versiones_apunte_nuevas
SELECT id, aporte_id, numero, nombre_archivo, referencia_archivo, hash_archivo,
       tamano_bytes, tipo_mime, estado, fecha_creacion
FROM versiones_apunte;
DELETE FROM sqlite_sequence WHERE name = 'versiones_apunte_nuevas';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'versiones_apunte_nuevas', seq FROM sqlite_sequence WHERE name = 'versiones_apunte';
DROP TABLE versiones_apunte;
ALTER TABLE versiones_apunte_nuevas RENAME TO versiones_apunte;
CREATE UNIQUE INDEX idx_versiones_hash_unico
    ON versiones_apunte (hash_archivo) WHERE hash_archivo IS NOT NULL;
CREATE INDEX idx_versiones_aporte ON versiones_apunte (aporte_id, numero);

CREATE TABLE revisiones_academicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL UNIQUE REFERENCES versiones_apunte(id) ON DELETE CASCADE,
    revisor_id INTEGER NOT NULL REFERENCES estudiantes(id),
    comunidad_id INTEGER NOT NULL REFERENCES comunidades_estudiantiles(id),
    fecha TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('Aprobacion', 'Rechazo', 'SolicitudCorreccion')),
    alcance TEXT NOT NULL CHECK (length(trim(alcance)) > 0),
    observaciones TEXT NOT NULL CHECK (length(trim(observaciones)) > 0)
);
