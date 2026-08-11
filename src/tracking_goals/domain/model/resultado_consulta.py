"""Raiz de agregado: resultado de una consulta al servicio."""

from __future__ import annotations

from dataclasses import dataclass, field

from tracking_goals.domain.model.metadatos import Metadatos
from tracking_goals.domain.model.usuario import Usuario

ESTADO_OK = "ok"


@dataclass(frozen=True)
class ResultadoConsulta:
    """Respuesta completa del servicio: `results` + `meta` + `status`."""

    usuarios: tuple[Usuario, ...] = field(default=())
    metadatos: Metadatos | None = None
    status: str = ESTADO_OK

    @property
    def es_exitoso(self) -> bool:
        return self.status == ESTADO_OK

    @property
    def total_usuarios_recibidos(self) -> int:
        return len(self.usuarios)

    @property
    def hay_pagina_siguiente(self) -> bool:
        return self.metadatos is not None and self.metadatos.hay_pagina_siguiente

    def unir(self, otro: "ResultadoConsulta") -> "ResultadoConsulta":
        """Acumula los usuarios de otra pagina conservando su `meta` mas reciente."""
        return ResultadoConsulta(
            usuarios=self.usuarios + otro.usuarios,
            metadatos=otro.metadatos or self.metadatos,
            status=otro.status,
        )
