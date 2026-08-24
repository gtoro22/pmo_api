"""Entidad de dominio: Objetivo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Objetivo:
    """Objetivo definido dentro de una perspectiva de una evaluacion.

    `resultado` y `cumplimiento` son `Number | null` segun el contrato del
    servicio: llegan en `None` cuando aun no existe un valor calculado. Lo mismo
    aplica a `minimo` y `sobresaliente`.

    `indicador` figura en el documento tecnico v1.0 pero el servicio ya no lo
    entrega; en su lugar llega `indicador_medicion`. Se conserva el campo para
    no perder el dato si el servicio vuelve a exponerlo.
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
    objetivo_estrategico: str | None = None
    indicador_medicion: str | None = None
    peso: float | None = None
    minimo: float | None = None
    sobresaliente: float | None = None
    periodo: str | None = None
    fecha_limite: str | None = None
    estado_seguimientos: str | None = None

    @property
    def tiene_resultado(self) -> bool:
        return self.resultado is not None

    @property
    def tiene_cumplimiento(self) -> bool:
        return self.cumplimiento is not None
