"""DTOs de entrada y salida de los casos de uso."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tracking_goals.application.ports.transportador_archivos import ResultadoEnvio
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta


@dataclass(frozen=True)
class SolicitudExportacion:
    """Peticion de exportacion recibida desde la interfaz (CLI)."""

    criterio: CriterioConsulta
    destino: Path
    todas_las_paginas: bool = False
    # None = usar lo definido en el .env; True/False = forzar desde el CLI
    enviar: bool | None = None


@dataclass(frozen=True)
class ResumenEjecucion:
    """Resultado de la ejecucion, para reportarlo al usuario y a los logs."""

    archivo: Path
    usuarios: int
    filas: int
    paginas_consultadas: int
    total_usuarios_servicio: int | None
    total_paginas_servicio: int | None
    next_updated_since: str | None
    status: str
    envio: ResultadoEnvio
