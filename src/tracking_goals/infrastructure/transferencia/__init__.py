"""Adaptadores de entrega del reporte a destinos remotos."""

from tracking_goals.infrastructure.transferencia.fabrica import construir_transportador
from tracking_goals.infrastructure.transferencia.transportador_ftp import TransportadorFtp
from tracking_goals.infrastructure.transferencia.transportador_nulo import TransportadorNulo
from tracking_goals.infrastructure.transferencia.transportador_sftp import TransportadorSftp

__all__ = [
    "TransportadorFtp",
    "TransportadorNulo",
    "TransportadorSftp",
    "construir_transportador",
]
