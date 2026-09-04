"""Punto de entrada para registrar la llave de un servidor SFTP.

Con `ENVIO_VERIFICAR_HOST_KEY=true` (el valor por defecto), el invocador solo
conecta a servidores cuya llave ya este en `known_hosts`. Este comando la
consulta y la registra, tomando el servidor y el puerto del `.env`.

Equivale a `ssh-keyscan -p <puerto> <host>`, pero usa paramiko, asi que funciona
en servidores sin el cliente de OpenSSH instalado.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path

from tracking_goals.domain.exceptions import ErrorDeDominio
from tracking_goals.infrastructure.config.settings import cargar_settings
from tracking_goals.infrastructure.logging.configurador import configurar_logging
from tracking_goals.infrastructure.transferencia.registro_host_keys import (
    RegistradorHostKeys,
    known_hosts_por_defecto,
)

NOMBRE_PROCESO = "registrar-host-key"
CODIGO_OK = 0
CODIGO_ERROR = 1
CODIGO_INTERRUMPIDO = 130

DESCRIPCION = (
    "Registra la llave publica de un servidor SFTP en un archivo known_hosts, "
    "requisito para conectarse con la verificacion de host key activada."
)

EPILOGO = """Ejemplos:
  registrar_host_key.py
  registrar_host_key.py --salida .ssh/known_hosts
  registrar_host_key.py --host 172.20.1.65 --puerto 4422

Sin argumentos toma ENVIO_HOST, ENVIO_PUERTO y ENVIO_KNOWN_HOSTS del .env.
"""


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="registrar_host_key.py",
        description=DESCRIPCION,
        epilog=EPILOGO,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", help="Servidor. Por defecto ENVIO_HOST del .env.")
    parser.add_argument(
        "--puerto", type=int, help="Puerto. Por defecto ENVIO_PUERTO del .env."
    )
    parser.add_argument(
        "--salida",
        type=Path,
        help="Archivo known_hosts a escribir. Por defecto ENVIO_KNOWN_HOSTS del "
        ".env, o ~/.ssh/known_hosts.",
    )
    parser.add_argument("--timeout", type=int, help="Segundos de espera.")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nivel de detalle del log.",
    )
    parser.add_argument("--env-file", type=Path, help="Ruta alternativa del .env.")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    argumentos = construir_parser().parse_args(argv)

    try:
        settings = cargar_settings(argumentos.env_file)
    except ErrorDeDominio as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return CODIGO_ERROR

    nivel = argumentos.log_level or settings.log_level
    configurar_logging(nivel, settings.log_dir, nombre=NOMBRE_PROCESO)
    logger = logging.getLogger(NOMBRE_PROCESO)

    # Los argumentos del CLI anulan lo definido en el .env para esta ejecucion
    config = settings.envio
    if argumentos.host:
        config = replace(config, host=argumentos.host)
    if argumentos.puerto:
        config = replace(config, puerto=argumentos.puerto)

    destino = argumentos.salida or known_hosts_por_defecto(config)

    try:
        registro = RegistradorHostKeys(config, timeout=argumentos.timeout).registrar(destino)
    except ErrorDeDominio as error:
        logger.error("%s: %s", type(error).__name__, error)
        return CODIGO_ERROR
    except KeyboardInterrupt:
        logger.warning("Registro interrumpido por el usuario.")
        return CODIGO_INTERRUMPIDO

    logger.info("Servidor            : %s", registro.nombre)
    logger.info("Tipo de llave       : %s", registro.tipo)
    logger.info("Huella              : %s", registro.huella)
    logger.info("Archivo known_hosts : %s", registro.archivo.resolve())
    logger.warning(
        "Contraste la huella con el administrador del servidor antes de confiar en ella."
    )
    if settings.envio.known_hosts is None:
        logger.info("Para fijarlo, agregue al .env: ENVIO_KNOWN_HOSTS=%s", registro.archivo.resolve())
    return CODIGO_OK


if __name__ == "__main__":
    raise SystemExit(main())
