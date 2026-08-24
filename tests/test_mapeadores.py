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


def test_mapea_la_respuesta_real_del_servicio(respuesta_servicio):
    resultado = MapeadorRespuesta().a_resultado(respuesta_servicio)

    usuario = resultado.usuarios[0]
    assert usuario.cargo == "Especialista de Administracion de Contratos"
    assert usuario.area == "Gestion Corporativa y Control de Gestion"
    assert usuario.unidad_negocio == "Amagi Group"

    evaluacion = usuario.evaluaciones[0]
    assert evaluacion.inicio == "2026-04-01"
    assert evaluacion.fin == "2026-08-31"
    assert evaluacion.evaluador == "Apellido1 Apellido2 Nombre1 Nombre2"
    assert evaluacion.estado_evaluacion == "Evaluacion Finalizada"

    perspectiva = evaluacion.perspectivas[0]
    assert perspectiva.peso == 100.0
    assert perspectiva.cumplimiento == 78.38

    objetivo = perspectiva.objetivos[0]
    assert objetivo.objetivo_estrategico == "VENEZUELA"
    assert objetivo.indicador_medicion == "• Mantenimiento del Dashboard Comercial"
    assert objetivo.peso == 35.0
    assert objetivo.periodo == "Q4 2026"
    assert objetivo.fecha_limite == "2026-08-31"
    assert objetivo.estado_seguimientos == "Seguimiento Aprobado"
    assert objetivo.minimo is None
    assert objetivo.sobresaliente is None
    assert objetivo.indicador is None

    assert resultado.metadatos.total_users == 143
    assert resultado.metadatos.total_pages == 3
    assert resultado.hay_pagina_siguiente


def test_campos_nuevos_ausentes_no_rompen_el_mapeo(respuesta_documentacion):
    """La respuesta del documento tecnico v1.0 sigue siendo valida."""
    resultado = MapeadorRespuesta().a_resultado(respuesta_documentacion)

    usuario = resultado.usuarios[0]
    assert usuario.cargo is None
    assert usuario.area is None

    evaluacion = usuario.evaluaciones[0]
    assert evaluacion.evaluador is None
    assert evaluacion.estado_evaluacion is None

    objetivo = evaluacion.perspectivas[0].objetivos[0]
    assert objetivo.indicador == "VENEZUELA"
    assert objetivo.indicador_medicion is None
    assert objetivo.periodo is None


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
