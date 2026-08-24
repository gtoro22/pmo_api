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


def test_aplana_los_campos_nuevos_del_servicio(respuesta_servicio):
    """Los campos que el servicio entrega y no estan documentados deben llegar al Excel."""
    resultado = MapeadorRespuesta().a_resultado(respuesta_servicio)
    filas = AplanadorObjetivos().aplanar(resultado)

    assert len(filas) == 1
    fila = filas[0]

    # Usuario evaluado: datos organizacionales
    assert fila.cargo == "Especialista de Administracion de Contratos"
    assert fila.nivel_cargo == "Operativo"
    assert fila.area == "Gestion Corporativa y Control de Gestion"
    assert fila.grupo == "Soporte"
    assert fila.localizacion == "Venezuela"
    assert fila.unidad_negocio == "Amagi Group"

    # Evaluacion: vigencia, evaluador y estado
    assert fila.evaluacion_inicio == "2026-04-01"
    assert fila.evaluacion_fin == "2026-08-31"
    assert fila.evaluador == "Apellido1 Apellido2 Nombre1 Nombre2"
    assert fila.estado_evaluacion == "Evaluacion Finalizada"

    # Perspectiva: peso y cumplimiento propios
    assert fila.perspectiva_peso == 100.0
    assert fila.perspectiva_cumplimiento == 78.38

    # Objetivo
    assert fila.objetivo_estrategico == "VENEZUELA"
    assert fila.indicador_medicion == "• Mantenimiento del Dashboard Comercial"
    assert fila.objetivo_peso == 35.0
    assert fila.minimo is None
    assert fila.sobresaliente is None
    assert fila.periodo == "Q4 2026"
    assert fila.resultado == 90.0
    assert fila.cumplimiento == 90.0
    assert fila.fecha_limite == "2026-08-31"
    assert fila.estado_seguimientos == "Seguimiento Aprobado"

    # `indicador` esta documentado pero el servicio ya no lo envia
    assert fila.indicador is None


def test_pesos_y_cumplimientos_no_se_pisan_entre_niveles(respuesta_servicio):
    """`peso` y `cumplimiento` existen en perspectiva y objetivo: deben ir separados."""
    resultado = MapeadorRespuesta().a_resultado(respuesta_servicio)
    fila = AplanadorObjetivos().aplanar(resultado)[0]

    assert fila.perspectiva_peso == 100.0
    assert fila.objetivo_peso == 35.0
    assert fila.perspectiva_cumplimiento == 78.38
    assert fila.cumplimiento == 90.0


def test_columnas_cubren_los_campos_solicitados_en_el_reporte():
    """Los campos del reporte de seguimiento que el servicio si entrega."""
    columnas = set(RegistroPlano.columnas())
    assert {
        "identificacion",       # Cedula Evaluado
        "nombres",              # Nombre Evaluado
        "apellidos",            # Nombre Evaluado
        "area",                 # Area Evaluado
        "cargo",                # Cargo Evaluado
        "evaluador",            # Nombre Evaluador
        "estado_evaluacion",    # Estado de la evaluacion
    }.issubset(columnas)


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
