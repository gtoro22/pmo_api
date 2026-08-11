"""Adaptadores HTTP hacia la API de Amagi."""

from tracking_goals.infrastructure.http.cliente_http import ClienteHttpAmagi
from tracking_goals.infrastructure.http.endpoints import Endpoints, RutasAmagi
from tracking_goals.infrastructure.http.mapeadores import MapeadorRespuesta
from tracking_goals.infrastructure.http.repositorio_objetivos_api import (
    RepositorioObjetivosApi,
)

__all__ = [
    "ClienteHttpAmagi",
    "Endpoints",
    "MapeadorRespuesta",
    "RepositorioObjetivosApi",
    "RutasAmagi",
]
