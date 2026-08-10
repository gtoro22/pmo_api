"""Catalogo de endpoints de la API de Amagi.

Por decision de arquitectura, el `.env` solo contiene el ENDPOINT BASE
(`AMAGI_API_BASE_URL`). Las rutas concretas de cada llamado se declaran aqui,
dentro del bloque de infraestructura del DDD.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin


class RutasAmagi:
    """Rutas relativas expuestas por el servicio."""

    TRACKING_GOALS = "/api/v1/tracking_goals"


@dataclass(frozen=True)
class Endpoints:
    """Construye URLs absolutas a partir del endpoint base configurado."""

    base_url: str

    def _url(self, ruta: str) -> str:
        return urljoin(f"{self.base_url.rstrip('/')}/", ruta.lstrip("/"))

    @property
    def tracking_goals(self) -> str:
        """GET - consulta de evaluaciones, perspectivas y objetivos."""
        return self._url(RutasAmagi.TRACKING_GOALS)
