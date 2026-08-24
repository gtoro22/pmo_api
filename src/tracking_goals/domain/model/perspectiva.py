"""Entidad de dominio: Perspectiva."""

from __future__ import annotations

from dataclasses import dataclass, field

from tracking_goals.domain.model.objetivo import Objetivo


@dataclass(frozen=True)
class Perspectiva:
    """Perspectiva de una evaluacion (ej. "Procesos Internos").

    `objetivos` puede llegar vacio: el servicio lo representa como arreglo vacio.
    `peso` y `cumplimiento` no figuran en el documento tecnico v1.0.
    """

    id: int
    nombre: str
    peso: float | None = None
    cumplimiento: float | None = None
    objetivos: tuple[Objetivo, ...] = field(default=())

    @property
    def total_objetivos(self) -> int:
        return len(self.objetivos)
