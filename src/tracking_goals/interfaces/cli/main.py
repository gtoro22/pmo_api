"""Punto de entrada del invocador desde linea de comandos."""

from __future__ import annotations

import logging
import sys

from tracking_goals.application.dto.solicitud_exportacion import ResumenEjecucion
from tracking_goals.domain.exceptions import ErrorDeDominio
from tracking_goals.infrastructure.config.settings import cargar_settings
from tracking_goals.infrastructure.logging.configurador import (
    NOMBRE_PROCESO,
    configurar_logging,
    registrar_fin_proceso,
    registrar_inicio_proceso,
)
from tracking_goals.interfaces.cli.argumentos import construir_parser, construir_solicitud
from tracking_goals.interfaces.cli.contenedor import Contenedor

CODIGO_OK = 0
CODIGO_ERROR = 1
CODIGO_INTERRUMPIDO = 130


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    argumentos = construir_parser().parse_args(argv)

    # 1) Configuracion (endpoint base y secretos provienen del .env).
    try:
        settings = cargar_settings(argumentos.env_file)
    except ErrorDeDominio as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return CODIGO_ERROR

    # 2) Log de inicio de proceso.
    nivel = argumentos.log_level or settings.log_level
    archivo_log = configurar_logging(nivel, settings.log_dir)
    registrar_inicio_proceso(archivo_log, argv)

    logger = logging.getLogger(NOMBRE_PROCESO)
    logger.info("Endpoint base      : %s", settings.api_base_url)
    logger.info("Token              : %s", settings.token_enmascarado)

    contenedor = None
    try:
        solicitud = construir_solicitud(argumentos, settings)
        logger.info("Criterio           : %s", solicitud.criterio.describir())
        logger.info("Archivo de salida  : %s", solicitud.destino)

        contenedor = Contenedor(settings)
        logger.info("Endpoint invocado  : %s", contenedor.endpoints.tracking_goals)

        resumen = contenedor.exportar_objetivos.ejecutar(solicitud)
        _reportar(logger, resumen)
        registrar_fin_proceso(exitoso=True)
        return CODIGO_OK
    except ErrorDeDominio as error:
        logger.error("%s: %s", type(error).__name__, error)
        registrar_fin_proceso(exitoso=False)
        return CODIGO_ERROR
    except KeyboardInterrupt:
        logger.warning("Proceso interrumpido por el usuario.")
        registrar_fin_proceso(exitoso=False)
        return CODIGO_INTERRUMPIDO
    except Exception:  # pragma: no cover - red de seguridad
        logger.exception("Error inesperado durante la ejecucion.")
        registrar_fin_proceso(exitoso=False)
        return CODIGO_ERROR
    finally:
        if contenedor is not None:
            contenedor.cerrar()


def _reportar(logger: logging.Logger, resumen: ResumenEjecucion) -> None:
    logger.info("Resumen de ejecucion:")
    logger.info("  Estado del servicio      : %s", resumen.status)
    logger.info("  Paginas consultadas      : %s", resumen.paginas_consultadas)
    logger.info("  Usuarios recibidos       : %s", resumen.usuarios)
    logger.info("  Total usuarios (servicio): %s", resumen.total_usuarios_servicio)
    logger.info("  Total paginas (servicio) : %s", resumen.total_paginas_servicio)
    logger.info("  Filas exportadas         : %s", resumen.filas)
    logger.info("  next_updated_since       : %s", resumen.next_updated_since)
    logger.info("  Archivo Excel            : %s", resumen.archivo.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
