"""Carga de configuracion desde el archivo `.env` / variables de entorno.

Aqui vive UNICAMENTE el endpoint base y los secretos. Las rutas concretas de la
API estan declaradas en `infrastructure/http/endpoints.py`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from tracking_goals.domain.exceptions import ErrorDeDominio

VALORES_VERDADEROS = {"1", "true", "yes", "y", "si", "on"}


class ConfiguracionInvalida(ErrorDeDominio):
    """Falta una variable obligatoria o su valor no es utilizable."""


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
