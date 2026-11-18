-- HU-02, P05: comunidad, revisores y asignación de aportes.

CREATE TABLE comunidades_estudiantiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE estudiantes_nuevos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    rol TEXT UNIQUE CHECK (rol IN ('Estudiante', 'Moderador')),
    comunidad_id INTEGER REFERENCES comunidades_estudiantiles(id),
    disponible INTEGER NOT NULL DEFAULT 0 CHECK (disponible IN (0, 1))
);

INSERT INTO estudiantes_nuevos (id, nombre, correo, rol)
SELECT id, nombre, correo, rol FROM estudiantes;
DELETE FROM sqlite_sequence WHERE name = 'estudiantes_nuevos';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'estudiantes_nuevos', seq FROM sqlite_sequence WHERE name = 'estudiantes';
DROP TABLE estudiantes;
ALTER TABLE estudiantes_nuevos RENAME TO estudiantes;

CREATE TABLE aportes_nuevos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    autor_id INTEGER NOT NULL REFERENCES estudiantes(id),
    ramo_id INTEGER NOT NULL REFERENCES ramos(id),
    periodo_id INTEGER NOT NULL REFERENCES periodos_academicos(id),
    tema_id INTEGER NOT NULL REFERENCES temas_unidad(id),
    procedencia TEXT NOT NULL CHECK (length(trim(procedencia)) > 0),
    fecha_envio TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('PendienteAsignacion', 'RequiereCorreccion', 'Asignado'))
);

INSERT INTO aportes_nuevos (
    id, autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio, estado
)
SELECT id, autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio, estado
FROM aportes;
DELETE FROM sqlite_sequence WHERE name = 'aportes_nuevos';
INSERT INTO sqlite_sequence (name, seq)
SELECT 'aportes_nuevos', seq FROM sqlite_sequence WHERE name = 'aportes';
DROP TABLE aportes;
ALTER TABLE aportes_nuevos RENAME TO aportes;
CREATE INDEX idx_aportes_autor ON aportes (autor_id);

CREATE TABLE estudiantes_ramos_habilitados (
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id),
    ramo_id INTEGER NOT NULL REFERENCES ramos(id),
    PRIMARY KEY (estudiante_id, ramo_id)
);

CREATE TABLE asignaciones_revision (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aporte_id INTEGER NOT NULL REFERENCES aportes(id),
    revisor_id INTEGER NOT NULL REFERENCES estudiantes(id),
    comunidad_id INTEGER NOT NULL REFERENCES comunidades_estudiantiles(id),
    fecha_asignacion TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('Asignada', 'Finalizada'))
);

CREATE UNIQUE INDEX idx_asignacion_vigente_aporte
    ON asignaciones_revision (aporte_id) WHERE estado = 'Asignada';
CREATE INDEX idx_asignacion_vigente_revisor
    ON asignaciones_revision (revisor_id) WHERE estado = 'Asignada';
