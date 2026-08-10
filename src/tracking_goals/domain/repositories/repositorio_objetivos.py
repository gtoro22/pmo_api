"""Puerto de salida: repositorio de objetivos.

El dominio declara QUE necesita; la infraestructura decide COMO obtenerlo
(cliente HTTP, cache, fixture de pruebas, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from tracking_goals.domain.model.resultado_consulta import ResultadoConsulta
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta


class RepositorioObjetivos(ABC):
    """Contrato de consulta de evaluaciones, perspectivas y objetivos."""

    @abstractmethod
    def consultar(self, criterio: CriterioConsulta) -> ResultadoConsulta:
        """Devuelve una pagina de resultados para el criterio indicado.

        Raises:
            ErrorDeConexion: fallo de red, DNS, TLS o timeout.
            ErrorDeAutenticacion: token invalido o sin permisos.
            RespuestaInvalida: respuesta no interpretable segun el contrato.
            ErrorDeConsulta: cualquier otro fallo del servicio.
        """
        raise NotImplementedError
