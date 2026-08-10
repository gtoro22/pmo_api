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
                        meta=objetivo.meta,
                        unidad_medida=objetivo.unidad_medida,
                        tipo_calculo=objetivo.tipo_calculo,
                        tipo_indicador=objetivo.tipo_indicador,
                        indicador=objetivo.indicador,
                        resultado=objetivo.resultado,
                        cumplimiento=objetivo.cumplimiento,
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
