"""Infraestructura de logging."""

from tracking_goals.infrastructure.logging.configurador import (
    NOMBRE_PROCESO,
    configurar_logging,
    registrar_fin_proceso,
    registrar_inicio_proceso,
)

__all__ = [
    "NOMBRE_PROCESO",
    "configurar_logging",
    "registrar_fin_proceso",
    "registrar_inicio_proceso",
]
