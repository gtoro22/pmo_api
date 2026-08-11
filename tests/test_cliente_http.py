"""Pruebas del cliente HTTP y del repositorio API (con respuestas simuladas)."""

from __future__ import annotations

import pytest
import responses

from tracking_goals.domain.exceptions import (
    ErrorDeAutenticacion,
    ErrorDeConsulta,
    RespuestaInvalida,
)
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta
from tracking_goals.infrastructure.http.cliente_http import ClienteHttpAmagi
from tracking_goals.infrastructure.http.endpoints import Endpoints
from tracking_goals.infrastructure.http.repositorio_objetivos_api import (
    RepositorioObjetivosApi,
)

URL = "https://amagi.elearning.co/api/v1/tracking_goals"


def _repositorio(settings) -> RepositorioObjetivosApi:
    return RepositorioObjetivosApi(
        ClienteHttpAmagi(settings), Endpoints(settings.api_base_url)
    )


@responses.activate
def test_consulta_exitosa_envia_token_y_parametros(settings, respuesta_documentacion):
    responses.add(responses.GET, URL, json=respuesta_documentacion, status=200)

    resultado = _repositorio(settings).consultar(
        CriterioConsulta(project="2026", identity="5555553333", page=1, per_page=50)
    )

    assert resultado.total_usuarios_recibidos == 1
    peticion = responses.calls[0].request
    assert peticion.headers["Authorization"] == "Bearer token-de-pruebas"
    assert "project=2026" in peticion.url
    assert "identity=5555553333" in peticion.url
    assert "per_page=50" in peticion.url


@responses.activate
def test_401_lanza_error_de_autenticacion(settings):
    responses.add(responses.GET, URL, json={"error": "unauthorized"}, status=401)

    with pytest.raises(ErrorDeAutenticacion):
        _repositorio(settings).consultar(CriterioConsulta())


@responses.activate
def test_400_lanza_error_de_consulta(settings):
    responses.add(responses.GET, URL, json={"error": "bad request"}, status=400)

    with pytest.raises(ErrorDeConsulta):
        _repositorio(settings).consultar(CriterioConsulta())


@responses.activate
def test_json_invalido_lanza_respuesta_invalida(settings):
    responses.add(responses.GET, URL, body="<html>error</html>", status=200)

    with pytest.raises(RespuestaInvalida):
        _repositorio(settings).consultar(CriterioConsulta())


@responses.activate
def test_500_se_reintenta_y_luego_tiene_exito(settings, respuesta_documentacion):
    from dataclasses import replace

    settings = replace(settings, api_max_reintentos=2, api_backoff=0)
    responses.add(responses.GET, URL, json={"error": "boom"}, status=500)
    responses.add(responses.GET, URL, json=respuesta_documentacion, status=200)

    resultado = _repositorio(settings).consultar(CriterioConsulta())

    assert resultado.total_usuarios_recibidos == 1
    assert len(responses.calls) == 2
