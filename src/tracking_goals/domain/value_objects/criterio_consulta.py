"""Objeto de valor: criterio de consulta al servicio."""

from __future__ import annotations

from dataclasses import dataclass, replace

from tracking_goals.domain.exceptions import CriterioInvalido

PER_PAGE_MAXIMO = 500


@dataclass(frozen=True)
class CriterioConsulta:
    """Parametros de filtrado y paginacion aceptados por el servicio.

    - `project`  filtra por codigo/nombre de proyecto (ej. "2026").
    - `identity` filtra por numero de identificacion del usuario.
    - `page` / `per_page` controlan la paginacion.
    - `updated_since` habilita la sincronizacion incremental.
    """

    project: str | None = None
    identity: str | None = None
    page: int = 1
    per_page: int = 50
    updated_since: str | None = None

    def __post_init__(self) -> None:
        if self.page < 1:
            raise CriterioInvalido(f"`page` debe ser mayor o igual a 1 (recibido: {self.page}).")
        if self.per_page < 1:
            raise CriterioInvalido(
                f"`per_page` debe ser mayor o igual a 1 (recibido: {self.per_page})."
            )
        if self.per_page > PER_PAGE_MAXIMO:
            raise CriterioInvalido(
                f"`per_page` no puede superar {PER_PAGE_MAXIMO} (recibido: {self.per_page})."
            )

    def siguiente_pagina(self) -> "CriterioConsulta":
        return replace(self, page=self.page + 1)

    def como_parametros(self) -> dict[str, str]:
        """Representacion como query params, omitiendo los filtros vacios."""
        parametros: dict[str, str] = {
            "page": str(self.page),
            "per_page": str(self.per_page),
        }
        if self.project:
            parametros["project"] = self.project
        if self.identity:
            parametros["identity"] = self.identity
        if self.updated_since:
            parametros["updated_since"] = self.updated_since
        return parametros

    def describir(self) -> str:
        """Descripcion legible para los logs (sin datos sensibles de auth)."""
        return ", ".join(f"{clave}={valor}" for clave, valor in sorted(self.como_parametros().items()))
