"""Raiz de composicion: ensambla los adaptadores con los casos de uso."""

from __future__ import annotations

from dataclasses import dataclass

from tracking_goals.application.use_cases.consultar_objetivos import ConsultarObjetivos
from tracking_goals.application.use_cases.exportar_objetivos_excel import (
    ExportarObjetivosExcel,
)
from tracking_goals.domain.services.aplanador_objetivos import AplanadorObjetivos
from tracking_goals.infrastructure.config.settings import Settings
from tracking_goals.infrastructure.exportacion.exportador_excel import ExportadorExcel
from tracking_goals.infrastructure.http.cliente_http import ClienteHttpAmagi
from tracking_goals.infrastructure.http.endpoints import Endpoints
from tracking_goals.infrastructure.http.repositorio_objetivos_api import (
    RepositorioObjetivosApi,
)
from tracking_goals.infrastructure.transferencia.fabrica import construir_transportador


@dataclass
class Contenedor:
    """Contenedor minimo de dependencias del invocador."""

    settings: Settings

    def __post_init__(self) -> None:
        self.endpoints = Endpoints(base_url=self.settings.api_base_url)
        self.cliente = ClienteHttpAmagi(self.settings)
        self.repositorio = RepositorioObjetivosApi(self.cliente, self.endpoints)
        self.consultar_objetivos = ConsultarObjetivos(self.repositorio)
        self.transportador = construir_transportador(self.settings.envio)
        self.exportar_objetivos = ExportarObjetivosExcel(
            consultar_objetivos=self.consultar_objetivos,
            aplanador=AplanadorObjetivos(),
            exportador=ExportadorExcel(),
            transportador=self.transportador,
        )

    def cerrar(self) -> None:
        self.cliente.cerrar()
