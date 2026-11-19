# Diseño de la ficha y del archivo

La ficha, la vista previa y la descarga reciben el ID de versión y usan la misma consulta de versiones publicadas. Se reutiliza el almacenamiento existente. La vista previa comprueba el formato antes de servirlo en línea. La descarga usa una respuesta de adjunto y la ruta vuelve al catálogo si la versión o el archivo no están disponibles.

La implementación actual publica mediante aprobación comunitaria. Cuando se incorpore la publicación directa institucional, la ficha identificará ese origen sin inferir aprobación académica.
