"""Garantiza que todo campo del JSON del servicio tenga columna en el Excel.

Es la prueba que evita la regresion de fondo: que el servicio agregue campos y
estos se pierdan silenciosamente en la exportacion.
"""

from __future__ import annotations

import logging

import pytest

from tracking_goals.domain.model.registro_plano import RegistroPlano
from tracking_goals.domain.services.aplanador_objetivos import AplanadorObjetivos
from tracking_goals.infrastructure.http.mapeadores import (
    CLAVES_CONOCIDAS,
    MapeadorRespuesta,
)

CONTENEDORES = {"evaluaciones", "perspectivas", "objetivos"}

# Campos del JSON que en el Excel llevan otro nombre, para que no colisionen
# entre niveles (`id`, `nombre`, `peso` y `cumplimiento` existen en varios).
RENOMBRES = {
    ("usuario", "id"): "usuario_id",
    ("evaluacion", "id"): "evaluacion_id",
    ("evaluacion", "nombre"): "evaluacion_nombre",
    ("evaluacion", "inicio"): "evaluacion_inicio",
    ("evaluacion", "fin"): "evaluacion_fin",
    ("perspectiva", "id"): "perspectiva_id",
    ("perspectiva", "nombre"): "perspectiva_nombre",
    ("perspectiva", "peso"): "perspectiva_peso",
    ("perspectiva", "cumplimiento"): "perspectiva_cumplimiento",
    ("objetivo", "id"): "objetivo_id",
    ("objetivo", "peso"): "objetivo_peso",
    ("meta", "page"): "meta_page",
    ("meta", "per_page"): "meta_per_page",
    ("meta", "total_users"): "meta_total_users",
    ("meta", "total_pages"): "meta_total_pages",
    ("meta", "updated_since"): "meta_updated_since",
    ("meta", "server_time"): "meta_server_time",
    ("meta", "next_updated_since"): "meta_next_updated_since",
}


def _columna(nivel: str, clave: str) -> str:
    return RENOMBRES.get((nivel, clave), clave)


def _claves_escalares(cuerpo: dict) -> dict[str, set[str]]:
    """Claves de dato (no contenedores) presentes en cada nivel del JSON."""
    niveles: dict[str, set[str]] = {}

    def registrar(nodo: dict, nivel: str) -> None:
        niveles.setdefault(nivel, set()).update(
            k for k in nodo if k not in CONTENEDORES
        )

    for usuario in cuerpo["results"]:
        registrar(usuario, "usuario")
        for evaluacion in usuario.get("evaluaciones") or []:
            registrar(evaluacion, "evaluacion")
            for perspectiva in evaluacion.get("perspectivas") or []:
                registrar(perspectiva, "perspectiva")
                for objetivo in perspectiva.get("objetivos") or []:
                    registrar(objetivo, "objetivo")
    if cuerpo.get("meta"):
        registrar(cuerpo["meta"], "meta")
    return niveles


def test_todo_campo_del_json_tiene_columna(respuesta_servicio):
    """Ningun dato del servicio puede quedar fuera del archivo de salida."""
    columnas = set(RegistroPlano.columnas())
    sin_columna = [
        f"{nivel}.{clave}"
        for nivel, claves in _claves_escalares(respuesta_servicio).items()
        for clave in sorted(claves)
        if _columna(nivel, clave) not in columnas
    ]
    assert not sin_columna, f"Campos del JSON sin columna en el Excel: {sin_columna}"
    assert "status" in columnas


