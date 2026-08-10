"""Objeto de valor: metadatos de paginacion y sincronizacion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Metadatos:
    """Seccion `meta` de la respuesta del servicio."""

    page: int
    per_page: int
    total_users: int
    total_pages: int
    updated_since: str | None
    server_time: str | None
    next_updated_since: str | None

    @property
    def hay_pagina_siguiente(self) -> bool:
        return self.page < self.total_pages
