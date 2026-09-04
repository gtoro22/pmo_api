"""Caso de uso: exportar los objetivos consultados y entregar el archivo."""

from __future__ import annotations

import logging

from tracking_goals.application.dto.solicitud_exportacion import (
    ResumenEjecucion,
    SolicitudExportacion,
)
from tracking_goals.application.ports.exportador_registros import ExportadorRegistros
from tracking_goals.application.ports.transportador_archivos import (
    ResultadoEnvio,
    TransportadorArchivos,
)
from tracking_goals.application.use_cases.consultar_objetivos import ConsultarObjetivos
from tracking_goals.domain.exceptions import ErrorDeEnvio
from tracking_goals.domain.services.aplanador_objetivos import AplanadorObjetivos

logger = logging.getLogger(__name__)


class ExportarObjetivosExcel:
    """Consulta el servicio, aplana la jerarquia, escribe el Excel y lo entrega.

    La entrega remota se resuelve por el puerto `TransportadorArchivos`: cuando
    esta deshabilitada se inyecta un transportador nulo, asi que este caso de uso
    no necesita saber si hay SFTP, FTP o nada configurado.
    """

    def __init__(
        self,
        consultar_objetivos: ConsultarObjetivos,
        aplanador: AplanadorObjetivos,
        exportador: ExportadorRegistros,
        transportador: TransportadorArchivos,
    ) -> None:
        self._consultar_objetivos = consultar_objetivos
        self._aplanador = aplanador
        self._exportador = exportador
        self._transportador = transportador

    def ejecutar(self, solicitud: SolicitudExportacion) -> ResumenEjecucion:
        resultado, paginas = self._consultar_objetivos.ejecutar(
            solicitud.criterio, todas_las_paginas=solicitud.todas_las_paginas
        )

        registros = self._aplanador.aplanar(resultado)
        logger.info(
            "Aplanado completado: %s usuarios -> %s filas.",
            resultado.total_usuarios_recibidos,
            len(registros),
        )

        archivo = self._exportador.exportar(registros, solicitud.destino)
        logger.info("Archivo generado: %s", archivo)

        envio = self._entregar(archivo, solicitud)

        metadatos = resultado.metadatos
        return ResumenEjecucion(
            archivo=archivo,
            usuarios=resultado.total_usuarios_recibidos,
            filas=len(registros),
            paginas_consultadas=paginas,
            total_usuarios_servicio=metadatos.total_users if metadatos else None,
            total_paginas_servicio=metadatos.total_pages if metadatos else None,
            next_updated_since=metadatos.next_updated_since if metadatos else None,
            status=resultado.status,
            envio=envio,
        )

    def _entregar(self, archivo, solicitud: SolicitudExportacion) -> ResultadoEnvio:
        if solicitud.enviar is False:
            logger.info("Envio remoto omitido por la opcion --no-enviar.")
            return ResultadoEnvio.deshabilitado("Omitido con --no-enviar")
        try:
            return self._transportador.enviar(archivo)
        except ErrorDeEnvio:
            logger.error(
                "El Excel se genero correctamente en %s, pero no se pudo entregar "
                "en el destino remoto. El archivo sigue disponible en disco.",
                archivo,
            )
            raise
