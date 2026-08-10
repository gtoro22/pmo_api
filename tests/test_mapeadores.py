"""Pruebas del mapeo JSON -> dominio."""

from __future__ import annotations

import pytest

from tracking_goals.domain.exceptions import RespuestaInvalida
from tracking_goals.infrastructure.http.mapeadores import MapeadorRespuesta


def test_mapea_el_ejemplo_de_la_documentacion(respuesta_documentacion):
    resultado = MapeadorRespuesta().a_resultado(respuesta_documentacion)

    assert resultado.es_exitoso
    assert resultado.total_usuarios_recibidos == 1

    usuario = resultado.usuarios[0]
    assert usuario.id == 13
    assert usuario.identificacion == "5555553333"
    assert usuario.nombre_completo == "Usuario Prueba"

    evaluacion = usuario.evaluaciones[0]
    assert evaluacion.proyecto == "2026"
    assert evaluacion.total_objetivos == 4

    objetivo = evaluacion.perspectivas[0].objetivos[0]
    assert objetivo.meta == 100.0
    assert objetivo.resultado is None
    assert objetivo.cumplimiento is None
    assert not objetivo.tiene_resultado

    assert resultado.metadatos.total_pages == 1
    assert resultado.metadatos.next_updated_since == "2026-07-29T10:38:00-05:00"
    assert not resultado.hay_pagina_siguiente


def test_identificacion_numerica_se_conserva_como_texto():
    cuerpo = {"results": [{"id": 1, "identificacion": 12345, "evaluaciones": []}], "status": "ok"}
    usuario = MapeadorRespuesta().a_resultado(cuerpo).usuarios[0]
    assert usuario.identificacion == "12345"


def test_arreglos_vacios_son_validos():
    cuerpo = {
        "results": [
            {
                "id": 1,
                "identificacion": "1",
                "nombres": "A",
                "apellidos": "B",
                "evaluaciones": [
                    {
                        "id": 2,
                        "proyecto": "2026",
                        "nombre": "Eval",
                        "total_perspectivas": 0,
                        "total_objetivos": 0,
                        "perspectivas": [],
                    }
                ],
            }
        ],
        "status": "ok",
    }
    resultado = MapeadorRespuesta().a_resultado(cuerpo)
    assert resultado.usuarios[0].evaluaciones[0].perspectivas == ()
    assert resultado.metadatos is None


def test_results_no_lista_lanza_respuesta_invalida():
    with pytest.raises(RespuestaInvalida):
        MapeadorRespuesta().a_resultado({"results": {"id": 1}})