def test_todo_campo_del_json_llega_a_la_fila(respuesta_servicio):
    """Tener la columna no basta: el valor del JSON debe llegar intacto a la fila."""
    resultado = MapeadorRespuesta().a_resultado(respuesta_servicio)
    fila = AplanadorObjetivos().aplanar(resultado)[0]
    datos = fila.como_diccionario()

    usuario = respuesta_servicio["results"][0]
    evaluacion = usuario["evaluaciones"][0]
    perspectiva = evaluacion["perspectivas"][0]
    objetivo = perspectiva["objetivos"][0]
    fuentes = {
        "usuario": usuario,
        "evaluacion": evaluacion,
        "perspectiva": perspectiva,
        "objetivo": objetivo,
        "meta": respuesta_servicio["meta"],
    }

    discrepancias = []
    for nivel, origen in fuentes.items():
        for clave, valor in origen.items():
            if clave in CONTENEDORES:
                continue
            columna = _columna(nivel, clave)
            en_fila = datos.get(columna)
            # Los numericos se mapean a float; `identificacion` y las fechas, a texto
            if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                coincide = en_fila is not None and float(en_fila) == float(valor)
            else:
                coincide = en_fila == valor
            if not coincide:
                discrepancias.append(f"{nivel}.{clave}: JSON={valor!r} fila={en_fila!r}")

    assert not discrepancias, "Valores que no llegaron intactos:\n" + "\n".join(discrepancias)
    assert datos["status"] == respuesta_servicio["status"]


def test_las_claves_conocidas_cubren_el_contrato_vigente(respuesta_servicio):
    """El catalogo del mapeador debe reflejar lo que el servicio envia hoy."""
    for nivel, claves in _claves_escalares(respuesta_servicio).items():
        contenedores_del_nivel = CLAVES_CONOCIDAS[nivel] & CONTENEDORES
        no_declaradas = claves - CLAVES_CONOCIDAS[nivel] - contenedores_del_nivel
        assert not no_declaradas, f"`{nivel}` recibe claves no declaradas: {no_declaradas}"


def test_avisa_cuando_el_servicio_agrega_campos(caplog):
    """Si el servicio crece, el log lo delata en vez de perder el dato."""
    cuerpo = {
        "results": [
            {
                "id": 1,
                "identificacion": "9",
                "nombres": "A",
                "apellidos": "B",
                "correo": "a@b.co",
                "evaluaciones": [
                    {
                        "id": 2,
                        "proyecto": "2026",
                        "nombre": "Q4",
                        "total_perspectivas": 1,
                        "total_objetivos": 1,
                        "evaluador_identificacion": "123",
                        "perspectivas": [
                            {
                                "id": 3,
                                "nombre": "P",
                                "objetivos": [
                                    {"id": 4, "objetivo": "O", "ponderacion_nueva": 5}
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        "meta": {"page": 1, "per_page": 50, "total_users": 1, "total_pages": 1,
                 "cursor": "abc"},
        "status": "ok",
    }

    with caplog.at_level(logging.WARNING):
        MapeadorRespuesta().a_resultado(cuerpo)

    avisos = "\n".join(r.getMessage() for r in caplog.records)
    assert "correo" in avisos
    assert "evaluador_identificacion" in avisos
    assert "ponderacion_nueva" in avisos
    assert "cursor" in avisos


def test_no_avisa_nada_con_el_contrato_vigente(respuesta_servicio, caplog):
    with caplog.at_level(logging.WARNING):
        MapeadorRespuesta().a_resultado(respuesta_servicio)

    assert [r.getMessage() for r in caplog.records] == []


def test_el_aviso_no_se_arrastra_entre_paginas(respuesta_servicio, caplog):
    """Cada llamada parte de cero: no debe repetir avisos de la pagina anterior."""
    mapeador = MapeadorRespuesta()
    mapeador.a_resultado({"results": [{"id": 1, "campo_raro": 1, "evaluaciones": []}]})
    caplog.clear()

    with caplog.at_level(logging.WARNING):
        mapeador.a_resultado(respuesta_servicio)

    assert "campo_raro" not in "\n".join(r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("nivel", sorted(CLAVES_CONOCIDAS))
def test_cada_nivel_declara_sus_claves(nivel):
    assert CLAVES_CONOCIDAS[nivel], f"`{nivel}` no declara ninguna clave"
