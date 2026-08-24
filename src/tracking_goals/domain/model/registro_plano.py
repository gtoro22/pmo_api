"""Objeto de valor: registro plano (una fila del Excel).

Aplana la jerarquia usuario -> evaluacion -> perspectiva -> objetivo e incluye
ademas los metadatos de la respuesta, de modo que el archivo de salida contenga
TODOS los parametros del JSON de salida en formato plano.

Los campos `peso` y `cumplimiento` existen en dos niveles distintos, por eso los
de perspectiva se prefijan (`perspectiva_peso`, `perspectiva_cumplimiento`) y el
peso del objetivo se nombra `objetivo_peso`. Los campos propios del objetivo
(`meta`, `resultado`, `cumplimiento`) van sin prefijo porque el objetivo es el
grano de la fila.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any


@dataclass(frozen=True)
class RegistroPlano:
    """Una fila plana del reporte. El orden de los campos es el de las columnas."""

    # --- Usuario evaluado ----------------------------------------------------
    usuario_id: int | None = None
    identificacion: str | None = None
    nombres: str | None = None
    apellidos: str | None = None
    nombre_completo: str | None = None
    cargo: str | None = None
    nivel_cargo: str | None = None
    area: str | None = None
    grupo: str | None = None
    localizacion: str | None = None
    unidad_negocio: str | None = None

    # --- Evaluacion ----------------------------------------------------------
    evaluacion_id: int | None = None
    proyecto: str | None = None
    evaluacion_nombre: str | None = None
    evaluacion_inicio: str | None = None
    evaluacion_fin: str | None = None
    evaluador: str | None = None
    estado_evaluacion: str | None = None
    total_perspectivas: int | None = None
    total_objetivos: int | None = None

    # --- Perspectiva ---------------------------------------------------------
    perspectiva_id: int | None = None
    perspectiva_nombre: str | None = None
    perspectiva_peso: float | None = None
    perspectiva_cumplimiento: float | None = None

    # --- Objetivo ------------------------------------------------------------
    objetivo_id: int | None = None
    objetivo: str | None = None
    objetivo_estrategico: str | None = None
    indicador_medicion: str | None = None
    indicador: str | None = None
    objetivo_peso: float | None = None
    meta: float | None = None
    minimo: float | None = None
    sobresaliente: float | None = None
    unidad_medida: str | None = None
    tipo_calculo: str | None = None
    tipo_indicador: str | None = None
    periodo: str | None = None
    resultado: float | None = None
    cumplimiento: float | None = None
    fecha_limite: str | None = None
    estado_seguimientos: str | None = None

    # --- Metadatos de la respuesta ------------------------------------------
    meta_page: int | None = None
    meta_per_page: int | None = None
    meta_total_users: int | None = None
    meta_total_pages: int | None = None
    meta_updated_since: str | None = None
    meta_server_time: str | None = None
    meta_next_updated_since: str | None = None
    status: str | None = None

    @classmethod
    def columnas(cls) -> tuple[str, ...]:
        """Nombres de columna en el orden declarado."""
        return tuple(campo.name for campo in fields(cls))

    def valores(self) -> tuple[Any, ...]:
        """Valores de la fila en el mismo orden que `columnas()`."""
        datos = asdict(self)
        return tuple(datos[nombre] for nombre in self.columnas())

    def como_diccionario(self) -> dict[str, Any]:
        return asdict(self)
