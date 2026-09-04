"""Selecciona el adaptador de entrega segun la configuracion del `.env`."""

from __future__ import annotations

import logging

from tracking_goals.application.ports.transportador_archivos import TransportadorArchivos
from tracking_goals.infrastructure.config.settings import ConfiguracionEnvio
from tracking_goals.infrastructure.transferencia.transportador_ftp import TransportadorFtp
from tracking_goals.infrastructure.transferencia.transportador_nulo import TransportadorNulo
from tracking_goals.infrastructure.transferencia.transportador_sftp import TransportadorSftp

logger = logging.getLogger(__name__)


def construir_transportador(config: ConfiguracionEnvio) -> TransportadorArchivos:
    """Devuelve el transportador correspondiente al protocolo configurado."""
    if not config.habilitado:
        return TransportadorNulo()
    if config.es_sftp:
        return TransportadorSftp(config)
    return TransportadorFtp(config)
