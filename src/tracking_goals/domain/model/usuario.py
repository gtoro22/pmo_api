"""Entidad de dominio: Usuario."""

from __future__ import annotations

from dataclasses import dataclass, field

from tracking_goals.domain.model.evaluacion import Evaluacion


@dataclass(frozen=True)
class Usuario:
    """Usuario evaluado.

    `identificacion` se conserva como texto para preservar ceros iniciales y
    formatos alfanumericos, segun las recomendaciones del contrato.

    Los campos organizacionales (`cargo`, `area`, `grupo`, ...) no figuran en el
    documento tecnico v1.0 pero si los entrega el servicio.
    """

    id: int
    identificacion: str | None
    nombres: str | None
    apellidos: str | None
    cargo: str | None = None
    nivel_cargo: str | None = None
    area: str | None = None
    grupo: str | None = None
    localizacion: str | None = None
    unidad_negocio: str | None = None
    evaluaciones: tuple[Evaluacion, ...] = field(default=())

    @property
    def nombre_completo(self) -> str:
        partes = [p for p in (self.nombres, self.apellidos) if p]
        return " ".join(partes)
