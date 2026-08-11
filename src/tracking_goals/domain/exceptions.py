"""Errores del dominio y del contrato de sus puertos."""

from __future__ import annotations


class ErrorDeDominio(Exception):
    """Error base de la aplicacion."""


class CriterioInvalido(ErrorDeDominio):
    """Los parametros de consulta no cumplen las reglas del dominio."""


class ErrorDeConsulta(ErrorDeDominio):
    """Fallo generico al consultar el servicio (contrato del repositorio)."""


class ErrorDeConexion(ErrorDeConsulta):
    """No fue posible comunicarse con el servicio (red, DNS, timeout, TLS)."""


class ErrorDeAutenticacion(ErrorDeConsulta):
    """El token es invalido, expiro o no tiene permisos (401 / 403)."""


class RespuestaInvalida(ErrorDeConsulta):
    """La respuesta no es JSON valido o no cumple la estructura esperada."""


class ErrorDeExportacion(ErrorDeDominio):
    """Fallo al generar el archivo de salida."""
