"""Invocador del servicio web de evaluaciones y objetivos de Amagi.

Arquitectura DDD por capas:
    domain/         modelo, reglas de negocio y puertos (sin dependencias externas)
    application/    casos de uso y DTOs
    infrastructure/ adaptadores: HTTP, Excel, configuracion y logging
    interfaces/     entrada del sistema (CLI)
"""

__version__ = "1.0.0"
