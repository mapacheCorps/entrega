ALTER TABLE versiones_apunte ADD COLUMN especialidad_requerida TEXT;
ALTER TABLE versiones_apunte ADD COLUMN comunidad_solicitante_id INTEGER REFERENCES comunidades_estudiantiles(id);
