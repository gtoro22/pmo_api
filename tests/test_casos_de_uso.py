"""Pruebas de los casos de uso con un repositorio en memoria."""

from __future__ import annotations

from pathlib import Path

import pytest

from tracking_goals.application.dto.solicitud_exportacion import SolicitudExportacion
from tracking_goals.application.use_cases.consultar_objetivos import ConsultarObjetivos
from tracking_goals.application.use_cases.exportar_objetivos_excel import (
    ExportarObjetivosExcel,
)
from tracking_goals.domain.exceptions import ErrorDeConsulta
from tracking_goals.domain.model.metadatos import Metadatos
from tracking_goals.domain.model.resultado_consulta import ResultadoConsulta
from tracking_goals.domain.model.usuario import Usuario
from tracking_goals.domain.repositories.repositorio_objetivos import RepositorioObjetivos
from tracking_goals.domain.services.aplanador_objetivos import AplanadorObjetivos
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta
from tracking_goals.infrastructure.exportacion.exportador_excel import ExportadorExcel
from tracking_goals.infrastructure.transferencia.transportador_nulo import TransportadorNulo


class RepositorioEnMemoria(RepositorioObjetivos):
    def __init__(self, paginas: dict[int, ResultadoConsulta]) -> None:
        self._paginas = paginas
        self.criterios: list[CriterioConsulta] = []

    def consultar(self, criterio: CriterioConsulta) -> ResultadoConsulta:
        self.criterios.append(criterio)
        if criterio.page not in self._paginas:
            raise ErrorDeConsulta(f"Pagina inexistente: {criterio.page}")
        return self._paginas[criterio.page]


def _pagina(numero: int, total_paginas: int, usuarios: int) -> ResultadoConsulta:
    return ResultadoConsulta(
        usuarios=tuple(
            Usuario(id=numero * 100 + i, identificacion=str(i), nombres="N", apellidos="A")
            for i in range(usuarios)
        ),
        metadatos=Metadatos(
            page=numero,
            per_page=usuarios,
            total_users=total_paginas * usuarios,
            total_pages=total_paginas,
            updated_since=None,
            server_time="2026-07-29T10:38:00-05:00",
            next_updated_since="2026-07-29T10:40:00-05:00",
        ),
    )


def test_consulta_una_sola_pagina_por_defecto():
    repositorio = RepositorioEnMemoria({1: _pagina(1, 3, 2), 2: _pagina(2, 3, 2)})
    resultado, paginas = ConsultarObjetivos(repositorio).ejecutar(CriterioConsulta())

    assert paginas == 1
    assert resultado.total_usuarios_recibidos == 2


def test_recorre_todas_las_paginas():
    repositorio = RepositorioEnMemoria(
        {1: _pagina(1, 3, 2), 2: _pagina(2, 3, 2), 3: _pagina(3, 3, 2)}
    )
    resultado, paginas = ConsultarObjetivos(repositorio).ejecutar(
        CriterioConsulta(), todas_las_paginas=True
    )

    assert paginas == 3
    assert resultado.total_usuarios_recibidos == 6
    assert [c.page for c in repositorio.criterios] == [1, 2, 3]
    assert resultado.metadatos.page == 3


def test_exportacion_completa_genera_resumen(tmp_path: Path):
    repositorio = RepositorioEnMemoria({1: _pagina(1, 1, 2)})
    caso_de_uso = ExportarObjetivosExcel(
        consultar_objetivos=ConsultarObjetivos(repositorio),
        aplanador=AplanadorObjetivos(),
        exportador=ExportadorExcel(),
        transportador=TransportadorNulo(),
    )

    destino = tmp_path / "reporte.xlsx"
    resumen = caso_de_uso.ejecutar(SolicitudExportacion(CriterioConsulta(), destino))

    assert resumen.archivo == destino
    assert destino.exists()
    assert resumen.usuarios == 2
    assert resumen.filas == 2
    assert resumen.paginas_consultadas == 1
    assert resumen.next_updated_since == "2026-07-29T10:40:00-05:00"
    assert resumen.status == "ok"
    assert resumen.envio.enviado is False


def test_error_del_repositorio_se_propaga():
    repositorio = RepositorioEnMemoria({})
    with pytest.raises(ErrorDeConsulta):
        ConsultarObjetivos(repositorio).ejecutar(CriterioConsulta())
