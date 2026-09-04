"""Adaptadores de entrega del reporte a destinos remotos."""

from tracking_goals.infrastructure.transferencia.fabrica import (
    construir_transportador,
    verificar_dependencias_sftp,
)
from tracking_goals.infrastructure.transferencia.registro_host_keys import (
    LlaveRegistrada,
    RegistradorHostKeys,
    known_hosts_por_defecto,
    nombre_en_known_hosts,
)
from tracking_goals.infrastructure.transferencia.transportador_ftp import TransportadorFtp
from tracking_goals.infrastructure.transferencia.transportador_nulo import TransportadorNulo
from tracking_goals.infrastructure.transferencia.transportador_sftp import TransportadorSftp

__all__ = [
    "LlaveRegistrada",
    "RegistradorHostKeys",
    "TransportadorFtp",
    "TransportadorNulo",
    "TransportadorSftp",
    "construir_transportador",
    "known_hosts_por_defecto",
    "nombre_en_known_hosts",
    "verificar_dependencias_sftp",
]
