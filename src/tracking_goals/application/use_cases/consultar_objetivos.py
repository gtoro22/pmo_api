"""Caso de uso: consultar objetivos (con paginacion opcional)."""

from __future__ import annotations

import logging

from tracking_goals.domain.model.resultado_consulta import ResultadoConsulta
from tracking_goals.domain.repositories.repositorio_objetivos import RepositorioObjetivos
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta

logger = logging.getLogger(__name__)

LIMITE_PAGINAS = 1000


class ConsultarObjetivos:
    """Orquesta una o varias llamadas al repositorio segun la paginacion."""

    def __init__(self, repositorio: RepositorioObjetivos) -> None:
        self._repositorio = repositorio

    def ejecutar(
        self, criterio: CriterioConsulta, todas_las_paginas: bool = False
    ) -> tuple[ResultadoConsulta, int]:
        """Devuelve el resultado acumulado y el numero de paginas consultadas."""
        logger.info("Consultando servicio con criterio: %s", criterio.describir())
        acumulado = self._repositorio.consultar(criterio)
        paginas = 1
        self._registrar_pagina(acumulado, paginas)

        if not todas_las_paginas:
            return acumulado, paginas

        actual = acumulado
        while actual.hay_pagina_siguiente and paginas < LIMITE_PAGINAS:
            criterio = criterio.siguiente_pagina()
            logger.info("Consultando pagina siguiente: %s", criterio.describir())
            actual = self._repositorio.consultar(criterio)
            acumulado = acumulado.unir(actual)
            paginas += 1
            self._registrar_pagina(actual, paginas)

        if paginas >= LIMITE_PAGINAS and actual.hay_pagina_siguiente:
            logger.warning(
                "Se alcanzo el limite de %s paginas; la consulta puede estar incompleta.",
                LIMITE_PAGINAS,
            )
        return acumulado, paginas

    @staticmethod
    def _registrar_pagina(resultado: ResultadoConsulta, numero: int) -> None:
        metadatos = resultado.metadatos
        if metadatos is None:
            logger.info(
                "Pagina %s procesada: %s usuarios (respuesta sin seccion meta).",
                numero,
                resultado.total_usuarios_recibidos,
            )
            return
        logger.info(
            "Pagina %s/%s procesada: %s usuarios (total_users=%s, status=%s).",
            metadatos.page,
            metadatos.total_pages,
            resultado.total_usuarios_recibidos,
            metadatos.total_users,
            resultado.status,
        )
