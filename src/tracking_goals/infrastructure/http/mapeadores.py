"""Traduccion del JSON del servicio al modelo de dominio (anticorruption layer)."""

from __future__ import annotations

from typing import Any

from tracking_goals.domain.exceptions import RespuestaInvalida
from tracking_goals.domain.model.evaluacion import Evaluacion
from tracking_goals.domain.model.metadatos import Metadatos
from tracking_goals.domain.model.objetivo import Objetivo
from tracking_goals.domain.model.perspectiva import Perspectiva
from tracking_goals.domain.model.resultado_consulta import ESTADO_OK, ResultadoConsulta
from tracking_goals.domain.model.usuario import Usuario


class MapeadorRespuesta:
    """Convierte el cuerpo JSON de `tracking_goals` en objetos de dominio."""

    def a_resultado(self, cuerpo: dict[str, Any]) -> ResultadoConsulta:
        resultados = cuerpo.get("results", [])
        if not isinstance(resultados, list):
            raise RespuestaInvalida("`results` debe ser un arreglo de usuarios.")

        usuarios = tuple(self._a_usuario(item) for item in resultados)
        metadatos = self._a_metadatos(cuerpo.get("meta"), len(usuarios))
        status = _texto(cuerpo.get("status")) or ESTADO_OK
        return ResultadoConsulta(usuarios=usuarios, metadatos=metadatos, status=status)

    # -- Niveles ---------------------------------------------------------------

    def _a_usuario(self, datos: Any) -> Usuario:
        datos = _objeto(datos, "usuario")
        evaluaciones = _lista(datos.get("evaluaciones"), "evaluaciones")
        return Usuario(
            id=_entero(datos.get("id")),
            identificacion=_texto(datos.get("identificacion")),
            nombres=_texto(datos.get("nombres")),
            apellidos=_texto(datos.get("apellidos")),
            evaluaciones=tuple(self._a_evaluacion(item) for item in evaluaciones),
        )

    def _a_evaluacion(self, datos: Any) -> Evaluacion:
        datos = _objeto(datos, "evaluacion")
        perspectivas = _lista(datos.get("perspectivas"), "perspectivas")
        return Evaluacion(
            id=_entero(datos.get("id")),
            proyecto=_texto(datos.get("proyecto")),
            nombre=_texto(datos.get("nombre")),
            total_perspectivas=_entero_opcional(datos.get("total_perspectivas")),
            total_objetivos=_entero_opcional(datos.get("total_objetivos")),
            perspectivas=tuple(self._a_perspectiva(item) for item in perspectivas),
        )

    def _a_perspectiva(self, datos: Any) -> Perspectiva:
        datos = _objeto(datos, "perspectiva")
        objetivos = _lista(datos.get("objetivos"), "objetivos")
        return Perspectiva(
            id=_entero(datos.get("id")),
            nombre=_texto(datos.get("nombre")) or "",
            objetivos=tuple(self._a_objetivo(item) for item in objetivos),
        )

    def _a_objetivo(self, datos: Any) -> Objetivo:
        datos = _objeto(datos, "objetivo")
        return Objetivo(
            id=_entero(datos.get("id")),
            objetivo=_texto(datos.get("objetivo")) or "",
            meta=_decimal_opcional(datos.get("meta")),
            unidad_medida=_texto(datos.get("unidad_medida")),
            tipo_calculo=_texto(datos.get("tipo_calculo")),
            tipo_indicador=_texto(datos.get("tipo_indicador")),
            indicador=_texto(datos.get("indicador")),
            resultado=_decimal_opcional(datos.get("resultado")),
            cumplimiento=_decimal_opcional(datos.get("cumplimiento")),
        )

    @staticmethod
    def _a_metadatos(datos: Any, usuarios_recibidos: int) -> Metadatos | None:
        if datos is None:
            return None
        datos = _objeto(datos, "meta")
        return Metadatos(
            page=_entero_opcional(datos.get("page")) or 1,
            per_page=_entero_opcional(datos.get("per_page")) or usuarios_recibidos,
            total_users=_entero_opcional(datos.get("total_users")) or usuarios_recibidos,
            total_pages=_entero_opcional(datos.get("total_pages")) or 1,
            updated_since=_texto(datos.get("updated_since")),
            server_time=_texto(datos.get("server_time")),
            next_updated_since=_texto(datos.get("next_updated_since")),
        )


# -- Conversiones defensivas ---------------------------------------------------


def _objeto(valor: Any, contexto: str) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise RespuestaInvalida(
            f"Se esperaba un objeto JSON para `{contexto}` y se recibio {type(valor).__name__}."
        )
    return valor


def _lista(valor: Any, contexto: str) -> list[Any]:
    if valor is None:
        return []
    if not isinstance(valor, list):
        raise RespuestaInvalida(
            f"Se esperaba un arreglo para `{contexto}` y se recibio {type(valor).__name__}."
        )
    return valor


def _texto(valor: Any) -> str | None:
    """Preserva los valores como texto (ej. `identificacion` con ceros iniciales)."""
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor
    return str(valor)


def _entero(valor: Any) -> int:
    convertido = _entero_opcional(valor)
    if convertido is None:
        raise RespuestaInvalida(f"Se esperaba un identificador entero y se recibio {valor!r}.")
    return convertido


def _entero_opcional(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError) as error:
        raise RespuestaInvalida(f"Se esperaba un entero y se recibio {valor!r}.") from error


def _decimal_opcional(valor: Any) -> float | None:
    """`Number | null`: conserva `None` cuando el servicio aun no tiene el dato."""
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except (TypeError, ValueError) as error:
        raise RespuestaInvalida(f"Se esperaba un numero y se recibio {valor!r}.") from error
