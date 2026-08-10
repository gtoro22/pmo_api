"""Entidad de dominio: Objetivo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Objetivo:
    """Objetivo definido dentro de una perspectiva de una evaluacion.

    `resultado` y `cumplimiento` son `Number | null` segun el contrato del
    servicio: llegan en `None` cuando aun no existe un valor calculado.
    """

    id: int
    objetivo: str
    meta: float | None
    unidad_medida: str | None
    tipo_calculo: str | None
    tipo_indicador: str | None
    indicador: str | None
    resultado: float | None
    cumplimiento: float | None

    @property
    def tiene_resultado(self) -> bool:
        return self.resultado is not None

    @property
    def tiene_cumplimiento(self) -> bool:
        return self.cumplimiento is not None
