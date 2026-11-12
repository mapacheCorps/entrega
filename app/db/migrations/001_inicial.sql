-- Migración inicial de Torpedos universitarios.
-- Cubre las entidades necesarias para HU-01.

CREATE TABLE estudiantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    rol TEXT NOT NULL UNIQUE CHECK (rol IN ('Estudiante', 'Moderador'))
);

CREATE TABLE carreras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL
);

CREATE TABLE ramos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    nombre TEXT NOT NULL,
    carrera_id INTEGER NOT NULL REFERENCES carreras(id),
    UNIQUE (carrera_id, codigo)
);

CREATE TABLE periodos_academicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anio INTEGER NOT NULL CHECK (anio BETWEEN 2000 AND 2100),
    semestre INTEGER NOT NULL CHECK (semestre IN (1, 2)),
    UNIQUE (anio, semestre)
);

CREATE TABLE temas_unidad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ramo_id INTEGER NOT NULL REFERENCES ramos(id),
    numero INTEGER NOT NULL CHECK (numero >= 1),
    nombre TEXT NOT NULL,
    UNIQUE (ramo_id, numero)
);

CREATE TABLE aportes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    autor_id INTEGER NOT NULL REFERENCES estudiantes(id),
    ramo_id INTEGER NOT NULL REFERENCES ramos(id),
    periodo_id INTEGER NOT NULL REFERENCES periodos_academicos(id),
    tema_id INTEGER NOT NULL REFERENCES temas_unidad(id),
    procedencia TEXT NOT NULL CHECK (length(trim(procedencia)) > 0),
    fecha_envio TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('PendienteAsignacion', 'RequiereCorreccion'))
);

CREATE TABLE versiones_apunte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aporte_id INTEGER NOT NULL REFERENCES aportes(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL CHECK (numero >= 1),
    nombre_archivo TEXT NOT NULL,
    referencia_archivo TEXT,
    hash_archivo TEXT,
    tamano_bytes INTEGER CHECK (tamano_bytes IS NULL OR tamano_bytes >= 0),
    tipo_mime TEXT,
    estado TEXT NOT NULL CHECK (estado IN ('Recibida', 'PendienteRevision', 'RequiereCorreccion', 'Final')),
    fecha_creacion TEXT NOT NULL,
    UNIQUE (aporte_id, numero),
    CHECK (hash_archivo IS NULL OR referencia_archivo IS NOT NULL)
);

CREATE UNIQUE INDEX idx_versiones_hash_unico
    ON versiones_apunte (hash_archivo)
    WHERE hash_archivo IS NOT NULL;

CREATE INDEX idx_versiones_aporte ON versiones_apunte (aporte_id, numero);
CREATE INDEX idx_aportes_autor ON aportes (autor_id);
CREATE INDEX idx_ramos_carrera ON ramos (carrera_id);
CREATE INDEX idx_temas_ramo ON temas_unidad (ramo_id);
