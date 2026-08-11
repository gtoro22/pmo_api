"""Pruebas del criterio de consulta y del catalogo de endpoints."""

from __future__ import annotations

import pytest

from tracking_goals.domain.exceptions import CriterioInvalido
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta
from tracking_goals.infrastructure.http.endpoints import Endpoints


def test_parametros_omiten_filtros_vacios():
    criterio = CriterioConsulta(project="2026", page=1, per_page=50)
    assert criterio.como_parametros() == {"page": "1", "per_page": "50", "project": "2026"}


def test_parametros_incluyen_todos_los_filtros():
    criterio = CriterioConsulta(
        project="2026", identity="5555553333", page=2, per_page=10, updated_since="2026-07-29T10:38:00-05:00"
    )
    assert criterio.como_parametros() == {
        "page": "2",
        "per_page": "10",
        "project": "2026",
        "identity": "5555553333",
        "updated_since": "2026-07-29T10:38:00-05:00",
    }


def test_siguiente_pagina_incrementa_page():
    assert CriterioConsulta(page=1).siguiente_pagina().page == 2


@pytest.mark.parametrize("page,per_page", [(0, 50), (-1, 50), (1, 0), (1, 501)])
def test_criterios_invalidos(page, per_page):
    with pytest.raises(CriterioInvalido):
        CriterioConsulta(page=page, per_page=per_page)


def test_endpoint_se_construye_desde_el_base_url():
    assert (
        Endpoints("https://amagi.elearning.co").tracking_goals
        == "https://amagi.elearning.co/api/v1/tracking_goals"
    )


def test_endpoint_tolera_barra_final_en_el_base_url():
    assert (
        Endpoints("https://amagi.elearning.co/").tracking_goals
        == "https://amagi.elearning.co/api/v1/tracking_goals"
    )
