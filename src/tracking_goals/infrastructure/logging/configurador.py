"""Configuracion del logging del invocador.

Escribe simultaneamente en consola y en un archivo por ejecucion dentro de
`LOG_DIR`, y registra el evento de inicio del proceso.
"""

from __future__ import annotations

import logging
import platform
import sys
from datetime import datetime
from pathlib import Path

FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
NOMBRE_PROCESO = "tracking-goals-invoker"


def configurar_logging(nivel: str = "INFO", directorio: Path = Path("logs")) -> Path:
    """Inicializa los handlers de consola y archivo. Devuelve la ruta del log."""
    directorio.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = directorio / f"{NOMBRE_PROCESO}_{marca}.log"

    raiz = logging.getLogger()
    raiz.setLevel(getattr(logging, nivel.upper(), logging.INFO))
    for handler in list(raiz.handlers):
        raiz.removeHandler(handler)

    formateador = logging.Formatter(FORMATO, datefmt=FORMATO_FECHA)

    consola = logging.StreamHandler(stream=sys.stdout)
    consola.setFormatter(formateador)
    raiz.addHandler(consola)

    fichero = logging.FileHandler(archivo, encoding="utf-8")
    fichero.setFormatter(formateador)
    raiz.addHandler(fichero)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return archivo


def registrar_inicio_proceso(archivo_log: Path, argumentos: list[str] | None = None) -> None:
    """Deja constancia del arranque del proceso (requisito del invocador)."""
    logger = logging.getLogger(NOMBRE_PROCESO)
    logger.info("=" * 78)
    logger.info("INICIO DEL PROCESO | %s", NOMBRE_PROCESO)
    logger.info("Fecha de inicio    : %s", datetime.now().isoformat(timespec="seconds"))
    logger.info("Python             : %s", platform.python_version())
    logger.info("Plataforma         : %s", platform.platform())
    logger.info("Archivo de log     : %s", archivo_log)
    if argumentos is not None:
        logger.info("Argumentos         : %s", " ".join(argumentos) or "(sin argumentos)")
    logger.info("=" * 78)


def registrar_fin_proceso(exitoso: bool) -> None:
    logger = logging.getLogger(NOMBRE_PROCESO)
    estado = "FINALIZADO CORRECTAMENTE" if exitoso else "FINALIZADO CON ERRORES"
    logger.info("-" * 78)
    logger.info("%s | %s", estado, datetime.now().isoformat(timespec="seconds"))
    logger.info("-" * 78)
