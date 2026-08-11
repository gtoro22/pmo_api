"""Entidad de dominio: Usuario."""

from __future__ import annotations

from dataclasses import dataclass, field

from tracking_goals.domain.model.evaluacion import Evaluacion


@dataclass(frozen=True)
class Usuario:
    """Usuario incluido en una evaluacion.

    `identificacion` se conserva como texto para preservar ceros iniciales y
    formatos alfanumericos, segun las recomendaciones del contrato.
    """

    id: int
    identificacion: str | None
    nombres: str | None
    apellidos: str | None
    evaluaciones: tuple[Evaluacion, ...] = field(default=())

    @property
    def nombre_completo(self) -> str:
        partes = [p for p in (self.nombres, self.apellidos) if p]
        return " ".join(partes)
