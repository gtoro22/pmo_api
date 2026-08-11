"""Pruebas del servicio de dominio que aplana la jerarquia."""

from __future__ import annotations

from tracking_goals.domain.model.evaluacion import Evaluacion
from tracking_goals.domain.model.registro_plano import RegistroPlano
from tracking_goals.domain.model.resultado_consulta import ResultadoConsulta
from tracking_goals.domain.model.usuario import Usuario
from tracking_goals.domain.services.aplanador_objetivos import AplanadorObjetivos
from tracking_goals.infrastructure.http.mapeadores import MapeadorRespuesta


def test_aplana_todos_los_campos_del_json(respuesta_documentacion):
    resultado = MapeadorRespuesta().a_resultado(respuesta_documentacion)
    filas = AplanadorObjetivos().aplanar(resultado)

    assert len(filas) == 1
    fila = filas[0]

    assert fila.usuario_id == 13
    assert fila.identificacion == "5555553333"
    assert fila.nombres == "Usuario"
    assert fila.apellidos == "Prueba"
    assert fila.evaluacion_id == 127
    assert fila.proyecto == "2026"
    assert fila.evaluacion_nombre == "Q4 2026 CO"
    assert fila.total_perspectivas == 1
    assert fila.total_objetivos == 4
    assert fila.perspectiva_id == 7
    assert fila.perspectiva_nombre == "Procesos Internos"
    assert fila.objetivo_id == 15
    assert fila.meta == 100.0
    assert fila.unidad_medida == "Porcentaje"
    assert fila.tipo_calculo == "Ultimo dato"
    assert fila.tipo_indicador == "Creciente"
    assert fila.indicador == "VENEZUELA"
    assert fila.resultado is None
    assert fila.cumplimiento is None

    # Metadatos replicados en cada fila
    assert fila.meta_page == 1
    assert fila.meta_per_page == 50
    assert fila.meta_total_users == 1
    assert fila.meta_total_pages == 1
    assert fila.meta_updated_since is None
    assert fila.meta_server_time == "2026-07-29T10:38:00-05:00"
    assert fila.meta_next_updated_since == "2026-07-29T10:38:00-05:00"
    assert fila.status == "ok"


def test_columnas_cubren_todo_el_contrato():
    columnas = RegistroPlano.columnas()
    esperadas = {
        "usuario_id",
        "identificacion",
        "nombres",
        "apellidos",
        "evaluacion_id",
        "proyecto",
        "evaluacion_nombre",
        "total_perspectivas",
        "total_objetivos",
        "perspectiva_id",
        "perspectiva_nombre",
        "objetivo_id",
        "objetivo",
        "meta",
        "unidad_medida",
        "tipo_calculo",
        "tipo_indicador",
        "indicador",
        "resultado",
        "cumplimiento",
        "meta_page",
        "meta_per_page",
        "meta_total_users",
        "meta_total_pages",
        "meta_updated_since",
        "meta_server_time",
        "meta_next_updated_since",
        "status",
    }
    assert esperadas.issubset(set(columnas))


def test_usuario_sin_evaluaciones_genera_una_fila():
    resultado = ResultadoConsulta(
        usuarios=(Usuario(id=1, identificacion="9", nombres="Sin", apellidos="Datos"),)
    )
    filas = AplanadorObjetivos().aplanar(resultado)
    assert len(filas) == 1
    assert filas[0].usuario_id == 1
    assert filas[0].evaluacion_id is None


def test_evaluacion_sin_perspectivas_genera_una_fila():
    evaluacion = Evaluacion(
        id=5, proyecto="2026", nombre="Eval", total_perspectivas=0, total_objetivos=0
    )
    resultado = ResultadoConsulta(
        usuarios=(Usuario(id=1, identificacion="9", nombres="A", apellidos="B",
                          evaluaciones=(evaluacion,)),)
    )
    filas = AplanadorObjetivos().aplanar(resultado)
    assert len(filas) == 1
    assert filas[0].evaluacion_id == 5
    assert filas[0].perspectiva_id is None
