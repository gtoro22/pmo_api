"""Adaptador de entrega por FTP y FTPS (FTP sobre TLS)."""

from __future__ import annotations

import ftplib
import logging
from pathlib import Path, PurePosixPath

from tracking_goals.application.ports.transportador_archivos import (
    ResultadoEnvio,
    TransportadorArchivos,
)
from tracking_goals.domain.exceptions import ErrorDeEnvio
from tracking_goals.infrastructure.config.settings import ConfiguracionEnvio

logger = logging.getLogger(__name__)


class TransportadorFtp(TransportadorArchivos):
    """Sube el reporte por FTP simple o por FTPS segun `ENVIO_PROTOCOLO`.

    FTP simple viaja sin cifrar, credenciales incluidas. Use `ftps` siempre que
    el servidor lo permita.
    """

    def __init__(self, config: ConfiguracionEnvio) -> None:
        self._config = config

    def enviar(self, archivo: Path) -> ResultadoEnvio:
        cfg = self._config
        nombre_remoto = cfg.nombre_remoto or archivo.name
        destino = PurePosixPath(cfg.directorio_remoto) / nombre_remoto

        if not cfg.usa_tls:
            logger.warning(
                "Protocolo ftp sin cifrado: las credenciales y el archivo viajan en claro. "
                "Use ENVIO_PROTOCOLO=ftps si el servidor lo soporta."
            )

        cliente = ftplib.FTP_TLS() if cfg.usa_tls else ftplib.FTP()
        try:
            logger.info(
                "Conectando por %s a %s:%s como %s.",
                cfg.protocolo, cfg.host, cfg.puerto, cfg.usuario,
            )
            cliente.connect(host=cfg.host, port=cfg.puerto, timeout=cfg.timeout)
            cliente.login(user=cfg.usuario, passwd=cfg.password)
            if cfg.usa_tls:
                cliente.prot_p()  # cifra tambien el canal de datos
            cliente.set_pasv(cfg.ftp_pasivo)

            self._ubicarse(cliente, PurePosixPath(cfg.directorio_remoto))

            logger.info("Subiendo %s -> %s", archivo.name, destino)
            with archivo.open("rb") as flujo:
                cliente.storbinary(f"STOR {nombre_remoto}", flujo)

            tam_remoto = self._tamano_remoto(cliente, nombre_remoto)

        except ftplib.error_perm as error:
            raise ErrorDeEnvio(
                f"El servidor {cfg.protocolo} rechazo la operacion: {error}. "
                "Verifique credenciales y permisos sobre `ENVIO_DIRECTORIO_REMOTO`."
            ) from error
        except ftplib.all_errors as error:
            raise ErrorDeEnvio(f"Fallo de {cfg.protocolo} con {cfg.host}: {error}") from error
        except OSError as error:
            raise ErrorDeEnvio(f"No fue posible leer el archivo {archivo}: {error}") from error
        finally:
            self._cerrar(cliente)

        tam_local = archivo.stat().st_size
        if tam_remoto is not None and tam_remoto != tam_local:
            raise ErrorDeEnvio(
                f"La transferencia quedo incompleta: {tam_remoto} de {tam_local} bytes en {destino}."
            )

        logger.info("Archivo entregado por %s en %s (%s bytes).", cfg.protocolo, destino, tam_local)
        return ResultadoEnvio(enviado=True, protocolo=cfg.protocolo, destino=str(destino))

    # -- Auxiliares ------------------------------------------------------------

    def _ubicarse(self, cliente: ftplib.FTP, directorio: PurePosixPath) -> None:
        """Entra al directorio remoto, creandolo si hace falta."""
        if str(directorio) in (".", ""):
            return
        try:
            cliente.cwd(str(directorio))
            return
        except ftplib.error_perm:
            if not self._config.crear_directorio:
                raise

        acumulado = PurePosixPath("/") if directorio.is_absolute() else PurePosixPath()
        partes = directorio.parts[1:] if directorio.is_absolute() else directorio.parts
        if directorio.is_absolute():
            cliente.cwd("/")
        for parte in partes:
            acumulado = acumulado / parte
            try:
                cliente.cwd(parte)
            except ftplib.error_perm:
                logger.info("Creando directorio remoto %s", acumulado)
                cliente.mkd(parte)
                cliente.cwd(parte)

    @staticmethod
    def _tamano_remoto(cliente: ftplib.FTP, nombre: str) -> int | None:
        """SIZE es opcional en el protocolo; si el servidor no lo soporta, se omite."""
        try:
            return cliente.size(nombre)
        except (ftplib.error_perm, ftplib.error_reply, OSError):
            logger.debug("El servidor no reporto el tamano remoto; se omite la verificacion.")
            return None

    @staticmethod
    def _cerrar(cliente: ftplib.FTP) -> None:
        try:
            cliente.quit()
        except Exception:  # el servidor pudo cerrar antes; no invalida la transferencia
            try:
                cliente.close()
            except Exception:
                pass
