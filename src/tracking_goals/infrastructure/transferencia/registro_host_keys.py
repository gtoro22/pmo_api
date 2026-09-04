"""Registro de llaves de servidores SSH en un archivo `known_hosts`.

Conocimiento de infraestructura, no de dominio: como se le pregunta la llave a un
servidor SSH, con que nombre se identifica cuando no usa el puerto 22 y en que
formato se persiste. Vive junto al adaptador SFTP porque resuelve el requisito
que este impone: con `ENVIO_VERIFICAR_HOST_KEY=true` solo se conecta a servidores
cuya llave ya este registrada.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from tracking_goals.domain.exceptions import ErrorDeEnvio
from tracking_goals.infrastructure.config.settings import ConfiguracionEnvio

logger = logging.getLogger(__name__)

PUERTO_SSH_ESTANDAR = 22
PERMISOS_KNOWN_HOSTS = 0o600


def nombre_en_known_hosts(host: str, puerto: int) -> str:
    """Identificador del servidor dentro de `known_hosts`.

    OpenSSH (y paramiko) escriben `[host]:puerto` cuando el puerto no es el 22,
    y una entrada registrada para un puerto no sirve para otro.
    """
    if puerto == PUERTO_SSH_ESTANDAR:
        return host
    return f"[{host}]:{puerto}"


def known_hosts_por_defecto(config: ConfiguracionEnvio) -> Path:
    """Archivo donde se registra la llave si el `.env` no indica uno."""
    if config.known_hosts is not None:
        return config.known_hosts
    return Path.home() / ".ssh" / "known_hosts"


@dataclass(frozen=True)
class LlaveRegistrada:
    """Resultado del registro, para reportarlo a quien lo solicito."""

    nombre: str
    tipo: str
    huella: str
    archivo: Path
    ya_estaba: bool

    def describir(self) -> str:
        estado = "ya estaba registrada" if self.ya_estaba else "registrada"
        return f"{self.nombre} ({self.tipo}) {estado} en {self.archivo}"


class RegistradorHostKeys:
    """Obtiene la llave publica de un servidor SSH y la guarda en `known_hosts`."""

    def __init__(self, config: ConfiguracionEnvio, timeout: int | None = None) -> None:
        self._config = config
        self._timeout = timeout if timeout is not None else config.timeout

    def registrar(self, destino: Path | None = None) -> LlaveRegistrada:
        """Consulta la llave del servidor configurado y la persiste.

        Raises:
            ErrorDeEnvio: si el servidor no responde o el archivo no se puede escribir.
        """
        from tracking_goals.infrastructure.transferencia.fabrica import (
            verificar_dependencias_sftp,
        )

        verificar_dependencias_sftp()
        import paramiko

        config = self._config
        if not config.host:
            raise ErrorDeEnvio(
                "No hay servidor al que consultarle la llave: defina `ENVIO_HOST` "
                "en el .env o use la opcion --host."
            )

        archivo = destino or known_hosts_por_defecto(config)
        nombre = nombre_en_known_hosts(config.host, config.puerto)

        llave = self._consultar_llave(paramiko)

        llaves = paramiko.HostKeys()
        if archivo.is_file():
            try:
                llaves.load(str(archivo))
            except OSError as error:
                raise ErrorDeEnvio(f"No fue posible leer {archivo}: {error}") from error

        ya_estaba = llaves.check(nombre, llave)
        llaves.add(nombre, llave.get_name(), llave)

        try:
            archivo.parent.mkdir(parents=True, exist_ok=True)
            llaves.save(str(archivo))
            archivo.chmod(PERMISOS_KNOWN_HOSTS)
        except OSError as error:
            raise ErrorDeEnvio(f"No fue posible escribir {archivo}: {error}") from error

        registro = LlaveRegistrada(
            nombre=nombre,
            tipo=llave.get_name(),
            huella=self._huella(llave),
            archivo=archivo,
            ya_estaba=ya_estaba,
        )
        logger.info("Llave %s", registro.describir())
        return registro

    # -- Auxiliares ------------------------------------------------------------

    def _consultar_llave(self, paramiko):
        config = self._config
        logger.info("Consultando la llave de %s:%s", config.host, config.puerto)
        transporte = paramiko.Transport((config.host, config.puerto))
        try:
            transporte.start_client(timeout=self._timeout)
            llave = transporte.get_remote_server_key()
        except paramiko.SSHException as error:
            raise ErrorDeEnvio(
                f"El servidor {config.host}:{config.puerto} no completo el saludo SSH: {error}"
            ) from error
        except OSError as error:
            raise ErrorDeEnvio(
                f"No fue posible conectar con {config.host}:{config.puerto}: {error}"
            ) from error
        finally:
            transporte.close()

        if llave is None:
            raise ErrorDeEnvio(
                f"El servidor {config.host}:{config.puerto} no entrego ninguna llave."
            )
        return llave

    @staticmethod
    def _huella(llave) -> str:
        """Huella en el mismo formato que muestra el cliente de OpenSSH."""
        digest = hashlib.sha256(llave.asbytes()).digest()
        return "SHA256:" + base64.b64encode(digest).decode().rstrip("=")
