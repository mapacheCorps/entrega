-- HU-03/CU-13: Experto para revisión de materias especializadas

CREATE TABLE IF NOT EXISTS expertos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    correo TEXT NOT NULL UNIQUE CHECK (length(trim(correo)) > 0),
    especialidad TEXT NOT NULL CHECK (length(trim(especialidad)) > 0),
    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_expertos_correo ON expertos (correo);

-- Recrear versiones_apunte con CHECK que incluya EnRevisionExperto
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
        'EnRevision', 'EnRevisionExperto', 'Aprobada', 'Publicada', 'Rechazada'
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_versiones_hash_unico
    ON versiones_apunte (hash_archivo) WHERE hash_archivo IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_versiones_aporte ON versiones_apunte (aporte_id, numero);

-- Extender revisiones_academicas con tipo_revisor y experto_id
CREATE TABLE revisiones_academicas_nuevas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL UNIQUE REFERENCES versiones_apunte(id) ON DELETE CASCADE,
    tipo_revisor TEXT NOT NULL DEFAULT 'comunidad' CHECK (tipo_revisor IN ('comunidad', 'experto')),
    revisor_id INTEGER REFERENCES estudiantes(id),          -- Moderador (cuando comunidad)
    experto_id INTEGER REFERENCES expertos(id),             -- Experto (cuando experto)
    comunidad_id INTEGER NOT NULL REFERENCES comunidades_estudiantiles(id),
    fecha TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('Aprobacion', 'Rechazo', 'SolicitudCorreccion')),
    alcance TEXT NOT NULL CHECK (length(trim(alcance)) > 0),
    observaciones TEXT NOT NULL CHECK (length(trim(observaciones)) > 0),
    especialidad_registrada TEXT,                           -- Denormalizada para ficha
    CHECK (
        (tipo_revisor = 'comunidad' AND revisor_id IS NOT NULL AND experto_id IS NULL)
        OR
        (tipo_revisor = 'experto' AND experto_id IS NOT NULL AND revisor_id IS NULL)
    )
);

INSERT INTO revisiones_academicas_nuevas (id, version_id, tipo_revisor, revisor_id, experto_id, comunidad_id, fecha, decision, alcance, observaciones, especialidad_registrada)
SELECT
    id,
    version_id,
    'comunidad' AS tipo_revisor,
    revisor_id,
    NULL AS experto_id,
    comunidad_id,
    fecha,
    decision,
    alcance,
    observaciones,
    NULL AS especialidad_registrada
FROM revisiones_academicas;

DROP TABLE revisiones_academicas;
ALTER TABLE revisiones_academicas_nuevas RENAME TO revisiones_academicas;

CREATE INDEX IF NOT EXISTS idx_revisiones_tipo_revisor ON revisiones_academicas (tipo_revisor);
CREATE INDEX IF NOT EXISTS idx_revisiones_experto ON revisiones_academicas (experto_id);
CREATE INDEX IF NOT EXISTS idx_revisiones_revisor ON revisiones_academicas (revisor_id);