"""Entidad de dominio: Perspectiva."""

from __future__ import annotations

from dataclasses import dataclass, field

from tracking_goals.domain.model.objetivo import Objetivo


@dataclass(frozen=True)
class Perspectiva:
    """Perspectiva de una evaluacion (ej. "Procesos Internos").

    `objetivos` puede llegar vacio: el servicio lo representa como arreglo vacio.
    """

    id: int
    nombre: str
    objetivos: tuple[Objetivo, ...] = field(default=())

    @property
    def total_objetivos(self) -> int:
        return len(self.objetivos)
