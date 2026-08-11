"""Cliente HTTP para la API de Amagi.

Encapsula autenticacion por Bearer Token, timeouts, reintentos con backoff
exponencial y la traduccion de errores HTTP a excepciones del dominio.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from tracking_goals.domain.exceptions import (
    ErrorDeAutenticacion,
    ErrorDeConexion,
    ErrorDeConsulta,
    RespuestaInvalida,
)
from tracking_goals.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

CODIGOS_REINTENTABLES = {429, 500, 502, 503, 504}


class ClienteHttpAmagi:
    """Adaptador de bajo nivel sobre `requests`."""

    def __init__(self, settings: Settings, sesion: requests.Session | None = None) -> None:
        self._settings = settings
        self._sesion = sesion or requests.Session()
        self._sesion.headers.update(
            {
                "Authorization": f"Bearer {settings.api_token}",
                "Accept": "application/json",
                "User-Agent": "tracking-goals-invoker/1.0",
            }
        )

    def obtener_json(self, url: str, parametros: dict[str, str]) -> dict[str, Any]:
        """Ejecuta un GET y devuelve el cuerpo JSON como diccionario."""
        intentos = max(1, self._settings.api_max_reintentos)
        ultimo_error: Exception | None = None

        for intento in range(1, intentos + 1):
            try:
                logger.debug("GET %s params=%s (intento %s/%s)", url, parametros, intento, intentos)
                respuesta = self._sesion.get(
                    url,
                    params=parametros,
                    timeout=self._settings.api_timeout,
                    verify=self._settings.api_verificar_ssl,
                )
            except requests.exceptions.RequestException as error:
                ultimo_error = ErrorDeConexion(f"Fallo de comunicacion con el servicio: {error}")
                self._esperar_si_corresponde(intento, intentos, str(error))
                continue

            if respuesta.status_code in (401, 403):
                raise ErrorDeAutenticacion(
                    f"Autenticacion rechazada por el servicio (HTTP {respuesta.status_code}). "
                    "Verifique `AMAGI_API_TOKEN` en el archivo .env."
                )

            if respuesta.status_code in CODIGOS_REINTENTABLES:
                ultimo_error = ErrorDeConsulta(
                    f"El servicio respondio HTTP {respuesta.status_code}."
                )
                self._esperar_si_corresponde(
                    intento, intentos, f"HTTP {respuesta.status_code}"
                )
                continue

            if respuesta.status_code >= 400:
                raise ErrorDeConsulta(
                    f"El servicio respondio HTTP {respuesta.status_code}: "
                    f"{respuesta.text[:300]}"
                )

            return self._interpretar_json(respuesta)

        raise ultimo_error or ErrorDeConsulta("No fue posible consultar el servicio.")

    # -- Auxiliares ------------------------------------------------------------

    @staticmethod
    def _interpretar_json(respuesta: requests.Response) -> dict[str, Any]:
        try:
            cuerpo = respuesta.json()
        except ValueError as error:
            raise RespuestaInvalida(
                "La respuesta del servicio no es JSON valido."
            ) from error
        if not isinstance(cuerpo, dict):
            raise RespuestaInvalida(
                f"Se esperaba un objeto JSON en la raiz y se recibio {type(cuerpo).__name__}."
            )
        return cuerpo

    def _esperar_si_corresponde(self, intento: int, intentos: int, motivo: str) -> None:
        if intento >= intentos:
            logger.error("Consulta fallida tras %s intentos (%s).", intentos, motivo)
            return
        espera = self._settings.api_backoff ** intento
        logger.warning(
            "Intento %s/%s fallido (%s). Reintentando en %.1fs.", intento, intentos, motivo, espera
        )
        time.sleep(espera)

    def cerrar(self) -> None:
        self._sesion.close()
