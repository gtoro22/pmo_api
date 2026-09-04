"""Carga de configuracion desde el archivo `.env` / variables de entorno.

Aqui vive UNICAMENTE el endpoint base y los secretos. Las rutas concretas de la
API estan declaradas en `infrastructure/http/endpoints.py`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

from dotenv import load_dotenv

from tracking_goals.domain.exceptions import ErrorDeDominio

VALORES_VERDADEROS = {"1", "true", "yes", "y", "si", "on"}


class ConfiguracionInvalida(ErrorDeDominio):
    """Falta una variable obligatoria o su valor no es utilizable."""


PROTOCOLOS = ("sftp", "ftp", "ftps")
PUERTOS_POR_DEFECTO = {"sftp": 22, "ftp": 21, "ftps": 21}


@dataclass(frozen=True)
class ConfiguracionEnvio:
    """Parametros de entrega del reporte a un servidor remoto.

    Se habilita con `ENVIO_HABILITADO`. Cuando esta deshabilitada, el resto de
    los valores se ignora y el invocador solo deja el Excel en disco.
    """

    habilitado: bool = False
    protocolo: str = "sftp"
    host: str = ""
    puerto: int = 22
    usuario: str = ""
    password: str = ""
    llave_privada: Path | None = None
    llave_passphrase: str = ""
    directorio_remoto: str = "."
    nombre_remoto: str | None = None
    crear_directorio: bool = True
    timeout: int = 30
    verificar_host_key: bool = True
    known_hosts: Path | None = None
    ftp_pasivo: bool = True

    @property
    def es_sftp(self) -> bool:
        return self.protocolo == "sftp"

    @property
    def usa_tls(self) -> bool:
        return self.protocolo == "ftps"

    def describir(self) -> str:
        """Descripcion para los logs. Nunca incluye la contrasena."""
        if not self.habilitado:
            return "deshabilitado"
        auth = "llave" if self.llave_privada else "password"
        return (
            f"{self.protocolo}://{self.usuario}@{self.host}:{self.puerto}"
            f"{self.directorio_remoto} (auth={auth})"
        )


@dataclass(frozen=True)
class Settings:
    """Configuracion efectiva del invocador."""

    api_base_url: str
    api_token: str
    api_timeout: int = 30
    api_max_reintentos: int = 3
    api_backoff: float = 2.0
    api_verificar_ssl: bool = True
    proyecto_defecto: str | None = None
    per_page_defecto: int = 50
    log_level: str = "INFO"
    log_dir: Path = Path("logs")
    output_dir: Path = Path("output")
    envio: ConfiguracionEnvio = field(default_factory=ConfiguracionEnvio)

    @property
    def token_enmascarado(self) -> str:
        """Token apto para logs: solo los ultimos 4 caracteres."""
        if len(self.api_token) <= 4:
            return "****"
        return f"{'*' * 8}{self.api_token[-4:]}"


def cargar_settings(ruta_env: Path | None = None) -> Settings:
    """Lee el `.env` (si existe) y construye los `Settings`.

    Las variables ya presentes en el entorno tienen prioridad sobre el archivo,
    lo que permite sobreescribirlas con `docker run -e ...`.
    """
    if ruta_env is not None:
        load_dotenv(dotenv_path=ruta_env, override=False)
    else:
        load_dotenv(override=False)

    base_url = _texto("AMAGI_API_BASE_URL", obligatorio=True)
    token = _texto("AMAGI_API_TOKEN", obligatorio=True)

    return Settings(
        api_base_url=base_url.rstrip("/"),
        api_token=token,
        api_timeout=_entero("AMAGI_API_TIMEOUT", 30),
        api_max_reintentos=_entero("AMAGI_API_MAX_REINTENTOS", 3),
        api_backoff=_decimal("AMAGI_API_BACKOFF", 2.0),
        api_verificar_ssl=_booleano("AMAGI_API_VERIFICAR_SSL", True),
        proyecto_defecto=_texto("AMAGI_PROYECTO_DEFECTO") or None,
        per_page_defecto=_entero("AMAGI_PER_PAGE_DEFECTO", 50),
        log_level=(_texto("LOG_LEVEL") or "INFO").upper(),
        log_dir=Path(_texto("LOG_DIR") or "logs"),
        output_dir=Path(_texto("OUTPUT_DIR") or "output"),
        envio=_cargar_envio(),
    )


def _cargar_envio() -> ConfiguracionEnvio:
    """Lee la configuracion de entrega remota y la valida si esta habilitada."""
    habilitado = _booleano("ENVIO_HABILITADO", False)
    protocolo = (_texto("ENVIO_PROTOCOLO") or "sftp").lower()

    if habilitado and protocolo not in PROTOCOLOS:
        raise ConfiguracionInvalida(
            f"`ENVIO_PROTOCOLO` debe ser uno de {', '.join(PROTOCOLOS)} "
            f"(recibido: {protocolo!r})."
        )

    llave = _texto("ENVIO_LLAVE_PRIVADA")
    known_hosts = _texto("ENVIO_KNOWN_HOSTS")

    envio = ConfiguracionEnvio(
        habilitado=habilitado,
        protocolo=protocolo,
        host=_texto("ENVIO_HOST"),
        puerto=_entero("ENVIO_PUERTO", PUERTOS_POR_DEFECTO.get(protocolo, 22)),
        usuario=_texto("ENVIO_USUARIO"),
        password=_texto("ENVIO_PASSWORD"),
        llave_privada=Path(llave) if llave else None,
        llave_passphrase=_texto("ENVIO_LLAVE_PASSPHRASE"),
        directorio_remoto=_texto("ENVIO_DIRECTORIO_REMOTO") or ".",
        nombre_remoto=_texto("ENVIO_NOMBRE_REMOTO") or None,
        crear_directorio=_booleano("ENVIO_CREAR_DIRECTORIO", True),
        timeout=_entero("ENVIO_TIMEOUT", 30),
        verificar_host_key=_booleano("ENVIO_VERIFICAR_HOST_KEY", True),
        known_hosts=Path(known_hosts) if known_hosts else None,
        ftp_pasivo=_booleano("ENVIO_FTP_PASIVO", True),
    )

    if habilitado:
        _validar_envio(envio)
    return envio


def habilitar_envio(envio: ConfiguracionEnvio) -> ConfiguracionEnvio:
    """Activa la entrega remota (opcion `--enviar`) validando los parametros.

    Sirve para forzar el envio en una ejecucion puntual sin editar el `.env`,
    pero los datos de conexion deben estar igualmente definidos alli.
    """
    activada = replace(envio, habilitado=True)
    _validar_envio(activada)
    return activada


def _validar_envio(envio: ConfiguracionEnvio) -> None:
    """Falla al arrancar, antes de consultar la API, si falta algo esencial."""
    faltantes = [
        nombre
        for nombre, valor in (("ENVIO_HOST", envio.host), ("ENVIO_USUARIO", envio.usuario))
        if not valor
    ]
    if faltantes:
        raise ConfiguracionInvalida(
            "`ENVIO_HABILITADO` esta activo pero faltan variables obligatorias: "
            f"{', '.join(faltantes)}."
        )

    if not envio.password and not envio.llave_privada:
        raise ConfiguracionInvalida(
            "`ENVIO_HABILITADO` esta activo pero no hay credencial: defina "
            "`ENVIO_PASSWORD` o `ENVIO_LLAVE_PRIVADA`."
        )

    if envio.llave_privada is not None:
        if not envio.es_sftp:
            raise ConfiguracionInvalida(
                "`ENVIO_LLAVE_PRIVADA` solo aplica al protocolo sftp; "
                f"el protocolo configurado es {envio.protocolo}."
            )
        if not envio.llave_privada.is_file():
            raise ConfiguracionInvalida(
                f"No existe la llave privada indicada en `ENVIO_LLAVE_PRIVADA`: "
                f"{envio.llave_privada}."
            )

    if envio.known_hosts is not None and not envio.known_hosts.is_file():
        raise ConfiguracionInvalida(
            f"No existe el archivo indicado en `ENVIO_KNOWN_HOSTS`: {envio.known_hosts}."
        )


# -- Lectura tipada de variables ----------------------------------------------


def _texto(nombre: str, obligatorio: bool = False) -> str:
    valor = (os.getenv(nombre) or "").strip()
    if obligatorio and not valor:
        raise ConfiguracionInvalida(
            f"Falta la variable de entorno obligatoria `{nombre}`. "
            "Copie `.env.example` a `.env` y complete el valor."
        )
    return valor


def _entero(nombre: str, defecto: int) -> int:
    valor = (os.getenv(nombre) or "").strip()
    if not valor:
        return defecto
    try:
        return int(valor)
    except ValueError as error:
        raise ConfiguracionInvalida(f"`{nombre}` debe ser un entero (recibido: {valor!r}).") from error


def _decimal(nombre: str, defecto: float) -> float:
    valor = (os.getenv(nombre) or "").strip()
    if not valor:
        return defecto
    try:
        return float(valor)
    except ValueError as error:
        raise ConfiguracionInvalida(f"`{nombre}` debe ser numerico (recibido: {valor!r}).") from error


def _booleano(nombre: str, defecto: bool) -> bool:
    valor = (os.getenv(nombre) or "").strip().lower()
    if not valor:
        return defecto
    return valor in VALORES_VERDADEROS
