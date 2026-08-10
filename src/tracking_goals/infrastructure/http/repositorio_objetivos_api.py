"""Adaptador del puerto `RepositorioObjetivos` sobre la API REST de Amagi."""

from __future__ import annotations

import logging

from tracking_goals.domain.model.resultado_consulta import ResultadoConsulta
from tracking_goals.domain.repositories.repositorio_objetivos import RepositorioObjetivos
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta
from tracking_goals.infrastructure.http.cliente_http import ClienteHttpAmagi
from tracking_goals.infrastructure.http.endpoints import Endpoints
from tracking_goals.infrastructure.http.mapeadores import MapeadorRespuesta

logger = logging.getLogger(__name__)


class RepositorioObjetivosApi(RepositorioObjetivos):
    """Implementacion HTTP del repositorio de objetivos."""

    def __init__(
        self,
        cliente: ClienteHttpAmagi,
        endpoints: Endpoints,
        mapeador: MapeadorRespuesta | None = None,
    ) -> None:
        self._cliente = cliente
        self._endpoints = endpoints
        self._mapeador = mapeador or MapeadorRespuesta()

    def consultar(self, criterio: CriterioConsulta) -> ResultadoConsulta:
        url = self._endpoints.tracking_goals
        logger.debug("Endpoint resuelto: %s", url)
        cuerpo = self._cliente.obtener_json(url, criterio.como_parametros())
        return self._mapeador.a_resultado(cuerpo)
