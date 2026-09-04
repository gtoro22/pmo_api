"""Adaptador nulo: se usa cuando la entrega remota esta deshabilitada.

Aplica el patron Null Object para que el caso de uso no tenga que preguntar si
el envio esta activo: siempre llama al puerto y este decide.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tracking_goals.application.ports.transportador_archivos import (
    ResultadoEnvio,
    TransportadorArchivos,
)

logger = logging.getLogger(__name__)


class TransportadorNulo(TransportadorArchivos):
    """No transfiere nada. El archivo queda unicamente en disco local."""

    def enviar(self, archivo: Path) -> ResultadoEnvio:
        logger.info("Envio remoto deshabilitado (ENVIO_HABILITADO=false).")
        return ResultadoEnvio.deshabilitado()
