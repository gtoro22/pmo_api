"""Adaptador de entrega por SFTP (SSH File Transfer Protocol)."""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath

from tracking_goals.application.ports.transportador_archivos import (
    ResultadoEnvio,
    TransportadorArchivos,
)
from tracking_goals.domain.exceptions import ErrorDeEnvio
from tracking_goals.infrastructure.config.settings import ConfiguracionEnvio

logger = logging.getLogger(__name__)


class TransportadorSftp(TransportadorArchivos):
    """Sube el reporte por SFTP autenticando con contrasena o con llave privada."""

    def __init__(self, config: ConfiguracionEnvio) -> None:
        self._config = config

    def enviar(self, archivo: Path) -> ResultadoEnvio:
        import paramiko  # se importa aqui para no exigir la libreria si no se usa

        cfg = self._config
        destino = PurePosixPath(cfg.directorio_remoto) / (cfg.nombre_remoto or archivo.name)

        logger.info("Conectando por SFTP a %s:%s como %s.", cfg.host, cfg.puerto, cfg.usuario)
        cliente = paramiko.SSHClient()
        try:
            self._configurar_host_keys(cliente, paramiko)
            cliente.connect(
                hostname=cfg.host,
                port=cfg.puerto,
                username=cfg.usuario,
                password=cfg.password or None,
                key_filename=str(cfg.llave_privada) if cfg.llave_privada else None,
                passphrase=cfg.llave_passphrase or None,
                timeout=cfg.timeout,
                allow_agent=False,
                look_for_keys=False,
            )

            with cliente.open_sftp() as sftp:
                sftp.get_channel().settimeout(cfg.timeout)
                if cfg.crear_directorio:
                    self._asegurar_directorio(sftp, PurePosixPath(cfg.directorio_remoto))
                logger.info("Subiendo %s -> %s", archivo.name, destino)
                sftp.put(str(archivo), str(destino))
                tam_remoto = sftp.stat(str(destino)).st_size

        except paramiko.AuthenticationException as error:
            raise ErrorDeEnvio(
                f"Autenticacion SFTP rechazada para {cfg.usuario}@{cfg.host}. "
                "Verifique `ENVIO_USUARIO` y `ENVIO_PASSWORD` o `ENVIO_LLAVE_PRIVADA`."
            ) from error
        except paramiko.SSHException as error:
            raise ErrorDeEnvio(f"Fallo de SSH/SFTP con {cfg.host}: {error}") from error
        except OSError as error:
            raise ErrorDeEnvio(f"No fue posible transferir el archivo a {cfg.host}: {error}") from error
        finally:
            cliente.close()

        tam_local = archivo.stat().st_size
        if tam_remoto != tam_local:
            raise ErrorDeEnvio(
                f"La transferencia quedo incompleta: {tam_remoto} de {tam_local} bytes en {destino}."
            )

        logger.info("Archivo entregado por SFTP en %s (%s bytes).", destino, tam_remoto)
        return ResultadoEnvio(enviado=True, protocolo="sftp", destino=str(destino))

    # -- Auxiliares ------------------------------------------------------------

    def _configurar_host_keys(self, cliente, paramiko) -> None:
        """Verifica la identidad del servidor salvo que se desactive explicitamente."""
        cfg = self._config
        if not cfg.verificar_host_key:
            logger.warning(
                "Verificacion de host key desactivada (ENVIO_VERIFICAR_HOST_KEY=false). "
                "La conexion queda expuesta a suplantacion del servidor."
            )
            cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            return

        if cfg.known_hosts is not None:
            cliente.load_host_keys(str(cfg.known_hosts))
        else:
            cliente.load_system_host_keys()
        cliente.set_missing_host_key_policy(paramiko.RejectPolicy())

    @staticmethod
    def _asegurar_directorio(sftp, directorio: PurePosixPath) -> None:
        """Crea el directorio remoto y sus padres si no existen."""
        if str(directorio) in (".", "", "/"):
            return
        try:
            sftp.stat(str(directorio))
            return
        except OSError:
            pass

        partes = directorio.parts
        acumulado = PurePosixPath(partes[0]) if directorio.is_absolute() else PurePosixPath()
        for parte in partes[1:] if directorio.is_absolute() else partes:
            acumulado = acumulado / parte
            try:
                sftp.stat(str(acumulado))
            except OSError:
                logger.info("Creando directorio remoto %s", acumulado)
                sftp.mkdir(str(acumulado))
