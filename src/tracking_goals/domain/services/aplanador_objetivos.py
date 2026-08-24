"""Servicio de dominio: aplanado de la jerarquia de resultados.

Convierte la estructura jerarquica usuario -> evaluacion -> perspectiva ->
objetivo en una lista de filas planas. Los niveles vacios (usuario sin
evaluaciones, evaluacion sin perspectivas, perspectiva sin objetivos) se
conservan como una fila con los campos inferiores en blanco para no perder
informacion de auditoria.
"""

from __future__ import annotations

from dataclasses import replace

from tracking_goals.domain.model.evaluacion import Evaluacion
from tracking_goals.domain.model.metadatos import Metadatos
from tracking_goals.domain.model.registro_plano import RegistroPlano
from tracking_goals.domain.model.resultado_consulta import ResultadoConsulta
from tracking_goals.domain.model.usuario import Usuario


class AplanadorObjetivos:
    """Traduce un `ResultadoConsulta` a filas planas listas para exportar."""

    def aplanar(self, resultado: ResultadoConsulta) -> list[RegistroPlano]:
        base = self._fila_de_metadatos(resultado.metadatos, resultado.status)
        filas: list[RegistroPlano] = []
        for usuario in resultado.usuarios:
            filas.extend(self._aplanar_usuario(usuario, base))
        return filas

    # -- Niveles ---------------------------------------------------------------

    def _aplanar_usuario(self, usuario: Usuario, base: RegistroPlano) -> list[RegistroPlano]:
        fila_usuario = replace(
            base,
            usuario_id=usuario.id,
            identificacion=usuario.identificacion,
            nombres=usuario.nombres,
            apellidos=usuario.apellidos,
            nombre_completo=usuario.nombre_completo,
            cargo=usuario.cargo,
            nivel_cargo=usuario.nivel_cargo,
            area=usuario.area,
            grupo=usuario.grupo,
            localizacion=usuario.localizacion,
            unidad_negocio=usuario.unidad_negocio,
        )
        if not usuario.evaluaciones:
            return [fila_usuario]

        filas: list[RegistroPlano] = []
        for evaluacion in usuario.evaluaciones:
            filas.extend(self._aplanar_evaluacion(evaluacion, fila_usuario))
        return filas

    def _aplanar_evaluacion(
        self, evaluacion: Evaluacion, base: RegistroPlano
    ) -> list[RegistroPlano]:
        fila_evaluacion = replace(
            base,
            evaluacion_id=evaluacion.id,
            proyecto=evaluacion.proyecto,
            evaluacion_nombre=evaluacion.nombre,
            evaluacion_inicio=evaluacion.inicio,
            evaluacion_fin=evaluacion.fin,
            evaluador=evaluacion.evaluador,
            estado_evaluacion=evaluacion.estado_evaluacion,
            total_perspectivas=evaluacion.total_perspectivas,
            total_objetivos=evaluacion.total_objetivos,
        )
        if not evaluacion.perspectivas:
            return [fila_evaluacion]

        filas: list[RegistroPlano] = []
        for perspectiva in evaluacion.perspectivas:
            fila_perspectiva = replace(
                fila_evaluacion,
                perspectiva_id=perspectiva.id,
                perspectiva_nombre=perspectiva.nombre,
                perspectiva_peso=perspectiva.peso,
                perspectiva_cumplimiento=perspectiva.cumplimiento,
            )
            if not perspectiva.objetivos:
                filas.append(fila_perspectiva)
                continue
            for objetivo in perspectiva.objetivos:
                filas.append(
                    replace(
                        fila_perspectiva,
                        objetivo_id=objetivo.id,
                        objetivo=objetivo.objetivo,
                        objetivo_estrategico=objetivo.objetivo_estrategico,
                        indicador_medicion=objetivo.indicador_medicion,
                        indicador=objetivo.indicador,
                        objetivo_peso=objetivo.peso,
                        meta=objetivo.meta,
                        minimo=objetivo.minimo,
                        sobresaliente=objetivo.sobresaliente,
                        unidad_medida=objetivo.unidad_medida,
                        tipo_calculo=objetivo.tipo_calculo,
                        tipo_indicador=objetivo.tipo_indicador,
                        periodo=objetivo.periodo,
                        resultado=objetivo.resultado,
                        cumplimiento=objetivo.cumplimiento,
                        fecha_limite=objetivo.fecha_limite,
                        estado_seguimientos=objetivo.estado_seguimientos,
                    )
                )
        return filas

    # -- Metadatos -------------------------------------------------------------

    @staticmethod
    def _fila_de_metadatos(metadatos: Metadatos | None, status: str) -> RegistroPlano:
        if metadatos is None:
            return RegistroPlano(status=status)
        return RegistroPlano(
            meta_page=metadatos.page,
            meta_per_page=metadatos.per_page,
            meta_total_users=metadatos.total_users,
            meta_total_pages=metadatos.total_pages,
            meta_updated_since=metadatos.updated_since,
            meta_server_time=metadatos.server_time,
            meta_next_updated_since=metadatos.next_updated_since,
            status=status,
        )
