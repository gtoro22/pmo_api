"""Entidad de dominio: Evaluacion."""

from __future__ import annotations

from dataclasses import dataclass, field

from tracking_goals.domain.model.perspectiva import Perspectiva


@dataclass(frozen=True)
class Evaluacion:
    """Evaluacion de desempeno asociada a un usuario.

    `total_perspectivas` y `total_objetivos` los entrega el servicio; el dominio
    los conserva tal cual y no los recalcula (ver recomendaciones del contrato).

    `evaluador` llega como nombre en texto libre: el servicio no expone
    identificacion, correo, area ni cargo del evaluador.
    """

    id: int
    proyecto: str | None
    nombre: str | None
    total_perspectivas: int | None
    total_objetivos: int | None
    inicio: str | None = None
    fin: str | None = None
    evaluador: str | None = None
    estado_evaluacion: str | None = None
    perspectivas: tuple[Perspectiva, ...] = field(default=())

    @property
    def perspectivas_recibidas(self) -> int:
        return len(self.perspectivas)

    @property
    def objetivos_recibidos(self) -> int:
        return sum(p.total_objetivos for p in self.perspectivas)

    @property
    def totales_consistentes(self) -> bool:
        """Compara los totales informados contra los elementos recibidos."""
        if self.total_perspectivas is None or self.total_objetivos is None:
            return True
        return (
            self.total_perspectivas == self.perspectivas_recibidas
            and self.total_objetivos == self.objetivos_recibidos
        )
