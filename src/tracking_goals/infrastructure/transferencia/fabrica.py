"""Selecciona el adaptador de entrega segun la configuracion del `.env`."""

from __future__ import annotations

import logging

from tracking_goals.application.ports.transportador_archivos import TransportadorArchivos
from tracking_goals.domain.exceptions import ErrorDeEnvio
from tracking_goals.infrastructure.config.settings import ConfiguracionEnvio
from tracking_goals.infrastructure.transferencia.transportador_ftp import TransportadorFtp
from tracking_goals.infrastructure.transferencia.transportador_nulo import TransportadorNulo
from tracking_goals.infrastructure.transferencia.transportador_sftp import TransportadorSftp

logger = logging.getLogger(__name__)

MENSAJE_SIN_PARAMIKO = (
    "El envio por SFTP necesita la libreria `paramiko`, que no esta instalada. "
    "Ejecute `pip install -r requirements.txt` (o use ENVIO_PROTOCOLO=ftps, que "
    "no la requiere)."
)


def construir_transportador(config: ConfiguracionEnvio) -> TransportadorArchivos:
    """Devuelve el transportador correspondiente al protocolo configurado.

    Comprueba aqui que las dependencias del protocolo esten disponibles: el
    contenedor se arma antes de consultar la API, asi que un requisito faltante
    se reporta de inmediato y no despues de haber generado el Excel.
    """
    if not config.habilitado:
        return TransportadorNulo()
    if config.es_sftp:
        verificar_dependencias_sftp()
        return TransportadorSftp(config)
    return TransportadorFtp(config)


def verificar_dependencias_sftp() -> None:
    """Falla con un mensaje accionable si `paramiko` no esta instalado."""
    try:
        import paramiko  # noqa: F401
    except ImportError as error:
        raise ErrorDeEnvio(MENSAJE_SIN_PARAMIKO) from error
